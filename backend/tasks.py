# background tasks

import csv
import os
from datetime import datetime, timedelta

from flask_mail import Message

from extension import celery, mail, db


# daily reminder

@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    # send reminders for drives closing in 7 days
    from models.auth import User
    from models.drive import Drive
    from models.applications import Application

    today = datetime.utcnow().date()
    week_later = today + timedelta(days=7)

    upcoming = Drive.query.filter(
        Drive.is_approved == True,
        Drive.application_deadline != None,
        Drive.application_deadline >= today,
        Drive.application_deadline <= week_later,
    ).all()

    if not upcoming:
        return "No upcoming deadlines – no reminders sent"

    students = User.query.filter_by(role="student", is_blocked=False).all()
    sent = 0

    for student in students:
        if not student.email:
            continue

        not_applied = [
            d for d in upcoming
            if not Application.query.filter_by(student_id=student.id, drive_id=d.id).first()
        ]
        if not not_applied:
            continue

        lines = "\n".join(
            f"  • {d.title}  –  deadline {d.application_deadline.strftime('%d/%m/%Y')}"
            for d in not_applied
        )
        body = (
            f"Hi {student.name},\n\n"
            f"The following placement drives have upcoming deadlines and you haven't applied yet:\n\n"
            f"{lines}\n\n"
            f"Login to the Placement Portal to apply before the deadline.\n\n"
            f"Regards,\nPlacement Cell"
        )
        try:
            mail.send(Message(
                subject="Placement Drive Deadline Reminder",
                recipients=[student.email],
                body=body,
            ))
            sent += 1
        except Exception:
            pass

    return f"Reminders sent to {sent} student(s)"


# monthly report

@celery.task(name="tasks.send_monthly_report")
def send_monthly_report():
    # make report and send it to admin
    from models.auth import User
    from models.drive import Drive
    from models.applications import Application

    now = datetime.utcnow()
    # get last month data
    if now.month == 1:
        m, y = 12, now.year - 1
    else:
        m, y = now.month - 1, now.year

    month_start = datetime(y, m, 1)
    month_end = datetime(y, m + 1, 1) if m < 12 else datetime(y + 1, 1, 1)
    month_label = month_start.strftime("%B %Y")

    drives = Drive.query.filter(
        Drive.drive_date >= month_start.date(),
        Drive.drive_date < month_end.date(),
    ).all()

    apps = Application.query.filter(
        Application.created_at >= month_start,
        Application.created_at < month_end,
    ).all()

    selected = [a for a in apps if a.status in ("shortlisted", "approved")]

    drive_rows = "".join(
        f"<tr><td>{d.title}</td>"
        f"<td>{d.drive_date.strftime('%d/%m/%Y') if d.drive_date else 'N/A'}</td>"
        f"<td>{Application.query.filter_by(drive_id=d.id).count()}</td></tr>"
        for d in drives
    )

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Monthly Placement Report</title></head>
<body style="font-family:Arial,sans-serif;padding:24px;color:#1f2937;">
  <h1 style="color:#111827;">Monthly Placement Activity Report</h1>
  <h2 style="color:#374151;">{month_label}</h2>
  <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse;margin-bottom:24px;">
    <tr style="background:#f3f4f6;"><th>Metric</th><th>Count</th></tr>
    <tr><td>Drives Conducted</td><td>{len(drives)}</td></tr>
    <tr><td>Total Applications Received</td><td>{len(apps)}</td></tr>
    <tr><td>Students Shortlisted / Selected</td><td>{len(selected)}</td></tr>
  </table>
  <h3>Drive-wise Breakdown</h3>
  <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse;">
    <tr style="background:#f3f4f6;"><th>Drive Title</th><th>Drive Date</th><th>Applications</th></tr>
    {drive_rows if drive_rows else '<tr><td colspan="3">No drives this month</td></tr>'}
  </table>
  <p style="margin-top:24px;color:#6b7280;font-size:0.9rem;">
    Generated on {now.strftime('%d/%m/%Y %H:%M UTC')}
  </p>
</body>
</html>
"""

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        return "No admin user found"

    try:
        mail.send(Message(
            subject=f"Monthly Placement Report – {month_label}",
            recipients=[admin.email],
            html=html,
        ))
        return f"Monthly report sent to {admin.email}"
    except Exception as e:
        return f"Failed to send report: {e}"


# csv export

@celery.task(name="tasks.export_student_csv", bind=True)
def export_student_csv(self, student_id):
    # make student application csv
    from flask import current_app
    from models.auth import User
    from models.drive import Drive
    from models.applications import Application
    from models.company import Company

    self.update_state(state="PROGRESS", meta={"status": "Generating CSV…"})

    student = User.query.get(student_id)
    if not student:
        return {"status": "FAILED", "message": "Student not found"}

    applications = Application.query.filter_by(student_id=student_id).order_by(
        Application.created_at.desc()
    ).all()

    rows = []
    for app in applications:
        drive = Drive.query.get(app.drive_id)
        company_user = User.query.get(drive.company_id) if drive else None
        company = Company.query.filter_by(user_id=company_user.id).first() if company_user else None

        rows.append({
            "Student ID": student.id,
            "Student Name": student.name,
            "Student Email": student.email,
            "Company Name": (
                company.company_name if company
                else (company_user.name if company_user else "Unknown")
            ),
            "Drive Title": drive.title if drive else "Unknown",
            "Application Status": app.status or "pending",
            "Applied On": app.created_at.strftime("%d/%m/%Y %H:%M") if app.created_at else "",
            "Drive Date": drive.drive_date.strftime("%d/%m/%Y") if drive and drive.drive_date else "",
            "Application Deadline": (
                drive.application_deadline.strftime("%d/%m/%Y")
                if drive and drive.application_deadline else ""
            ),
        })

    filename = f"applications_{student_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    exports_folder = current_app.config["EXPORTS_FOLDER"]
    filepath = os.path.join(exports_folder, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        else:
            f.write("No applications found\n")

    # also send csv on email
    try:
        if student.email:
            with open(filepath, "rb") as f:
                mail.send(Message(
                    subject="Your Application History – CSV Export",
                    recipients=[student.email],
                    body=(
                        f"Hi {student.name},\n\n"
                        f"Your placement application history export is ready.\n"
                        f"Total applications: {len(rows)}\n\n"
                        f"You can also download it directly from your dashboard.\n\n"
                        f"Regards,\nPlacement Cell"
                    ),
                    attachments=[(filename, "text/csv", f.read())],
                ))
    except Exception:
        pass  # csv is still saved if mail fails

    return {
        "status": "SUCCESS",
        "filename": filename,
        "download_url": f"/exports/{filename}",
        "total_applications": len(rows),
    }

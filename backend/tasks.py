# background tasks

import csv
import os
from datetime import datetime, timedelta

from extension import celery, db
from mail_utils import send_placement_mail
from report_utils import build_monthly_report_data, render_monthly_report_html

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
            f"  - {d.title} - last date {d.application_deadline.strftime('%d/%m/%Y')}"
            for d in not_applied
        )
        body = (
            f"Hi {student.name},\n\n"
            f"The following placement drives have upcoming last dates and you haven't applied yet:\n\n"
            f"{lines}\n\n"
            f"Login to the Placement Portal to apply before the last date.\n\n"
            f"Regards,\nPlacement Cell"
        )
        if send_placement_mail(
            subject="Placement Drive Deadline Reminder",
            recipients=[student.email],
            recipient_group="student",
            body=body,
        ):
            sent += 1

    return f"Reminders sent to {sent} student(s)"


# monthly report

@celery.task(name="tasks.send_monthly_report")
def send_monthly_report():
    # make report and send it to admin
    from models.auth import User
    data = build_monthly_report_data(period="previous")
    html = render_monthly_report_html(data)
    filename = f"monthly_report_{data['month_label'].replace(' ', '_').lower()}.html"

    admin = User.query.filter_by(role="admin").first()
    if not admin:
        return "No admin user found"

    if send_placement_mail(
        subject=f"Monthly Placement Report - {data['month_label']}",
        recipients=[admin.email],
        recipient_group="staff",
        html=html,
        attachments=[(filename, "text/html", html.encode("utf-8"))],
    ):
        return f"Monthly report sent to {admin.email}"
    return f"Failed to send report to {admin.email}"


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

    fieldnames = [
        "Student ID",
        "Student Name",
        "Student Email",
        "Company Name",
        "Drive Title",
        "Application Status",
        "Applied On",
        "Starting Date",
        "Last Date",
    ]
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
            "Starting Date": drive.drive_date.strftime("%d/%m/%Y") if drive and drive.drive_date else "",
            "Last Date": (
                drive.application_deadline.strftime("%d/%m/%Y")
                if drive and drive.application_deadline else ""
            ),
        })

    filename = f"applications_{student_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    exports_folder = current_app.config["EXPORTS_FOLDER"]
    filepath = os.path.join(exports_folder, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # also send csv on email
    mail_result = None
    if student.email:
        with open(filepath, "rb") as f:
            mail_result = send_placement_mail(
                subject="Your Application History - CSV Export",
                recipients=[student.email],
                recipient_group="student",
                body=(
                    f"Hi {student.name},\n\n"
                    f"Your placement application history export is ready.\n"
                    f"Total applications: {len(rows)}\n\n"
                    f"You can also download it directly from your dashboard.\n\n"
                    f"Regards,\nPlacement Cell"
                ),
                attachments=[(filename, "text/csv", f.read())],
            )

    return {
        "status": "SUCCESS",
        "filename": filename,
        "download_url": f"/exports/{filename}",
        "total_applications": len(rows),
        "mail_sent": bool(mail_result),
        "mail_error": mail_result.error if mail_result is not None and not mail_result.sent else "",
    }

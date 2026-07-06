from datetime import datetime

from models.applications import Application
from models.auth import User
from models.company import Company
from models.drive import Drive


def _company_name(company, company_user=None):
    if company:
        return company.company_name
    return company_user.name if company_user else "Unknown"


def month_window(period="previous", reference=None):
    reference = reference or datetime.utcnow()
    if period == "current":
        year = reference.year
        month = reference.month
    elif reference.month == 1:
        year = reference.year - 1
        month = 12
    else:
        year = reference.year
        month = reference.month - 1

    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    return start, end, start.strftime("%B %Y")


def build_monthly_report_data(period="previous"):
    start, end, month_label = month_window(period=period)
    drives = Drive.query.filter(
        Drive.drive_date >= start.date(),
        Drive.drive_date < end.date(),
    ).all()
    applications = Application.query.filter(
        Application.created_at >= start,
        Application.created_at < end,
    ).all()
    selected = [a for a in applications if (a.status or "").lower() in ("shortlisted", "approved")]
    applied_student_ids = {a.student_id for a in applications}

    breakdown = []
    for drive in drives:
        company_user = User.query.get(drive.company_id)
        company = Company.query.filter_by(user_id=drive.company_id).first()
        drive_applications = Application.query.filter(
            Application.drive_id == drive.id,
            Application.created_at >= start,
            Application.created_at < end,
        ).all()
        drive_selected = [
            app for app in drive_applications
            if (app.status or "").lower() in ("shortlisted", "approved")
        ]

        breakdown.append({
            "title": drive.title,
            "company": _company_name(company, company_user),
            "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "N/A",
            "applications": len(drive_applications),
            "selected": len(drive_selected),
        })

    return {
        "month_label": month_label,
        "start": start,
        "end": end,
        "drives": drives,
        "applications": applications,
        "selected": selected,
        "applied_students": len(applied_student_ids),
        "breakdown": breakdown,
    }


def render_monthly_report_html(data):
    rows = "".join(
        f"<tr><td>{item['title']}</td><td>{item['company']}</td>"
        f"<td>{item['drive_date']}</td><td>{item['applications']}</td>"
        f"<td>{item['selected']}</td></tr>"
        for item in data["breakdown"]
    )
    if not rows:
        rows = '<tr><td colspan="5">No drives in this month</td></tr>'

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Monthly Placement Report</title>
</head>
<body style="font-family:Arial,sans-serif;padding:24px;color:#1f2937;">
  <h1 style="color:#111827;">Monthly Placement Activity Report</h1>
  <h2 style="color:#374151;">{data["month_label"]}</h2>
  <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse;margin-bottom:24px;">
    <tr style="background:#f3f4f6;"><th>Metric</th><th>Count</th></tr>
    <tr><td>Drives Conducted</td><td>{len(data["drives"])}</td></tr>
    <tr><td>Students Applied</td><td>{data["applied_students"]}</td></tr>
    <tr><td>Total Applications Received</td><td>{len(data["applications"])}</td></tr>
    <tr><td>Students Shortlisted / Selected</td><td>{len(data["selected"])}</td></tr>
  </table>
  <h3>Drive-wise Breakdown</h3>
  <table border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse;">
    <tr style="background:#f3f4f6;">
      <th>Drive Title</th>
      <th>Company</th>
      <th>Starting Date</th>
      <th>Applications</th>
      <th>Selected</th>
    </tr>
    {rows}
  </table>
  <p style="margin-top:24px;color:#6b7280;font-size:0.9rem;">
    Generated on {datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")}
  </p>
</body>
</html>
"""

from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from extension import db, cache
from mail_utils import send_placement_mail
from report_utils import _company_name, build_monthly_report_data, render_monthly_report_html
from models.applications import Application
from models.auth import User
from models.company import Company
from models.drive import Drive

admin_bp = Blueprint("admin", __name__)

CACHE_TIMEOUT = 120  # 2 minutes for admin data


def _admin_check():
    user = User.query.get(int(get_jwt_identity()))
    if not user or user.role != "admin":
        return None
    return user


def _invalidate_admin_cache():
    for key in ("admin_summary", "admin_students", "admin_companies", "admin_drives",
                "admin_pending_drives", "admin_pending_companies", "admin_company_applications",
                "admin_student_applications"):
        cache.delete(key)


# dashboard summary

@admin_bp.route("/admin/summary", methods=["GET"])
@jwt_required()
def admin_summary():
    user = _admin_check()
    if not user:
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_summary")
    if cached:
        return jsonify(cached), 200

    students = User.query.filter_by(role="student").all()
    company_users = User.query.filter_by(role="company").all()
    drives = Drive.query.all()

    result = {
        "profile": {"name": user.name, "email": user.email},
        "stats": [
            {"label": "Total Students", "value": len(students)},
            {"label": "Total Companies", "value": len(company_users)},
            {"label": "Total Placement Drives", "value": len(drives)},
            {"label": "Approved Drives", "value": sum(1 for d in drives if d.is_approved)},
            {"label": "Pending Drives", "value": sum(1 for d in drives if not d.is_approved)},
            {"label": "Pending Companies", "value": sum(1 for c in company_users if c.is_blocked)},
        ],
    }
    cache.set("admin_summary", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


@admin_bp.route("/admin/monthly-report/download", methods=["GET"])
@jwt_required()
def admin_monthly_report_download():
    admin = _admin_check()
    if not admin:
        return jsonify({"message": "Admin access required"}), 403

    data = build_monthly_report_data(period="current")
    html = render_monthly_report_html(data)
    filename = f"monthly_report_{data['month_label'].replace(' ', '_').lower()}.html"
    mail_result = send_placement_mail(
        subject=f"Monthly Placement Report - {data['month_label']}",
        recipients=[admin.email],
        recipient_group="staff",
        html=html,
        attachments=[(filename, "text/html", html.encode("utf-8"))],
    )
    buffer = BytesIO(html.encode("utf-8"))
    buffer.seek(0)
    response = send_file(
        buffer,
        mimetype="text/html",
        as_attachment=True,
        download_name=filename,
    )
    response.headers["X-Mail-Sent"] = "true" if mail_result.sent else "false"
    response.headers["X-Mail-Error"] = (mail_result.error or "").replace("\r", " ").replace("\n", " ")
    return response


# students list

@admin_bp.route("/admin/students", methods=["GET"])
@jwt_required()
def admin_students():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_students")
    if cached:
        return jsonify(cached), 200

    result = [
        {
            "id": s.id,
            "name": s.name,
            "email": s.email,
            "status": "Blocked" if s.is_blocked else "Active",
        }
        for s in User.query.filter_by(role="student").all()
    ]
    cache.set("admin_students", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# companies list

@admin_bp.route("/admin/companies", methods=["GET"])
@jwt_required()
def admin_companies():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_companies")
    if cached:
        return jsonify(cached), 200

    result = []
    for cu in User.query.filter_by(role="company").all():
        company = Company.query.filter_by(user_id=cu.id).first()
        result.append({
            "id": cu.id,
            "name": _company_name(company, cu),
            "email": cu.email,
            "description": company.description if company else "",
            "status": "Approved" if not cu.is_blocked else "Pending",
        })

    cache.set("admin_companies", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# drives list

@admin_bp.route("/admin/drives", methods=["GET"])
@jwt_required()
def admin_drives():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_drives")
    if cached:
        return jsonify(cached), 200

    result = []
    for drive in Drive.query.all():
        company_user = User.query.get(drive.company_id)
        company = Company.query.filter_by(user_id=drive.company_id).first()
        result.append({
            "id": drive.id,
            "name": drive.title,
            "company": _company_name(company, company_user),
            "description": drive.description or "",
            "salary": drive.salary or "",
            "experience": drive.experience or "",
            "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "",
            "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive.application_deadline else "",
            "location": drive.location or "",
            "status": "Approved" if drive.is_approved else "Pending",
        })

    cache.set("admin_drives", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# pending drives

@admin_bp.route("/admin/pending-drives", methods=["GET"])
@jwt_required()
def admin_pending_drives():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_pending_drives")
    if cached:
        return jsonify(cached), 200

    result = []
    for drive in Drive.query.filter_by(is_approved=False).order_by(Drive.id.desc()).all():
        company_user = User.query.get(drive.company_id)
        company = Company.query.filter_by(user_id=drive.company_id).first()
        result.append({
            "id": drive.id,
            "name": drive.title,
            "company": _company_name(company, company_user),
            "description": drive.description or "",
            "salary": drive.salary or "",
            "experience": drive.experience or "",
            "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "",
            "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive.application_deadline else "",
            "location": drive.location or "",
            "status": "Pending",
        })

    cache.set("admin_pending_drives", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# approve drive

@admin_bp.route("/admin/approve-drive/<int:drive_id>", methods=["POST"])
@jwt_required()
def approve_drive(drive_id):
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404

    drive.is_approved = True
    db.session.commit()
    _invalidate_admin_cache()
    cache.delete(f"company_summary_{drive.company_id}")
    cache.delete(f"company_drives_{drive.company_id}")
    company_user = User.query.get(drive.company_id)
    mail_result = None
    if company_user and company_user.email:
        mail_result = send_placement_mail(
            subject=f"Drive approved: {drive.title}",
            recipients=[company_user.email],
            recipient_group="staff",
            body=(
                f"Hi {company_user.name},\n\n"
                f"Your placement drive '{drive.title}' has been approved by admin.\n"
                f"It is now visible to students for applications.\n\n"
                f"Regards,\nPlacement Portal"
            ),
        )
    response = {"message": "Drive approved successfully", "mail_sent": bool(mail_result)}
    if mail_result is not None and not mail_result.sent:
        response["mail_error"] = mail_result.error
        response["message"] += ", but email failed"
    elif mail_result is None:
        response["mail_error"] = "Company email not found"
        response["message"] += ", but company email not found"
    return jsonify(response), 200


# reject drive

@admin_bp.route("/admin/reject-drive/<int:drive_id>", methods=["POST"])
@jwt_required()
def reject_drive(drive_id):
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404

    company_id = drive.company_id
    db.session.delete(drive)
    db.session.commit()
    _invalidate_admin_cache()
    cache.delete(f"company_summary_{company_id}")
    cache.delete(f"company_drives_{company_id}")
    return jsonify({"message": "Drive rejected and removed"}), 200


# company registration requests

@admin_bp.route("/admin/company-applications", methods=["GET"])
@jwt_required()
def admin_company_applications():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_company_applications")
    if cached:
        return jsonify(cached), 200

    result = []
    for cu in User.query.filter_by(role="company").all():
        company = Company.query.filter_by(user_id=cu.id).first()
        is_approved = company is not None and not cu.is_blocked
        result.append({
            "id": cu.id,
            "name": _company_name(company, cu),
            "email": cu.email,
            "description": company.description if company else "",
            "status": "Approved" if is_approved else "Pending",
        })

    cache.set("admin_company_applications", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# student applications

@admin_bp.route("/admin/student-applications", methods=["GET"])
@jwt_required()
def admin_student_applications():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_student_applications")
    if cached:
        return jsonify(cached), 200

    result = []
    for application in Application.query.all():
        drive = Drive.query.get(application.drive_id)
        student = User.query.get(application.student_id)
        company_user = User.query.get(drive.company_id) if drive else None
        company = Company.query.filter_by(user_id=company_user.id).first() if company_user else None
        result.append({
            "id": application.id,
            "student_name": student.name if student else "Unknown",
            "student_email": student.email if student else "",
            "drive_name": drive.title if drive else "Unknown",
            "company_name": _company_name(company, company_user),
            "status": application.status,
            "created_at": application.created_at.strftime("%d/%m/%Y") if application.created_at else "",
            "resume_file": application.resume_file or "",
            "resume_url": f"/uploads/{application.resume_file}" if application.resume_file else "",
        })

    cache.set("admin_student_applications", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# pending companies

@admin_bp.route("/admin/pending-companies", methods=["GET"])
@jwt_required()
def pending_companies():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    cached = cache.get("admin_pending_companies")
    if cached:
        return jsonify(cached), 200

    result = [
        {"id": c.id, "name": c.name, "email": c.email, "is_blocked": c.is_blocked}
        for c in User.query.filter_by(role="company", is_blocked=True).all()
    ]
    cache.set("admin_pending_companies", result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# approve company

@admin_bp.route("/admin/approve-company/<int:user_id>", methods=["POST"])
@jwt_required()
def approve_company(user_id):
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    company = User.query.filter_by(id=user_id, role="company").first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.is_blocked = False
    db.session.commit()
    _invalidate_admin_cache()
    return jsonify({"message": "Company approved successfully"}), 200


# block company

@admin_bp.route("/admin/reject-company/<int:user_id>", methods=["POST"])
@jwt_required()
def reject_company(user_id):
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    company = User.query.filter_by(id=user_id, role="company").first()
    if not company:
        return jsonify({"message": "Company not found"}), 404

    company.is_blocked = True
    db.session.commit()
    _invalidate_admin_cache()
    return jsonify({"message": "Company rejected / blocked"}), 200


# block or unblock student

@admin_bp.route("/admin/block-student/<int:user_id>", methods=["POST"])
@jwt_required()
def block_student(user_id):
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    student = User.query.filter_by(id=user_id, role="student").first()
    if not student:
        return jsonify({"message": "Student not found"}), 404

    student.is_blocked = not student.is_blocked
    db.session.commit()
    _invalidate_admin_cache()
    action = "blocked" if student.is_blocked else "unblocked"
    return jsonify({"message": f"Student {action} successfully"}), 200


# search

@admin_bp.route("/admin/search", methods=["GET"])
@jwt_required()
def admin_search():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    q = (request.args.get("q") or "").strip().lower()
    search_type = request.args.get("type", "all")  # students | companies | drives | all

    if not q:
        return jsonify({"students": [], "companies": [], "drives": []}), 200

    result = {"students": [], "companies": [], "drives": []}

    if search_type in ("students", "all"):
        students = User.query.filter_by(role="student").all()
        result["students"] = [
            {"id": s.id, "name": s.name, "email": s.email,
             "status": "Blocked" if s.is_blocked else "Active"}
            for s in students
            if q in s.name.lower() or q in s.email.lower()
        ]

    if search_type in ("companies", "all"):
        company_users = User.query.filter_by(role="company").all()
        for cu in company_users:
            company = Company.query.filter_by(user_id=cu.id).first()
            name = _company_name(company, cu)
            if q in name.lower() or q in cu.email.lower():
                result["companies"].append({
                    "id": cu.id,
                    "name": name,
                    "email": cu.email,
                    "status": "Approved" if not cu.is_blocked else "Pending",
                })

    if search_type in ("drives", "all"):
        drives = Drive.query.all()
        for drive in drives:
            if q in (drive.title or "").lower() or q in (drive.location or "").lower():
                company_user = User.query.get(drive.company_id)
                company = Company.query.filter_by(user_id=drive.company_id).first()
                result["drives"].append({
                    "id": drive.id,
                    "name": drive.title,
                    "company": _company_name(company, company_user),
                    "status": "Approved" if drive.is_approved else "Pending",
                })

    return jsonify(result), 200


# reset company approvals

@admin_bp.route("/admin/reset-all-companies-pending", methods=["POST"])
@jwt_required()
def reset_all_companies_pending():
    if not _admin_check():
        return jsonify({"message": "Admin access required"}), 403

    companies = User.query.filter_by(role="company").all()
    for c in companies:
        c.is_blocked = True
    db.session.commit()
    _invalidate_admin_cache()
    return jsonify({"message": f"{len(companies)} companies pending mein set ho gayi"}), 200

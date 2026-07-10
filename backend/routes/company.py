from datetime import datetime, time, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extension import db, cache
from mail_utils import send_placement_mail
from models.applications import Application
from models.auth import User
from models.company import Company
from models.drive import Drive

company_bp = Blueprint("company", __name__)

CACHE_TIMEOUT = 60  # 1 minute


def _current_user():
    return User.query.get(int(get_jwt_identity()))


def _require_company():
    user = _current_user()
    if not user:
        return None, (jsonify({"message": "User not found"}), 404)
    if user.role != "company":
        return None, (jsonify({"message": "Company access required"}), 403)
    return user, None


def _invalidate_company_cache(user_id):
    cache.delete(f"company_summary_{user_id}")
    cache.delete(f"company_drives_{user_id}")
    cache.delete(f"company_applications_{user_id}")


def _invalidate_admin_cache():
    for key in ("admin_summary", "admin_students", "admin_companies", "admin_drives",
                "admin_pending_drives", "admin_pending_companies", "admin_company_applications",
                "admin_student_applications"):
        cache.delete(key)


def _format_interview_time(value):
    return value.strftime("%d/%m/%Y %H:%M UTC") if value else ""


def _default_interview_time(drive):
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    return datetime.combine(tomorrow, time(hour=10))


def _parse_interview_time(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%Y-%m-%d":
                return datetime.combine(parsed.date(), time(hour=10))
            return parsed
        except ValueError:
            continue
    return None


def _application_info(application):
    drive = Drive.query.get(application.drive_id)
    student = User.query.get(application.student_id)
    return {
        "id": application.id,
        "student_name": student.name if student else "Unknown",
        "drive_name": drive.title if drive else "Unknown",
        "salary": drive.salary if drive else "",
        "experience": drive.experience if drive else "",
        "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive and drive.drive_date else "",
        "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive and drive.application_deadline else "",
        "location": drive.location if drive else "",
        "status": application.status,
        "resume_file": application.resume_file or "",
        "resume_url": f"/uploads/{application.resume_file}" if application.resume_file else "",
        "interview_scheduled_at": _format_interview_time(application.interview_scheduled_at),
        "interview_mode": application.interview_mode or "",
        "interview_location": application.interview_location or "",
        "created_at": application.created_at.strftime("%d/%m/%Y") if application.created_at else "",
    }


def _get_owned_application(user_id, application_id):
    application = Application.query.get(application_id)
    if not application:
        return None
    drive = Drive.query.get(application.drive_id)
    if not drive or drive.company_id != user_id:
        return None
    return application


def _notify_student_application_status(application, drive, status_label):
    from mail_utils import MailResult
    student = User.query.get(application.student_id)
    if not student or not student.email:
        return MailResult(False, "Student email not found")

    company_user = User.query.get(drive.company_id) if drive else None
    company = Company.query.filter_by(user_id=drive.company_id).first() if drive else None
    company_name = company.company_name if company else (company_user.name if company_user else "Company")
    interview_lines = ""
    if application.interview_scheduled_at:
        interview_lines = (
            f"\nInterview Schedule:\n"
            f"Date & Time: {_format_interview_time(application.interview_scheduled_at)}\n"
            f"Mode: {application.interview_mode or 'In-person'}\n"
            f"Location/Link: {application.interview_location or drive.location or 'Placement Cell'}\n"
        )

    if (application.status or "").lower() == "shortlisted":
        shortlist_interview_text = interview_lines or "Interview details will be shared soon.\n"
        return send_placement_mail(
            subject=f"You are shortlisted for {drive.title}",
            recipients=[student.email],
            recipient_group="student",
            deliver_to_actual_recipients=True,
            body=(
                f"Hi {student.name},\n\n"
                f"Congratulations! You have been shortlisted by {company_name} "
                f"for the '{drive.title}' drive.\n"
                f"{shortlist_interview_text}\n"
                f"Please be available on time and check the Placement Portal for updates.\n\n"
                f"Regards,\nPlacement Portal"
            ),
        )

    return send_placement_mail(
        subject=f"Application update for {drive.title}",
        recipients=[student.email],
        recipient_group="student",
        body=(
            f"Hi {student.name},\n\n"
            f"Your application for '{drive.title}' has been updated.\n\n"
            f"Current Status: {status_label}\n"
            f"{interview_lines}\n"
            f"Regards,\nPlacement Portal"
        ),
    )


def _update_application_status(user_id, application_id, status, status_label, schedule_interview=False):
    application = _get_owned_application(user_id, application_id)
    if not application:
        return None, (jsonify({"message": "Application not found"}), 404)

    drive = Drive.query.get(application.drive_id)
    data = request.get_json(silent=True) or {}
    application.status = status

    if schedule_interview:
        interview_at = _parse_interview_time(data.get("interview_scheduled_at"))
        application.interview_scheduled_at = interview_at or application.interview_scheduled_at or _default_interview_time(drive)
        application.interview_mode = (data.get("interview_mode") or application.interview_mode or "In-person").strip()
        application.interview_location = (
            data.get("interview_location")
            or application.interview_location
            or (drive.location if drive else None)
            or "Placement Cell"
        ).strip()

    db.session.commit()
    _invalidate_company_cache(user_id)
    cache.delete(f"student_summary_{application.student_id}")
    cache.delete("admin_summary")
    cache.delete("admin_student_applications")
    mail_result = None
    if drive:
        mail_result = _notify_student_application_status(application, drive, status_label)

    return application, None, mail_result


# dashboard summary

@company_bp.route("/company/summary", methods=["GET"])
@jwt_required()
def company_summary():
    user, err = _require_company()
    if err:
        return err

    cache_key = f"company_summary_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    company = Company.query.filter_by(user_id=user.id).first()
    drives = Drive.query.filter_by(company_id=user.id).all()
    approved_drives = [d for d in drives if d.is_approved]
    applications = []
    for drive in drives:
        applications.extend(Application.query.filter_by(drive_id=drive.id).all())

    result = {
        "profile": {
            "name": user.name,
            "email": user.email,
            "company_name": company.company_name if company else user.name,
            "description": company.description if company else "",
        },
        "stats": [
            {"label": "Drives", "value": len(drives)},
            {"label": "Approved Drives", "value": len(approved_drives)},
            {"label": "Applications", "value": len(applications)},
            {"label": "Shortlisted", "value": sum(1 for a in applications if (a.status or "").lower() == "shortlisted")},
        ],
    }
    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# update profile

@company_bp.route("/company/profile", methods=["PUT"])
@jwt_required()
def company_update_profile():
    user, err = _require_company()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    company_name = (data.get("company_name") or data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    description = (data.get("description") or "").strip()

    if not company_name:
        return jsonify({"message": "Company name required hai"}), 400
    if not email or "@" not in email:
        return jsonify({"message": "Valid email required hai"}), 400

    existing_user = User.query.filter(
        db.func.lower(User.email) == email,
        User.id != user.id,
    ).first()
    if existing_user:
        return jsonify({"message": "Ye email kisi aur account par already registered hai"}), 400

    company = Company.query.filter_by(user_id=user.id).first()
    if not company:
        company = Company(user_id=user.id, company_name=company_name)
        db.session.add(company)

    user.name = company_name
    user.email = email
    company.company_name = company_name
    company.description = description

    db.session.commit()
    _invalidate_company_cache(user.id)
    _invalidate_admin_cache()

    return jsonify({
        "message": "Company profile updated successfully",
        "profile": {
            "name": user.name,
            "email": user.email,
            "company_name": company.company_name,
            "description": company.description or "",
        },
    }), 200


# create drive

@company_bp.route("/company/drives", methods=["POST"])
@jwt_required()
def company_create_drive():
    user, err = _require_company()
    if err:
        return err

    if user.is_blocked:
        return jsonify({"message": "Your company account is not approved yet"}), 403

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    salary = (data.get("salary") or "").strip()
    experience = (data.get("experience") or "").strip()
    location = (data.get("location") or "").strip()
    drive_date_text = (data.get("drive_date") or "").strip()
    deadline_text = (data.get("application_deadline") or "").strip()
    cgpa_required = data.get("cgpa_required")
    branch_required = (data.get("branch_required") or "").strip()

    if not title or not salary or not experience or not drive_date_text or not deadline_text:
        return jsonify({"message": "Title, salary, experience, starting date aur last date required hai"}), 400

    drive_date = None
    try:
        drive_date = datetime.strptime(drive_date_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Starting date invalid hai (YYYY-MM-DD chahiye)"}), 400

    application_deadline = None
    try:
        application_deadline = datetime.strptime(deadline_text, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Last date invalid hai (YYYY-MM-DD chahiye)"}), 400

    if application_deadline < drive_date:
        return jsonify({"message": "Last date starting date se pehle nahi ho sakti"}), 400

    drive = Drive(
        title=title,
        description=description,
        salary=salary,
        experience=experience,
        drive_date=drive_date,
        location=location,
        company_id=user.id,
        is_approved=False,
        application_deadline=application_deadline,
        cgpa_required=float(cgpa_required) if cgpa_required else None,
        branch_required=branch_required or None,
    )
    db.session.add(drive)
    db.session.commit()
    _invalidate_company_cache(user.id)
    _invalidate_admin_cache()
    return jsonify({"message": "Drive created successfully, awaiting admin approval"}), 201


# company drives

@company_bp.route("/company/drives", methods=["GET"])
@jwt_required()
def company_drives():
    user, err = _require_company()
    if err:
        return err

    cache_key = f"company_drives_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    company = Company.query.filter_by(user_id=user.id).first()
    result = [
        {
            "id": d.id,
            "title": d.title,
            "company": company.company_name if company else user.name,
            "description": d.description or "",
            "salary": d.salary or "",
            "experience": d.experience or "",
            "drive_date": d.drive_date.strftime("%d/%m/%Y") if d.drive_date else "",
            "application_deadline": d.application_deadline.strftime("%d/%m/%Y") if d.application_deadline else "",
            "location": d.location or "",
            "cgpa_required": d.cgpa_required or "",
            "branch_required": d.branch_required or "",
            "window": "Live Now" if d.is_approved else "Waiting Approval",
            "status": "Approved" if d.is_approved else "Pending",
        }
        for d in Drive.query.filter_by(company_id=user.id).order_by(Drive.id.desc()).all()
    ]
    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# received applications

@company_bp.route("/company/applications", methods=["GET"])
@jwt_required()
def company_applications():
    user, err = _require_company()
    if err:
        return err

    cache_key = f"company_applications_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    result = []
    for drive in Drive.query.filter_by(company_id=user.id).order_by(Drive.id.desc()).all():
        for app in Application.query.filter_by(drive_id=drive.id).all():
            result.append({**_application_info(app), "drive_name": drive.title})

    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# shortlist student

@company_bp.route("/company/applications/<int:application_id>/shortlist", methods=["POST"])
@jwt_required()
def company_shortlist_application(application_id):
    user, err = _require_company()
    if err:
        return err

    application, err, mail_result = _update_application_status(
        user.id,
        application_id,
        "shortlisted",
        "Shortlisted",
        schedule_interview=True,
    )
    if err:
        return err
    response = {
        "message": "Application shortlisted and interview scheduled",
        "mail_sent": bool(mail_result),
        "interview_scheduled_at": _format_interview_time(application.interview_scheduled_at),
    }
    if mail_result is not None and not mail_result.sent:
        response["mail_error"] = mail_result.error
        response["message"] += ", but email failed"
    return jsonify(response), 200


# reject student

@company_bp.route("/company/applications/<int:application_id>/reject", methods=["POST"])
@jwt_required()
def company_reject_application(application_id):
    user, err = _require_company()
    if err:
        return err

    _, err, mail_result = _update_application_status(user.id, application_id, "rejected", "Rejected")
    if err:
        return err
    response = {"message": "Application rejected", "mail_sent": bool(mail_result)}
    if mail_result is not None and not mail_result.sent:
        response["mail_error"] = mail_result.error
        response["message"] += ", but email failed"
    return jsonify(response), 200


# select student

@company_bp.route("/company/applications/<int:application_id>/select", methods=["POST"])
@jwt_required()
def company_select_application(application_id):
    user, err = _require_company()
    if err:
        return err

    _, err, mail_result = _update_application_status(user.id, application_id, "approved", "Approved")
    if err:
        return err
    response = {"message": "Student selected (final)", "mail_sent": bool(mail_result)}
    if mail_result is not None and not mail_result.sent:
        response["mail_error"] = mail_result.error
        response["message"] += ", but email failed"
    return jsonify(response), 200


# set application pending

@company_bp.route("/company/applications/<int:application_id>/pending", methods=["POST"])
@jwt_required()
def company_pending_application(application_id):
    user, err = _require_company()
    if err:
        return err

    _, err, mail_result = _update_application_status(user.id, application_id, "pending", "Pending")
    if err:
        return err
    response = {"message": "Application set to pending", "mail_sent": bool(mail_result)}
    if mail_result is not None and not mail_result.sent:
        response["mail_error"] = mail_result.error
        response["message"] += ", but email failed"
    return jsonify(response), 200

import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from extension import db, cache
from mail_utils import send_placement_mail
from models.applications import Application
from models.auth import User
from models.company import Company
from models.drive import Drive

student_bp = Blueprint("student", __name__)

CACHE_TIMEOUT = 60  # 1 minute for student-specific data


def _current_user():
    return User.query.get(int(get_jwt_identity()))


def _require_student():
    user = _current_user()
    if not user:
        return None, (jsonify({"message": "User not found"}), 404)
    if user.role != "student":
        return None, (jsonify({"message": "Student access required"}), 403)
    if user.is_blocked:
        return None, (jsonify({"message": "Your account has been blocked"}), 403)
    return user, None


def _company_info(company_user_id):
    company = Company.query.filter_by(user_id=company_user_id).first()
    if not company:
        return None
    company_user = User.query.get(company_user_id)
    return {
        "id": company.id,
        "name": company.company_name,
        "description": company.description or "",
        "status": "Open" if company_user and not company_user.is_blocked else "Pending",
    }


# dashboard summary

@student_bp.route("/student/summary", methods=["GET"])
@jwt_required()
def student_summary():
    user, err = _require_student()
    if err:
        return err

    cache_key = f"student_summary_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    applications = [
        app for app in Application.query.filter_by(student_id=user.id).order_by(Application.created_at.desc()).all()
        if Drive.query.get(app.drive_id) and Drive.query.get(app.drive_id).is_approved
    ]
    companies = User.query.filter_by(role="company").all()

    result = {
        "profile": {"name": user.name, "email": user.email, "cgpa": user.cgpa, "branch": user.branch or ""},
        "student": {"name": user.name, "email": user.email},
        "department": user.branch or "Computer Science",
        "stats": [
            {"label": "Applied Drives", "value": len(applications)},
            {"label": "Shortlisted", "value": sum(1 for a in applications if (a.status or "").lower() == "shortlisted")},
            {"label": "Organizations", "value": len(companies)},
        ],
    }
    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


@student_bp.route("/student/profile", methods=["PUT"])
@jwt_required()
def student_update_profile():
    user, err = _require_student()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    branch = (data.get("branch") or data.get("department") or "").strip()
    cgpa = data.get("cgpa")

    if name:
        user.name = name
    user.branch = branch or None

    if cgpa in ("", None):
        user.cgpa = None
    else:
        try:
            user.cgpa = float(cgpa)
        except (TypeError, ValueError):
            return jsonify({"message": "CGPA invalid hai"}), 400

    db.session.commit()
    cache.delete(f"student_summary_{user.id}")
    return jsonify({"message": "Profile updated successfully"}), 200


# companies and drives

@student_bp.route("/student/companies", methods=["GET"])
@jwt_required()
def student_companies():
    user, err = _require_student()
    if err:
        return err

    # search company
    q = (request.args.get("q") or "").strip().lower()

    cache_key = f"student_companies_{user.id}_{q}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    companies = []
    for cu in User.query.filter_by(role="company").all():
        company_info = _company_info(cu.id) or {
            "id": cu.id, "name": cu.name, "description": "", "status": "Pending"
        }
        company_info["id"] = cu.id
        company_info["email"] = cu.email

        drives_q = Drive.query.filter_by(company_id=cu.id, is_approved=True)
        drives = []
        for drive in drives_q.all():
            if q and q not in (drive.title or "").lower() and q not in company_info["name"].lower():
                continue
            drives.append({
                "id": drive.id,
                "title": drive.title,
                "salary": drive.salary or "",
                "experience": drive.experience or "",
                "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "",
                "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive.application_deadline else "",
                "location": drive.location or "",
                "cgpa_required": drive.cgpa_required or "",
                "branch_required": drive.branch_required or "",
                "applied": Application.query.filter_by(student_id=user.id, drive_id=drive.id).first() is not None,
            })

        company_info["drives"] = drives
        if not q or q in company_info["name"].lower() or drives:
            companies.append(company_info)

    cache.set(cache_key, companies, timeout=CACHE_TIMEOUT)
    return jsonify(companies), 200


# approved drives

@student_bp.route("/student/drives", methods=["GET"])
@jwt_required()
def student_drives():
    user, err = _require_student()
    if err:
        return err

    cache_key = f"student_drives_{user.id}"
    cached = cache.get(cache_key)
    if cached:
        return jsonify(cached), 200

    result = []
    for drive in Drive.query.filter_by(is_approved=True).all():
        company_user = User.query.get(drive.company_id)
        company = _company_info(drive.company_id)
        result.append({
            "id": drive.id,
            "name": drive.title,
            "company": company["name"] if company else (company_user.name if company_user else "Unknown"),
            "description": drive.description or "",
            "salary": drive.salary or "",
            "experience": drive.experience or "",
            "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "",
            "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive.application_deadline else "",
            "location": drive.location or "",
            "cgpa_required": drive.cgpa_required or "",
            "branch_required": drive.branch_required or "",
            "applied": Application.query.filter_by(student_id=user.id, drive_id=drive.id).first() is not None,
        })

    cache.set(cache_key, result, timeout=CACHE_TIMEOUT)
    return jsonify(result), 200


# apply drive

@student_bp.route("/student/apply-drive/<int:drive_id>", methods=["POST"])
@jwt_required()
def student_apply_drive(drive_id):
    user, err = _require_student()
    if err:
        return err

    drive = Drive.query.get(drive_id)
    if not drive:
        return jsonify({"message": "Drive not found"}), 404
    if not drive.is_approved:
        return jsonify({"message": "Drive is not approved yet"}), 400

    today = datetime.utcnow().date()
    if drive.drive_date and today < drive.drive_date:
        return jsonify({"message": "Applications abhi start nahi hui hain"}), 400
    if drive.application_deadline and today > drive.application_deadline:
        return jsonify({"message": "Application last date nikal chuki hai"}), 400

    if Application.query.filter_by(student_id=user.id, drive_id=drive.id).first():
        return jsonify({"message": "You have already applied for this drive"}), 400

    if drive.cgpa_required is not None:
        if user.cgpa is None:
            return jsonify({"message": "Apply karne se pehle profile me CGPA update karo"}), 400
        if user.cgpa < drive.cgpa_required:
            return jsonify({"message": f"Not eligible: minimum CGPA {drive.cgpa_required} required hai"}), 400

    if drive.branch_required:
        allowed_branches = [
            item.strip().lower()
            for item in drive.branch_required.split(",")
            if item.strip()
        ]
        if allowed_branches and (user.branch or "").strip().lower() not in allowed_branches:
            return jsonify({"message": "Not eligible: branch requirement match nahi ho raha"}), 400

    resume = request.files.get("resume")
    saved_filename = None
    if resume and resume.filename:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        safe_name = secure_filename(resume.filename)
        saved_filename = f"resume_{user.id}_{drive.id}_{safe_name}"
        resume.save(os.path.join(upload_folder, saved_filename))

    db.session.add(Application(
        student_id=user.id,
        drive_id=drive.id,
        resume_file=saved_filename,
        status="pending",
    ))
    db.session.commit()

    company_user = User.query.get(drive.company_id)
    company = Company.query.filter_by(user_id=drive.company_id).first()
    company_name = company.company_name if company else (company_user.name if company_user else "Company")

    if company_user and company_user.email:
        send_placement_mail(
            subject=f"New application for {drive.title}",
            recipients=[company_user.email],
            recipient_group="staff",
            body=(
                f"Hello {company_name},\n\n"
                f"A new student has applied for your drive.\n\n"
                f"Student Name: {user.name}\n"
                f"Student Email: {user.email}\n"
                f"Drive Title: {drive.title}\n"
                f"Application Time: {datetime.utcnow().strftime('%d/%m/%Y %H:%M UTC')}\n\n"
                f"Please log in to the Placement Portal to review the application."
            ),
        )

    if user.email:
        send_placement_mail(
            subject=f"Application received for {drive.title}",
            recipients=[user.email],
            recipient_group="student",
            body=(
                f"Hi {user.name},\n\n"
                f"Your application for '{drive.title}' has been submitted successfully.\n"
                f"We will notify you if there is any update.\n\n"
                f"Regards,\nPlacement Portal"
            ),
        )

    # clear old cache
    cache.delete(f"student_companies_{user.id}_")
    cache.delete(f"student_drives_{user.id}")
    cache.delete(f"student_summary_{user.id}")
    cache.delete(f"company_summary_{drive.company_id}")
    cache.delete(f"company_applications_{drive.company_id}")
    cache.delete("admin_summary")
    cache.delete("admin_student_applications")

    return jsonify({"message": "Application submitted successfully"}), 201


# applied drives

@student_bp.route("/student/applied-drives", methods=["GET"])
@jwt_required()
def student_applied_drives():
    user, err = _require_student()
    if err:
        return err

    result = []
    for app in Application.query.filter_by(student_id=user.id).order_by(Application.created_at.desc()).all():
        drive = Drive.query.get(app.drive_id)
        if not drive or not drive.is_approved:
            continue
        company_user = User.query.get(drive.company_id)
        company = _company_info(company_user.id) if company_user else None
        result.append({
            "id": drive.id,
            "name": drive.title,
            "company": company["name"] if company else (company_user.name if company_user else "Unknown"),
            "salary": drive.salary or "",
            "experience": drive.experience or "",
            "drive_date": drive.drive_date.strftime("%d/%m/%Y") if drive.drive_date else "",
            "application_deadline": drive.application_deadline.strftime("%d/%m/%Y") if drive.application_deadline else "",
            "location": drive.location or "",
            "date": app.created_at.strftime("%d/%m/%Y") if app.created_at else "",
            "status": app.status,
            "resume_file": app.resume_file or "",
            "resume_url": f"/uploads/{app.resume_file}" if app.resume_file else "",
        })

    return jsonify(result), 200


# application history

@student_bp.route("/student/history", methods=["GET"])
@jwt_required()
def student_history():
    user, err = _require_student()
    if err:
        return err

    result = []
    for app in Application.query.filter_by(student_id=user.id).order_by(Application.created_at.desc()).all():
        drive = Drive.query.get(app.drive_id)
        if not drive or not drive.is_approved:
            continue
        status_val = (app.status or "").lower()
        if status_val == "shortlisted":
            result_label = "Short Listed"
        elif status_val == "rejected":
            result_label = "Rejected"
        elif status_val == "approved":
            result_label = "Approved"
        else:
            result_label = app.status.title() if app.status else "Pending"

        result.append({
            "interview": "In-person",
            "jobTitle": drive.title if drive else "Unknown",
            "result": result_label,
            "remark": (
                f"Interview: {app.interview_scheduled_at.strftime('%d/%m/%Y %H:%M UTC')}"
                if app.interview_scheduled_at
                else ("Resume uploaded" if app.resume_file else "None")
            ),
            "company_name": "",
            "drive_name": drive.title if drive else "Unknown",
            "status": app.status,
            "interview_scheduled_at": app.interview_scheduled_at.strftime("%d/%m/%Y %H:%M UTC") if app.interview_scheduled_at else "",
            "interview_mode": app.interview_mode or "",
            "interview_location": app.interview_location or "",
            "created_at": app.created_at.strftime("%d/%m/%Y") if app.created_at else "",
        })

    return jsonify(result), 200


# export csv

@student_bp.route("/student/export-csv", methods=["POST"])
@jwt_required()
def student_export_csv():
    user, err = _require_student()
    if err:
        return err

    from tasks import export_student_csv
    task = export_student_csv.delay(user.id)
    return jsonify({"message": "CSV export started", "task_id": task.id}), 202


# check export status

@student_bp.route("/student/task-status/<task_id>", methods=["GET"])
@jwt_required()
def task_status(task_id):
    user, err = _require_student()
    if err:
        return err

    from celery.result import AsyncResult
    from extension import celery
    result = AsyncResult(task_id, app=celery)

    if result.state == "PENDING":
        return jsonify({"state": "PENDING", "status": "Task is waiting…"}), 200
    elif result.state == "PROGRESS":
        return jsonify({"state": "PROGRESS", "status": result.info.get("status", "")}), 200
    elif result.state == "SUCCESS":
        return jsonify({"state": "SUCCESS", **result.result}), 200
    else:
        return jsonify({"state": result.state, "status": str(result.info)}), 200

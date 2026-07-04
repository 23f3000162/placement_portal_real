import os
from celery.schedules import crontab
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash

load_dotenv()

from extension import db, jwt, cache, mail, celery
from models.auth import User
from models.company import Company
from models.drive import Drive
from models.applications import Application

from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp
from routes.company import company_bp

app = Flask(__name__)

# app settings
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portal.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key")
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")
app.config["EXPORTS_FOLDER"] = os.path.join(app.root_path, "exports")

# redis and celery
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
app.config["CELERY_BROKER_URL"] = REDIS_URL
app.config["CELERY_RESULT_BACKEND"] = REDIS_URL

# cache settings
app.config["CACHE_TYPE"] = os.environ.get("CACHE_TYPE", "SimpleCache")
app.config["CACHE_REDIS_URL"] = REDIS_URL
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # 5 minutes

# mail settings
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME", "noreply@placement.com")

# connect extensions
db.init_app(app)
jwt.init_app(app)
cache.init_app(app)
mail.init_app(app)
CORS(app)

# celery schedule
celery.conf.update(
    broker_url=app.config["CELERY_BROKER_URL"],
    result_backend=app.config["CELERY_RESULT_BACKEND"],
    timezone="UTC",
    beat_schedule={
        "daily-reminders": {
            "task": "tasks.send_daily_reminders",
            "schedule": crontab(hour=8, minute=0),
        },
        "monthly-report": {
            "task": "tasks.send_monthly_report",
            "schedule": crontab(day_of_month=1, hour=6, minute=0),
        },
    },
)


class ContextTask(celery.Task):
    # flask context is needed in celery tasks
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)


celery.Task = ContextTask

# make upload folders
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["EXPORTS_FOLDER"], exist_ok=True)

# routes
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(company_bp)

# create database and admin
with app.app_context():
    db.create_all()

    # add missing column in old database
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE drive ADD COLUMN application_deadline DATE"))
            conn.commit()
    except Exception:
        pass

    for statement in (
        "ALTER TABLE user ADD COLUMN cgpa FLOAT",
        "ALTER TABLE user ADD COLUMN branch VARCHAR(100)",
    ):
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text(statement))
                conn.commit()
        except Exception:
            pass

    admin_email = os.environ.get("ADMIN_EMAIL") or app.config["MAIL_USERNAME"] or "admin@gmail.com"
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    admin_user = User.query.filter_by(role="admin").first()

    if not admin_user:
        db.session.add(User(
            name="admin",
            email=admin_email,
            password=generate_password_hash(admin_password),
            role="admin"
        ))
    else:
        admin_user.email = admin_email
        admin_user.password = generate_password_hash(admin_password)
        admin_user.is_blocked = False

    db.session.commit()

    for company_user in User.query.filter_by(role="company").all():
        if not Company.query.filter_by(user_id=company_user.id).first():
            db.session.add(Company(
                user_id=company_user.id,
                company_name=company_user.name,
                description=""
            ))
    db.session.commit()


# file download routes
@app.route("/")
def home():
    return "Placement Portal"


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.isfile(path):
        return {"message": "File not found"}, 404
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)


@app.route("/exports/<path:filename>")
def download_export(filename):
    path = os.path.join(app.config["EXPORTS_FOLDER"], filename)
    if not os.path.isfile(path):
        return {"message": "File not found"}, 404
    return send_from_directory(app.config["EXPORTS_FOLDER"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

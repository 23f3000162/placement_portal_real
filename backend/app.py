import os
from celery.schedules import crontab
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

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
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com").strip()
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").strip().lower() in ("true", "1", "yes")
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "False").strip().lower() in ("true", "1", "yes")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "").strip()
# Remove any accidental spaces from gmail App Password
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "").strip().replace(" ", "")
app.config["MAIL_DEFAULT_SENDER"] = (
    os.environ.get("MAIL_DEFAULT_SENDER", "").strip()
    or app.config["MAIL_USERNAME"]
    or "noreply@placement.com"
)
app.config["MAIL_OVERRIDE_RECIPIENTS"] = os.environ.get("MAIL_OVERRIDE_RECIPIENTS", "").strip()
app.config["MAIL_STUDENT_RECIPIENTS"] = os.environ.get("MAIL_STUDENT_RECIPIENTS", "").strip()
app.config["MAIL_STAFF_RECIPIENTS"] = os.environ.get("MAIL_STAFF_RECIPIENTS", "").strip()
app.config["MAIL_SUPPRESS_SEND"] = os.environ.get("MAIL_SUPPRESS_SEND", "False").strip().lower() in ("true", "1", "yes")

# connect extensions
db.init_app(app)
jwt.init_app(app)
cache.init_app(app)
mail.init_app(app)
CORS(app, expose_headers=["Content-Disposition", "X-Mail-Sent", "X-Mail-Error"])

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
        "ALTER TABLE application ADD COLUMN interview_scheduled_at DATETIME",
        "ALTER TABLE application ADD COLUMN interview_mode VARCHAR(50)",
        "ALTER TABLE application ADD COLUMN interview_location VARCHAR(255)",
    ):
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text(statement))
                conn.commit()
        except Exception:
            pass

    admin_user = User.query.filter_by(role="admin").first()
    admin_email = os.environ.get("ADMIN_EMAIL") or (admin_user.email if admin_user else "admin@gmail.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

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
    import subprocess
    import atexit
    import sys
    import os
    
    # Only run background processes in the main reloader process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("🚀 Starting Redis and Celery in the background...")
        processes = []
        
        # Start redis
        try:
            if subprocess.call(["redis-cli", "ping"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
                p_redis = subprocess.Popen(["redis-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                processes.append(p_redis)
                print("Redis started")
            else:
                print("Redis is already running")
        except FileNotFoundError:
            print("⚠️ redis-server not found, ensure redis is installed.")

        # Start Celery worker
        try:
            p_worker = subprocess.Popen([sys.executable, "-m", "celery", "-A", "worker.celery", "worker", "--loglevel=info"], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(p_worker)
            print("Celery Worker started")
        except Exception as e:
            print(f"Failed to start Celery worker: {e}")
            
        # Start Celery beat
        try:
            p_beat = subprocess.Popen([sys.executable, "-m", "celery", "-A", "worker.celery", "beat", "--loglevel=info"], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes.append(p_beat)
            print("Celery Beat started")
        except Exception as e:
            print(f"Failed to start Celery beat: {e}")
            
        def cleanup():
            print("\n Stopping background services (Redis/Celery)...")
            for p in processes:
                try:
                    p.terminate()
                except:
                    pass
        
        atexit.register(cleanup)

    app.run(debug=True)

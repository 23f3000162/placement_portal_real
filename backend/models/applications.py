from extension import db 
from datetime import datetime
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'), nullable=False)
    resume_file = db.Column(db.String(255))
    status = db.Column(db.String(20),default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interview_scheduled_at = db.Column(db.DateTime, nullable=True)
    interview_mode = db.Column(db.String(50), nullable=True)
    interview_location = db.Column(db.String(255), nullable=True)
    

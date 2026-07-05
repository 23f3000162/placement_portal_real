from extension import db


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    salary = db.Column(db.String(100))
    experience = db.Column(db.String(100))
    drive_date = db.Column(db.Date)
    location = db.Column(db.String(100))
    company_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    application_deadline = db.Column(db.Date, nullable=True)
    cgpa_required = db.Column(db.Float, nullable=True)
    branch_required = db.Column(db.String(200), nullable=True)

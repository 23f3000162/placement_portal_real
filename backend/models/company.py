from extension import db

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comapny_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    @property
    def company_name(self):
        return self.comapny_name

    @company_name.setter
    def company_name(self, value):
        self.comapny_name = value

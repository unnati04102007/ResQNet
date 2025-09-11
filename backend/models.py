# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email}>"

class DisasterReport(db.Model):
    __tablename__ = 'disaster_report'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    image_path = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')  # pending/verified/rejected
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "lat": self.lat,
            "lon": self.lon,
            "image": self.image_path,
            "status": self.status,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Volunteer(db.Model):
    __tablename__ = 'volunteer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact = db.Column(db.String(120))
    skills = db.Column(db.String(255))
    location = db.Column(db.String(255))
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resource(db.Model):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key=True)
    resource_type = db.Column(db.String(120))  # eg: water, medical, shelter
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    location = db.Column(db.String(255))
    contact = db.Column(db.String(120))
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)

class Donation(db.Model):
    __tablename__ = 'donation'
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(120))
    donor_contact = db.Column(db.String(120))
    amount = db.Column(db.Float)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=True)
    resource = db.relationship('Resource', backref=db.backref('donations', lazy=True))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIFeedback(db.Model):
    __tablename__ = 'ai_feedback'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('disaster_report.id'))
    report = db.relationship('DisasterReport', backref=db.backref('ai_feedback', lazy=True))
    model_name = db.Column(db.String(120))
    confidence = db.Column(db.Float)
    verdict = db.Column(db.String(200))  # eg: "likely_true" / "likely_false"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

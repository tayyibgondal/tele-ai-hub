from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(200), nullable=True)
    position = db.Column(db.String(200), nullable=True)

    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True)
    product_updates = db.Column(db.Boolean, default=True)
    security_alerts = db.Column(db.Boolean, default=True)
    marketing_comms = db.Column(db.Boolean, default=False)

    # Privacy settings
    allow_analytics = db.Column(db.Boolean, default=True)
    show_profile = db.Column(db.Boolean, default=False)
    two_factor_auth = db.Column(db.Boolean, default=False)

    is_active = db.Column(db.Boolean, default=True)  # Default is True  

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

import os

class Config:
    SECRET_KEY = os.urandom(24)  # Random secret key for session management
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

import os
from dotenv import load_dotenv

load_dotenv()  # load .env

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'  # SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

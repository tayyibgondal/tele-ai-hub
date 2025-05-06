import os
from dotenv import load_dotenv

load_dotenv('../.env')  # load .env

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Use PostgreSQL in production (Vercel) or SQLite in development
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # For PostgreSQL on Vercel
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # For local development with SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
 
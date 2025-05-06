import sqlite3
import os

# Path to the SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'site.db')

def add_notification_privacy_columns():
    """Add notification and privacy setting columns to the user table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if the database and user table exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if not cursor.fetchone():
        print("User table doesn't exist. Please run the application first to initialize the database.")
        conn.close()
        return False
    
    # Get existing columns to avoid adding duplicates
    cursor.execute('PRAGMA table_info(user)')
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Add notification columns if they don't exist
    notification_columns = [
        ("email_notifications", "BOOLEAN DEFAULT 1"),
        ("product_updates", "BOOLEAN DEFAULT 1"),
        ("security_alerts", "BOOLEAN DEFAULT 1"),
        ("marketing_comms", "BOOLEAN DEFAULT 0")
    ]
    
    for col_name, col_type in notification_columns:
        if col_name not in existing_columns:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
    
    # Add privacy columns if they don't exist
    privacy_columns = [
        ("allow_analytics", "BOOLEAN DEFAULT 1"),
        ("show_profile", "BOOLEAN DEFAULT 0"),
        ("two_factor_auth", "BOOLEAN DEFAULT 0")
    ]
    
    for col_name, col_type in privacy_columns:
        if col_name not in existing_columns:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Database migration completed successfully!")
    return True

if __name__ == "__main__":
    add_notification_privacy_columns() 
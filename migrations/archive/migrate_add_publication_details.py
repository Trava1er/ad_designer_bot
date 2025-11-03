"""
Migration script to add publication detail columns to ads table.
Run this once to update the database schema.
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "bot.db"

def migrate():
    """Add new columns to ads table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(ads)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'channel_id' not in columns:
            print("Adding channel_id column...")
            cursor.execute("ALTER TABLE ads ADD COLUMN channel_id VARCHAR(255)")
            
        if 'post_link' not in columns:
            print("Adding post_link column...")
            cursor.execute("ALTER TABLE ads ADD COLUMN post_link TEXT")
            
        if 'amount_paid' not in columns:
            print("Adding amount_paid column...")
            cursor.execute("ALTER TABLE ads ADD COLUMN amount_paid DECIMAL(10, 2)")
            
        if 'placement_duration' not in columns:
            print("Adding placement_duration column...")
            cursor.execute("ALTER TABLE ads ADD COLUMN placement_duration VARCHAR(100)")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

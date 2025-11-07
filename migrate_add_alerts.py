#!/usr/bin/env python3
"""
Database migration to add alerts table
Run this script to add the alerts functionality to existing databases
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import text
from app.core.database import engine
from app.models.models import Base

def migrate_add_alerts():
    """Add alerts table to the database"""
    
    with engine.connect() as conn:
        # Create alerts table
        create_alerts_table = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            alert_type VARCHAR(50) DEFAULT 'GENERAL' NOT NULL,
            is_enabled VARCHAR(20) DEFAULT 'enabled' NOT NULL,
            is_read VARCHAR(20) DEFAULT 'unread' NOT NULL,
            expires_at TIMESTAMP NULL,
            post_id INTEGER NULL,
            college_id INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (post_id) REFERENCES posts (id),
            FOREIGN KEY (college_id) REFERENCES colleges (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        );
        """
        
        # Create indexes for better performance
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_college_id ON alerts(college_id);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_is_read ON alerts(is_read);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_is_enabled ON alerts(is_enabled);",
            "CREATE INDEX IF NOT EXISTS idx_alerts_expires_at ON alerts(expires_at);"
        ]
        
        try:
            # Execute table creation
            conn.execute(text(create_alerts_table))
            print("✅ Created alerts table")
            
            # Execute index creation
            for index_sql in create_indexes:
                conn.execute(text(index_sql))
            print("✅ Created alerts table indexes")
            
            # Commit transaction
            conn.commit()
            
            print("\n🎉 Alerts migration completed successfully!")
            print("\nNew endpoints available:")
            print("  GET    /alerts              - Get user's alerts")
            print("  POST   /alerts              - Create new alert")
            print("  PUT    /alerts/{id}         - Update alert (enable/disable/mark read)")
            print("  DELETE /alerts/{id}         - Delete alert")
            print("  POST   /alerts/mark-all-read - Mark all alerts as read")
            print("  GET    /alerts/unread-count - Get unread alerts count")
            print("  POST   /posts/{id}/alert    - Create alert for specific post")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("Starting alerts migration...")
    migrate_add_alerts()
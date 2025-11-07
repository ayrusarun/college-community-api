from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import SessionLocal, engine

def add_events_to_enum():
    """Add EVENTS to the PostType enum in the database"""
    
    db = SessionLocal()
    
    try:
        # Add the new enum value to the existing enum type
        db.execute(text("ALTER TYPE posttype ADD VALUE 'EVENTS'"))
        db.commit()
        print("✅ Successfully added EVENTS to PostType enum")
        
    except Exception as e:
        print(f"Error updating enum: {e}")
        # If enum already has EVENTS or other error, continue
        db.rollback()
    
    db.close()

if __name__ == "__main__":
    add_events_to_enum()
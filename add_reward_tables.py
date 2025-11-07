from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, RewardPoint, User

def add_reward_tables():
    """Add reward tables to existing database"""
    
    # Create new tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Initialize reward points for existing users
    existing_users = db.query(User).all()
    
    for user in existing_users:
        # Check if user already has reward points record
        existing_points = db.query(RewardPoint).filter(
            RewardPoint.user_id == user.id
        ).first()
        
        if not existing_points:
            # Create initial reward points record
            reward_points = RewardPoint(
                user_id=user.id,
                total_points=0
            )
            db.add(reward_points)
    
    db.commit()
    print(f"Initialized reward points for {len(existing_users)} users!")
    db.close()

if __name__ == "__main__":
    add_reward_tables()
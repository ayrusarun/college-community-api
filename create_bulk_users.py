from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal, engine
from app.models.models import Base, College, User, Post, PostType, RewardPoint
from app.core.security import get_password_hash
import random


def create_bulk_users():
    """Create 50+ sample users across multiple colleges"""
    
    db = SessionLocal()
    
    # Get existing colleges
    colleges = db.query(College).all()
    if not colleges:
        print("No colleges found. Please run init_db.py first!")
        return
    
    # Sample data for generating users
    first_names = [
        "Alex", "Blake", "Casey", "Dana", "Eli", "Fran", "Grace", "Henry", "Ivy", "Jack",
        "Katie", "Leo", "Maya", "Noah", "Olivia", "Parker", "Quinn", "Riley", "Sam", "Taylor",
        "Uma", "Victor", "Willow", "Xavier", "Yara", "Zoe", "Aaron", "Bella", "Chris", "Diana",
        "Emma", "Felix", "Gina", "Hugo", "Iris", "Jason", "Kira", "Liam", "Mia", "Nathan",
        "Orion", "Piper", "Quincy", "Ruby", "Sean", "Tina", "Ulysses", "Vera", "Wade", "Xara",
        "Yvonne", "Zach", "Ava", "Ben", "Cleo", "Diego", "Eva", "Finn"
    ]
    
    last_names = [
        "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris", "Johnson", "King",
        "Lee", "Miller", "Nelson", "O'Connor", "Parker", "Quinn", "Roberts", "Smith", "Taylor", "Wilson",
        "Adams", "Baker", "Cooper", "Dixon", "Edwards", "Foster", "Green", "Hill", "Jackson", "Kelly",
        "Lewis", "Moore", "Newton", "Oliver", "Peterson", "Robinson", "Stewart", "Thomas", "Turner", "White"
    ]
    
    departments = [
        "Computer Science", "Electrical Engineering", "Mechanical Engineering", "Business Administration",
        "Mathematics", "Physics", "Chemistry", "Biology", "Psychology", "English Literature",
        "Economics", "Political Science", "History", "Art & Design", "Music", "Philosophy",
        "Sociology", "Anthropology", "Environmental Science", "Data Science", "Biomedical Engineering",
        "Civil Engineering", "Architecture", "Communications", "Marketing"
    ]
    
    class_names = ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"]
    academic_years = ["2024-2025", "2025-2026", "2026-2027", "2027-2028"]
    
    # Generate users for each college
    total_users_created = 0
    
    for college in colleges:
        # Create 25-30 users per college
        users_per_college = random.randint(25, 30)
        
        print(f"\nCreating {users_per_college} users for {college.name}...")
        
        for i in range(users_per_college):
            # Generate user data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            username = f"{first_name.lower()}_{last_name.lower()}_{i+1}"
            
            # Make sure username is unique
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                username = f"{username}_{college.slug}"
            
            email_domain = college.slug + ".edu" if college.slug in ["stanford", "mit"] else f"{college.slug}.edu"
            email = f"{first_name.lower()}.{last_name.lower()}@{email_domain}"
            
            # Create user
            new_user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash("password123"),  # Same password for all
                full_name=full_name,
                department=random.choice(departments),
                class_name=random.choice(class_names),
                academic_year=random.choice(academic_years),
                college_id=college.id
            )
            
            db.add(new_user)
            total_users_created += 1
        
        # Commit users for this college
        db.commit()
        print(f"✓ Created {users_per_college} users for {college.name}")
    
    # Initialize reward points for all new users
    print("\nInitializing reward points for all users...")
    all_users = db.query(User).all()
    
    for user in all_users:
        existing_points = db.query(RewardPoint).filter(RewardPoint.user_id == user.id).first()
        if not existing_points:
            # Give some users random initial points for testing
            initial_points = random.randint(0, 50) if random.random() < 0.3 else 0
            reward_point = RewardPoint(
                user_id=user.id,
                total_points=initial_points
            )
            db.add(reward_point)
    
    db.commit()
    
    # Create some sample posts from random users
    print("\nCreating sample posts from new users...")
    
    post_titles = [
        "Study Tips for Finals Week",
        "Great Resources for Data Structures",
        "Looking for Project Partners",
        "Campus Event This Friday",
        "Internship Opportunities Available",
        "Tutoring Sessions Available",
        "Research Project Showcase",
        "Study Group Formation",
        "Career Fair Next Month",
        "Programming Contest Registration",
        "Academic Workshop Series",
        "Student Organization Meeting",
        "Lab Equipment Training",
        "Guest Lecture Series",
        "Scholarship Opportunities"
    ]
    
    post_contents = [
        "Here are some effective study strategies that have helped me during finals week. Feel free to share your own tips!",
        "I found these online resources really helpful for understanding algorithms and data structures. Check them out!",
        "Looking for motivated team members for a machine learning project. Anyone interested?",
        "Don't miss the tech talk happening this Friday in the main auditorium. Free pizza included!",
        "Several companies are offering internship positions for next summer. Let me know if you want more details.",
        "Offering free tutoring sessions for calculus and linear algebra. Message me to schedule!",
        "Excited to present my research project next week. It's about sustainable energy solutions.",
        "Starting a study group for advanced algorithms. We'll meet twice a week in the library.",
        "Mark your calendars! The annual career fair is coming up next month with 50+ companies.",
        "Registration is now open for the inter-university programming contest. Team up and compete!",
        "Join our academic workshop series covering various topics from research methodology to presentation skills.",
        "Monthly meeting of the Computer Science Student Organization this Thursday at 6 PM.",
        "Training session for new lab equipment available next week. Sign up at the front desk.",
        "We have an amazing guest lecture series lined up with industry experts and researchers.",
        "Multiple scholarship opportunities available for undergraduate and graduate students."
    ]
    
    # Get random users from different colleges
    random_users = db.query(User).order_by(func.random()).limit(20).all()
    
    for i, user in enumerate(random_users):
        if i < len(post_titles):
            post = Post(
                title=post_titles[i],
                content=post_contents[i],
                post_type=random.choice(list(PostType)),
                author_id=user.id,
                college_id=user.college_id,
                post_metadata={
                    "likes": random.randint(0, 25),
                    "comments": random.randint(0, 10),
                    "shares": random.randint(0, 5)
                }
            )
            db.add(post)
    
    db.commit()
    
    # Print summary
    print(f"\n{'='*50}")
    print("BULK USER CREATION COMPLETED!")
    print(f"{'='*50}")
    print(f"✅ Total users created: {total_users_created}")
    print(f"✅ Sample posts created: {min(len(random_users), len(post_titles))}")
    print(f"✅ Reward points initialized for all users")
    
    # Show breakdown by college
    print(f"\nUsers by College:")
    for college in colleges:
        user_count = db.query(User).filter(User.college_id == college.id).count()
        print(f"📚 {college.name}: {user_count} users")
    
    print(f"\nAll users have the same password: password123")
    print(f"You can now test the reward system with many users!")
    print(f"\nSample usernames to try:")
    
    # Show some sample usernames
    sample_users = db.query(User).limit(10).all()
    for user in sample_users[:5]:
        print(f"   - {user.username} ({user.college.name})")
    
    db.close()


if __name__ == "__main__":
    create_bulk_users()
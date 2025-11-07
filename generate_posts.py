import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, College, User, Post, PostType
from app.core.security import get_password_hash


# Sample post content for different categories
POST_TEMPLATES = {
    "IMPORTANT": [
        {
            "title": "Campus Safety Alert",
            "content": "Please be aware that there will be maintenance work on the main library from 8 PM to 6 AM tonight. Emergency exits will remain accessible."
        },
        {
            "title": "Important: Graduation 2025 Registration",
            "content": "Registration for Graduation 2025 is now open! Your journey to success starts here. Connect, learn, and grow with your campus community."
        },
        {
            "title": "Emergency Weather Alert",
            "content": "Severe weather warning in effect. All outdoor activities cancelled. Please stay indoors until further notice."
        },
        {
            "title": "Campus Closure Notice",
            "content": "Due to unforeseen circumstances, the campus will be closed tomorrow. All classes will be conducted online."
        },
        {
            "title": "Security Alert",
            "content": "Please be vigilant and report any suspicious activity to campus security immediately. Your safety is our priority."
        },
    ],
    "ANNOUNCEMENT": [
        {
            "title": "Study Group Formation",
            "content": "Looking to form a study group for Advanced Algorithms. We'll meet twice a week and work through problem sets together. DM me if interested!"
        },
        {
            "title": "Hackathon 2025 Registration Open",
            "content": "Join us for the biggest hackathon of the year! 48 hours of coding, innovation, and amazing prizes. Register now!"
        },
        {
            "title": "Career Fair Next Week",
            "content": "Top tech companies will be on campus next week. Don't miss this opportunity to network and land your dream internship!"
        },
        {
            "title": "Guest Lecture: AI in Healthcare",
            "content": "Dr. Sarah Chen from MIT will be giving a guest lecture on AI applications in healthcare. Room 301, 3 PM tomorrow."
        },
        {
            "title": "Club Meeting Tonight",
            "content": "Computer Science Club meeting tonight at 7 PM in the student center. Pizza will be provided! Discussing upcoming projects."
        },
        {
            "title": "Workshop: Python for Data Science",
            "content": "Free workshop on using Python for data analysis. Beginners welcome! Saturday 2-5 PM at the tech lab."
        },
        {
            "title": "Volunteer Opportunity",
            "content": "Help teach coding to local high school students. Looking for volunteers every Saturday morning. Great for your resume!"
        },
    ],
    "INFO": [
        {
            "title": "Library Hours Extended",
            "content": "Good news! The library will now be open until midnight on weekdays. Perfect for late-night study sessions!"
        },
        {
            "title": "New Coffee Shop Opens on Campus",
            "content": "A new artisan coffee shop just opened in the student union. They have amazing pastries and great study spots!"
        },
        {
            "title": "Gym Schedule Update",
            "content": "The campus gym will have extended hours during finals week. Stay healthy while studying hard!"
        },
        {
            "title": "Free Tutoring Services",
            "content": "Did you know we offer free tutoring for math, physics, and CS courses? Check out the academic support center."
        },
        {
            "title": "Campus WiFi Upgrade Complete",
            "content": "The WiFi infrastructure upgrade is complete! You should notice faster speeds across campus now."
        },
    ],
    "GENERAL": [
        {
            "title": "Machine Learning Project Showcase",
            "content": "Just finished my final project on machine learning! So excited to present it next week. Thanks to everyone who helped along the way! 🎓"
        },
        {
            "title": "Best Study Spots on Campus",
            "content": "After 3 years here, I've found the best quiet study spots. The third floor of the engineering building is amazing! 📚"
        },
        {
            "title": "Looking for Research Partners",
            "content": "Working on a computer vision project for my thesis. Looking for partners interested in deep learning and image processing."
        },
        {
            "title": "Recommend Good CS Electives?",
            "content": "Need to pick electives for next semester. Any recommendations for interesting CS courses? Interested in AI and web development."
        },
        {
            "title": "Just Aced My Algorithms Exam!",
            "content": "All those late nights studying finally paid off! Dynamic programming makes sense now 🎉"
        },
        {
            "title": "Anyone Want to Form a Running Group?",
            "content": "Looking to stay active this semester. Anyone interested in morning runs around campus? All fitness levels welcome!"
        },
        {
            "title": "Internship Offer!",
            "content": "Just got an internship offer at a top tech company! So grateful for the career center's help with interview prep."
        },
        {
            "title": "Photography Club Outing",
            "content": "Had an amazing time at the photography club outing this weekend. Captured some stunning shots of the campus at sunset! 📸"
        },
        {
            "title": "New Coding Bootcamp Experience",
            "content": "Just completed an intensive coding bootcamp. Learned so much about full-stack development in just 12 weeks!"
        },
        {
            "title": "Game Night This Friday",
            "content": "Organizing a board game night in the common room this Friday. Bring your favorite games and snacks! 🎲"
        },
        {
            "title": "Lost and Found",
            "content": "Found a blue backpack near the library yesterday. If it's yours, contact me with a description of the contents."
        },
        {
            "title": "Concert Tickets Available",
            "content": "Have 2 extra tickets to the concert next weekend. Selling at face value. Message me if interested!"
        },
        {
            "title": "Collaborative Research Project",
            "content": "Starting a research project on sustainable energy solutions. Looking for team members from engineering and environmental science."
        },
        {
            "title": "Mental Health Check-In",
            "content": "Remember to take care of your mental health during finals season. The counseling center is here to help! 💚"
        },
        {
            "title": "Part-Time Job Opening",
            "content": "The campus bookstore is hiring part-time. Flexible hours that work around class schedules. Apply at the student employment office."
        },
    ]
}

# Sample image URLs from Unsplash
IMAGE_URLS = [
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=500",
    "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=500",
    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",
    "https://images.unsplash.com/photo-1498243691581-b145c3f54a5a?w=500",
    "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=500",
    "https://images.unsplash.com/photo-1523580494863-6f3031224c94?w=500",
    "https://images.unsplash.com/photo-1517842645767-c639042777db?w=500",
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=500",
    "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=500",
    "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=500",
    "https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=500",
    "https://images.unsplash.com/photo-1513258496099-48168024aec0?w=500",
    "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=500",
    "https://images.unsplash.com/photo-1496016943515-7d33598c11e6?w=500",
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=500",
]


def generate_posts(db: Session):
    """Generate 50+ random posts with various types and engagement"""
    
    # Get all users and colleges
    users = db.query(User).all()
    colleges = db.query(College).all()
    
    if not users or not colleges:
        print("Please run init_db.py first to create users and colleges!")
        return
    
    print(f"Generating posts for {len(users)} users across {len(colleges)} colleges...")
    
    posts_created = 0
    
    # Generate posts for each post type
    for post_type in ["IMPORTANT", "ANNOUNCEMENT", "INFO", "GENERAL"]:
        templates = POST_TEMPLATES[post_type]
        
        # Determine how many posts to create for this type
        if post_type == "GENERAL":
            num_posts = 30  # Most posts should be general
        elif post_type == "ANNOUNCEMENT":
            num_posts = 15
        elif post_type == "INFO":
            num_posts = 10
        else:  # IMPORTANT
            num_posts = 5
        
        for i in range(num_posts):
            # Pick a random template
            template = random.choice(templates)
            
            # Pick a random user and their college
            user = random.choice(users)
            
            # Randomly decide if post should have an image (70% chance)
            image_url = random.choice(IMAGE_URLS) if random.random() < 0.7 else None
            
            # Generate random engagement metrics based on post type and age
            days_ago = random.randint(0, 30)
            created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Important posts get more engagement
            if post_type == "IMPORTANT":
                likes = random.randint(20, 100)
                comments = random.randint(5, 30)
                shares = random.randint(10, 50)
            elif post_type == "ANNOUNCEMENT":
                likes = random.randint(10, 50)
                comments = random.randint(3, 20)
                shares = random.randint(5, 25)
            elif post_type == "INFO":
                likes = random.randint(5, 30)
                comments = random.randint(1, 15)
                shares = random.randint(2, 15)
            else:  # GENERAL
                likes = random.randint(0, 40)
                comments = random.randint(0, 20)
                shares = random.randint(0, 10)
            
            # Newer posts get less engagement
            if days_ago < 1:
                likes = int(likes * 0.3)
                comments = int(comments * 0.3)
                shares = int(shares * 0.3)
            elif days_ago < 7:
                likes = int(likes * 0.7)
                comments = int(comments * 0.7)
                shares = int(shares * 0.7)
            
            # Create the post
            post = Post(
                title=template["title"],
                content=template["content"],
                image_url=image_url,
                post_type=getattr(PostType, post_type),
                author_id=user.id,
                college_id=user.college_id,
                post_metadata={
                    "likes": likes,
                    "comments": comments,
                    "shares": shares
                },
                created_at=created_at,
                updated_at=created_at
            )
            
            db.add(post)
            posts_created += 1
    
    db.commit()
    print(f"✅ Successfully created {posts_created} posts!")
    
    # Print summary
    for post_type in ["IMPORTANT", "ANNOUNCEMENT", "INFO", "GENERAL"]:
        count = db.query(Post).filter(Post.post_type == getattr(PostType, post_type)).count()
        print(f"   - {post_type}: {count} posts")
    
    print(f"\n📊 Total posts in database: {db.query(Post).count()}")


def main():
    """Main function to generate posts"""
    db = SessionLocal()
    
    try:
        # Ask user if they want to clear existing posts
        print("🚀 Post Generator")
        print("=" * 50)
        
        existing_posts = db.query(Post).count()
        if existing_posts > 0:
            print(f"⚠️  Found {existing_posts} existing posts in database.")
            response = input("Do you want to delete existing posts? (yes/no): ").lower()
            if response == 'yes':
                db.query(Post).delete()
                db.commit()
                print("✅ Existing posts deleted.")
        
        print("\n🎲 Generating random posts...")
        generate_posts(db)
        
        print("\n✨ Done! You can now test the API with 50+ posts.")
        print("\n📝 Sample API call:")
        print("curl -X GET 'http://localhost:8000/posts/?limit=20' -H 'Authorization: Bearer YOUR_TOKEN'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

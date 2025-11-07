from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.core.database import SessionLocal, engine
from app.models.models import Base, College, User, Post, PostType, RewardPoint, Reward
from app.core.security import get_password_hash
import random


def clean_db():
    """Clean all existing data"""
    db = SessionLocal()
    
    # Delete all existing data in reverse order of dependencies
    # First delete files (they reference users)
    db.execute(text("DELETE FROM files"))
    # Then delete rewards (they reference users)
    db.execute(text("DELETE FROM rewards"))
    db.execute(text("DELETE FROM reward_points"))
    db.execute(text("DELETE FROM posts"))
    db.execute(text("DELETE FROM users"))
    db.execute(text("DELETE FROM colleges"))
    
    db.commit()
    db.close()
    print("🗑️ Database cleaned successfully!")


def init_db():
    # Clean existing data first
    clean_db()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Create South Indian colleges
    colleges_data = [
        {"name": "Indian Institute of Technology Madras", "slug": "iit-madras"},
        {"name": "Indian Institute of Science Bangalore", "slug": "iisc-bangalore"},
        {"name": "National Institute of Technology Tiruchirappalli", "slug": "nit-trichy"},
        {"name": "Anna University Chennai", "slug": "anna-university"},
        {"name": "University of Mysore", "slug": "mysore-university"},
        {"name": "Cochin University of Science and Technology", "slug": "cusat"},
        {"name": "Vellore Institute of Technology", "slug": "vit-vellore"},
        {"name": "Amrita Vishwa Vidyapeetham", "slug": "amrita-university"}
    ]
    
    colleges = []
    for college_data in colleges_data:
        college = College(name=college_data["name"], slug=college_data["slug"])
        db.add(college)
        colleges.append(college)
    
    db.commit()
    
    # Refresh to get IDs
    for college in colleges:
        db.refresh(college)
    
    print(f"✅ Created {len(colleges)} Indian colleges")
    
    # South Indian names data
    first_names = [
        # Male names (Tamil, Telugu, Kannada, Malayalam)
        "Arjun", "Krishna", "Vishnu", "Sai", "Arun", "Karthik", "Ravi", "Suresh", "Ganesh", "Mahesh",
        "Rajesh", "Ramesh", "Venkat", "Pradeep", "Santosh", "Anand", "Ashwin", "Naveen", "Deepak", "Vijay",
        "Srinivas", "Sudheer", "Harish", "Kishore", "Mohan", "Gopal", "Madhav", "Narayan", "Shankar", "Bhaskar",
        
        # Female names (Tamil, Telugu, Kannada, Malayalam)
        "Priya", "Kavya", "Divya", "Meera", "Lakshmi", "Devi", "Sita", "Geetha", "Radha", "Anjali",
        "Sowmya", "Bhavya", "Shreya", "Pooja", "Deepika", "Sneha", "Swathi", "Nandini", "Sangeetha", "Vidya",
        "Radhika", "Lavanya", "Pavitra", "Sushma", "Rekha", "Shobha", "Usha", "Vani", "Yamuna", "Indira"
    ]
    
    last_names = [
        # Tamil surnames
        "Kumar", "Raman", "Krishnan", "Murugan", "Selvam", "Raj", "Babu", "Durai", "Vel", "Mani",
        # Telugu surnames  
        "Reddy", "Rao", "Raju", "Prasad", "Murthy", "Naidu", "Chandra", "Varma", "Sastry", "Goud",
        # Kannada surnames
        "Gowda", "Shetty", "Hegde", "Nayak", "Rai", "Bhat", "Acharya", "Sharma", "Kamath", "Kulkarni",
        # Malayalam surnames
        "Nair", "Menon", "Pillai", "Panicker", "Kurup", "Warrier", "Iyer", "Namboothiri", "Das", "Thampi",
        # Common South Indian surnames
        "Subramanian", "Venkatesh", "Mahadevan", "Raghavan", "Srinivasan", "Natarajan", "Ramakrishnan", "Gopalan"
    ]
    
    departments = [
        "Computer Science & Engineering", "Electronics & Communication", "Mechanical Engineering",
        "Civil Engineering", "Electrical Engineering", "Chemical Engineering", "Biotechnology",
        "Information Technology", "Aerospace Engineering", "Metallurgical Engineering",
        "Mathematics", "Physics", "Chemistry", "Biology", "Economics", "Business Administration",
        "Management Studies", "Liberal Arts", "Design", "Architecture"
    ]
    
    class_names = ["First Year", "Second Year", "Third Year", "Final Year", "M.Tech", "PhD"]
    academic_years = ["2024-25", "2025-26", "2026-27", "2027-28", "2028-29"]
    
    # Create hardcoded users for consistent testing
    total_users = 0
    all_users = []
    
    # Hardcoded users for IIT Madras (first college) with specific departments
    iit_madras = colleges[0]  # First college is IIT Madras
    print(f"Creating hardcoded users for {iit_madras.name}")
    
    # Define hardcoded users with specific departments for file upload testing
    hardcoded_users = [
        {
            "username": "arjun_cs",
            "email": "arjun.kumar@iitm.ac.in",
            "full_name": "Arjun Kumar",
            "department": "Computer Science & Engineering",
            "class_name": "Final Year",
            "academic_year": "2024-25"
        },
        {
            "username": "priya_me",
            "email": "priya.reddy@iitm.ac.in", 
            "full_name": "Priya Reddy",
            "department": "Mechanical Engineering",
            "class_name": "Third Year",
            "academic_year": "2025-26"
        },
        {
            "username": "krishna_ece",
            "email": "krishna.nair@iitm.ac.in",
            "full_name": "Krishna Nair",
            "department": "Electronics & Communication",
            "class_name": "Final Year", 
            "academic_year": "2024-25"
        },
        {
            "username": "vishnu_ce",
            "email": "vishnu.sharma@iitm.ac.in",
            "full_name": "Vishnu Sharma", 
            "department": "Civil Engineering",
            "class_name": "Second Year",
            "academic_year": "2026-27"
        },
        {
            "username": "sai_ee",
            "email": "sai.rao@iitm.ac.in",
            "full_name": "Sai Rao",
            "department": "Electrical Engineering", 
            "class_name": "Final Year",
            "academic_year": "2024-25"
        },
        {
            "username": "arun_ch",
            "email": "arun.pillai@iitm.ac.in",
            "full_name": "Arun Pillai",
            "department": "Chemical Engineering",
            "class_name": "M.Tech",
            "academic_year": "2025-26"
        },
        {
            "username": "kavya_bt", 
            "email": "kavya.menon@iitm.ac.in",
            "full_name": "Kavya Menon",
            "department": "Biotechnology",
            "class_name": "Third Year",
            "academic_year": "2025-26"
        },
        {
            "username": "divya_it",
            "email": "divya.gowda@iitm.ac.in", 
            "full_name": "Divya Gowda",
            "department": "Information Technology",
            "class_name": "Final Year",
            "academic_year": "2024-25"
        },
        {
            "username": "ravi_ae",
            "email": "ravi.shetty@iitm.ac.in",
            "full_name": "Ravi Shetty", 
            "department": "Aerospace Engineering",
            "class_name": "Second Year",
            "academic_year": "2026-27"
        },
        {
            "username": "meera_math",
            "email": "meera.iyer@iitm.ac.in",
            "full_name": "Meera Iyer",
            "department": "Mathematics",
            "class_name": "PhD",
            "academic_year": "2024-25"
        }
    ]
    
    # Create the hardcoded users
    for user_data in hardcoded_users:
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=get_password_hash("password123"),
            full_name=user_data["full_name"],
            department=user_data["department"],
            class_name=user_data["class_name"],
            academic_year=user_data["academic_year"],
            college_id=iit_madras.id
        )
        
        db.add(user)
        all_users.append(user)
        total_users += 1
    
    # Create additional users for other colleges (fewer, simpler)
    for college in colleges[1:]:  # Skip IIT Madras (already done)
        print(f"Creating 3 users for {college.name}")
        
        college_short = {
            "iisc-bangalore": "iisc", 
            "nit-trichy": "nitt",
            "anna-university": "au",
            "mysore-university": "uom",
            "cusat": "cusat",
            "vit-vellore": "vit",
            "amrita-university": "amrita"
        }.get(college.slug, college.slug[:4])
        
        # Create 3 users per other college
        simple_users = [
            {"name": "Student One", "dept": "Computer Science & Engineering"},
            {"name": "Student Two", "dept": "Mechanical Engineering"},  
            {"name": "Student Three", "dept": "Electrical Engineering"}
        ]
        
        for i, user_info in enumerate(simple_users, 1):
            username = f"student{i}_{college_short}"
            first_name = user_info["name"].split()[0].lower()
            last_name = user_info["name"].split()[1].lower()
            
            # Create email based on college
            if college.slug == "iisc-bangalore":
                domain = "iisc.ac.in"
            elif college.slug == "nit-trichy":
                domain = "nitt.edu"
            elif college.slug == "anna-university":
                domain = "annauniv.edu"
            elif college.slug == "vit-vellore":
                domain = "vit.ac.in"
            elif college.slug == "amrita-university":
                domain = "amrita.edu"
            else:
                domain = f"{college.slug.replace('-', '')}.edu.in"
            
            email = f"{first_name}.{last_name}@{domain}"
            
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=user_info["name"],
                department=user_info["dept"],
                class_name=random.choice(class_names),
                academic_year=random.choice(academic_years),
                college_id=college.id
            )
            
            db.add(user)
            all_users.append(user)
            total_users += 1
    
    db.commit()
    
    # Refresh all users to get their IDs
    for user in all_users:
        db.refresh(user)
    
    # Initialize reward points for all users
    for user in all_users:
        initial_points = random.randint(0, 100) if random.random() < 0.4 else 0
        reward_point = RewardPoint(
            user_id=user.id,
            total_points=initial_points
        )
        db.add(reward_point)
    
    db.commit()
    print(f"✅ Created {total_users} Indian users with reward points")
    
    # Create sample posts with South Indian context
    south_indian_post_data = [
        {
            "title": "JEE Advanced Preparation Tips for Tamil Nadu Students",
            "content": "Sharing effective strategies for JEE Advanced preparation. Focus on Tamil Nadu board syllabus alignment. Practice previous year papers regularly! வாழ்த்துக்கள்! 📚",
            "type": PostType.INFO,
            "image": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=500"
        },
        {
            "title": "முக்கியம்: Semester End Examination Schedule",
            "content": "The semester end examinations will commence from 15th December 2024. Please check the detailed timetable on the college website. All the best! 🎓",
            "type": PostType.IMPORTANT,
            "image": "https://images.unsplash.com/photo-1606092195730-5d7b9af1efc5?w=500"
        },
        {
            "title": "Shaastra 2024 - IIT Madras Tech Festival",
            "content": "Our annual technical festival Shaastra is here! Participate in coding competitions, robotics, and innovation challenges. Register before 30th November.",
            "type": PostType.ANNOUNCEMENT,
            "image": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=500"
        },
        {
            "title": "Data Structures Study Group - Telugu Medium",
            "content": "Looking to form a study group for Data Structures and Algorithms. We'll solve competitive programming problems together. Telugu explanation available! దయచేసి చేరండి!",
            "type": PostType.GENERAL,
            "image": None
        },
        {
            "title": "Internship Opportunity at Bangalore Tech Hub",
            "content": "Leading startups in Electronic City, Bangalore are offering summer internships for CS students. Great learning opportunity with stipend of ₹20,000/month!",
            "type": PostType.INFO,
            "image": "https://images.unsplash.com/photo-1556761175-b413da4baf72?w=500"
        },
        {
            "title": "Carnatic Music Concert - Thyagaraja Aradhana",
            "content": "Join us for a divine evening of Carnatic music this Friday at 7 PM in the main auditorium. Featuring renowned artists from Chennai and Mysore. ♪",
            "type": PostType.ANNOUNCEMENT,
            "image": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500"
        },
        {
            "title": "Research Paper Published in IEEE - AI for Agriculture",
            "content": "Excited to share that our research on 'AI for Paddy Crop Management' has been accepted in IEEE Conference! Special thanks to farmers in Thanjavur. 🎉",
            "type": PostType.GENERAL,
            "image": "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=500"
        },
        {
            "title": "Hostel Mess Menu - More South Indian Delicacies",
            "content": "New menu includes Chettinad chicken, Hyderabadi biryani, Kerala fish curry, and Karnataka rasam. Daily dosa and idli counter! ధన్యవాదాలు to mess committee.",
            "type": PostType.INFO,
            "image": None
        },
        {
            "title": "Campus Placement Drive - IT Giants Visit",
            "content": "Major IT companies including TCS Chennai, Infosys Mysore, and Wipro Bangalore visiting for placements. Final year students prepare well! Best of luck! 💼",
            "type": PostType.IMPORTANT,
            "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500"
        },
        {
            "title": "Trek to Nilgiri Hills - Ooty Adventure",
            "content": "Adventure club organizing a trek to beautiful Nilgiri mountains this weekend. Visit tea plantations and enjoy the cool weather! Registration open.",
            "type": PostType.EVENTS,
            "image": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=500"
        },
        {
            "title": "Annual Sports Meet - South Zone Championship",
            "content": "Biggest sporting event of the year! Inter-college competitions with teams from Tamil Nadu, Karnataka, Andhra Pradesh and Kerala. Prizes worth ₹1,00,000! 🏆",
            "type": PostType.EVENTS,
            "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500"
        },
        {
            "title": "HackFest Bangalore 2024 - Code for Bharat",
            "content": "48-hour hackathon focusing on Indian solutions! Build apps for local languages, agriculture, and rural development. Form teams of 3-4 members.",
            "type": PostType.EVENTS,
            "image": "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=500"
        }
    ]
    
    # Create posts from random users
    for i, post_data in enumerate(south_indian_post_data):
        if i < len(all_users):
            author = all_users[i % len(all_users)]
            
            post = Post(
                title=post_data["title"],
                content=post_data["content"],
                image_url=post_data["image"],
                post_type=post_data["type"],
                author_id=author.id,
                college_id=author.college_id,
                post_metadata={
                    "likes": random.randint(5, 50),
                    "comments": random.randint(0, 15),
                    "shares": random.randint(0, 8)
                }
            )
            db.add(post)
    
    db.commit()
    print(f"✅ Created {len(south_indian_post_data)} sample posts")
    
    # Print summary
    print(f"\n{'='*60}")
    print("�️ SOUTH INDIAN COLLEGE COMMUNITY DATABASE INITIALIZED! �️")
    print(f"{'='*60}")
    print(f"✅ Colleges created: {len(colleges)}")
    print(f"✅ Users created: {total_users}")
    print(f"✅ Posts created: {len(south_indian_post_data)}")
    print(f"✅ Reward points initialized for all users")
    
    print(f"\n🏛️ South Indian Colleges:")
    for college in colleges:
        user_count = db.query(User).filter(User.college_id == college.id).count()
        print(f"   • {college.name}: {user_count} students")
    
    print(f"\n👥 Sample Users (Password: password123):")
    sample_users = all_users[:5]
    for user in sample_users:
        college_name = db.query(College).filter(College.id == user.college_id).first().name
        print(f"   • {user.username} - {user.full_name} ({college_name})")
    
    print(f"\n🎯 Features Available:")
    print(f"   • Multi-tenant college system")
    print(f"   • AI-powered content moderation")
    print(f"   • Comprehensive reward system")
    print(f"   • Rich post engagement tracking")
    
    print(f"\n🚀 Ready for testing and Flutter development!")
    
    db.close()


if __name__ == "__main__":
    init_db()
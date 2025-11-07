from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class RewardType(enum.Enum):
    HELPFUL_POST = "HELPFUL_POST"
    ACADEMIC_EXCELLENCE = "ACADEMIC_EXCELLENCE"
    COMMUNITY_PARTICIPATION = "COMMUNITY_PARTICIPATION"
    PEER_RECOGNITION = "PEER_RECOGNITION"
    EVENT_PARTICIPATION = "EVENT_PARTICIPATION"
    MENTORSHIP = "MENTORSHIP"
    LEADERSHIP = "LEADERSHIP"
    OTHER = "OTHER"


class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="college")
    posts = relationship("Post", back_populates="college")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    class_name = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    college = relationship("College", back_populates="users")
    posts = relationship("Post", back_populates="author")
    
    # Reward relationships
    given_rewards = relationship("Reward", foreign_keys="Reward.giver_id", back_populates="giver")
    received_rewards = relationship("Reward", foreign_keys="Reward.receiver_id", back_populates="receiver")
    reward_points = relationship("RewardPoint", back_populates="user")


class PostType(enum.Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    INFO = "INFO"
    IMPORTANT = "IMPORTANT"
    EVENTS = "EVENTS"
    GENERAL = "GENERAL"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)  # New field for image URL
    post_type = Column(Enum(PostType), default=PostType.GENERAL, nullable=False)
    post_metadata = Column(JSON, default=lambda: {"likes": 0, "comments": 0, "shares": 0}, nullable=False)  # Renamed from metadata
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    college = relationship("College", back_populates="posts")


class RewardPoint(Base):
    __tablename__ = "reward_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reward_points")


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    giver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Integer, nullable=False)
    reward_type = Column(Enum(RewardType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # Optional: link to specific post
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    giver = relationship("User", foreign_keys=[giver_id], back_populates="given_rewards")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_rewards")
    post = relationship("Post")
    college = relationship("College")


class FileType(enum.Enum):
    DOCUMENT = "DOCUMENT"  # PDF, DOC, DOCX
    PRESENTATION = "PRESENTATION"  # PPT, PPTX
    SPREADSHEET = "SPREADSHEET"  # XLS, XLSX
    IMAGE = "IMAGE"  # JPG, PNG, GIF
    VIDEO = "VIDEO"  # MP4, AVI, MOV
    AUDIO = "AUDIO"  # MP3, WAV
    ARCHIVE = "ARCHIVE"  # ZIP, RAR
    TEXT = "TEXT"  # TXT, MD
    OTHER = "OTHER"


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_type = Column(Enum(FileType), nullable=False)
    mime_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Categorization
    department = Column(String(100), nullable=False, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False, index=True)
    
    # Upload metadata
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_metadata = Column(JSON, default=lambda: {"downloads": 0, "views": 0}, nullable=False)
    
    # AI indexing
    is_indexed = Column(String(20), default="pending", nullable=False)  # pending, indexed, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    college = relationship("College")
    uploader = relationship("User")


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_docs = Column(JSON, nullable=True)  # Store referenced documents
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User")
    college = relationship("College")


class IndexingTask(Base):
    __tablename__ = "indexing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), nullable=False)  # file, post, college_info
    content_id = Column(Integer, nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    college = relationship("College")
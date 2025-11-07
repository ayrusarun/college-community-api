from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PostType(str, Enum):
    ANNOUNCEMENT = "ANNOUNCEMENT"
    INFO = "INFO"
    IMPORTANT = "IMPORTANT"
    EVENTS = "EVENTS"
    GENERAL = "GENERAL"


class RewardType(str, Enum):
    HELPFUL_POST = "HELPFUL_POST"
    ACADEMIC_EXCELLENCE = "ACADEMIC_EXCELLENCE"
    COMMUNITY_PARTICIPATION = "COMMUNITY_PARTICIPATION"
    PEER_RECOGNITION = "PEER_RECOGNITION"
    EVENT_PARTICIPATION = "EVENT_PARTICIPATION"
    MENTORSHIP = "MENTORSHIP"
    LEADERSHIP = "LEADERSHIP"
    OTHER = "OTHER"


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    department: str
    class_name: str
    academic_year: str


class UserCreate(UserBase):
    password: str
    college_id: int


class UserResponse(UserBase):
    id: int
    college_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    college_name: str
    college_slug: str


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    college_slug: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Post schemas
class PostBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None
    post_type: PostType = PostType.GENERAL


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    post_type: Optional[PostType] = None


class PostResponse(PostBase):
    id: int
    author_id: int
    college_id: int
    post_metadata: Dict[str, Any]  # Contains likes, comments, shares, etc.
    created_at: datetime
    updated_at: datetime
    author_name: str
    author_department: str
    time_ago: str  # Human readable time difference

    class Config:
        from_attributes = True


class PostMetadataUpdate(BaseModel):
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None


# College schemas
class CollegeBase(BaseModel):
    name: str
    slug: str


class CollegeCreate(CollegeBase):
    pass


class CollegeResponse(CollegeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Reward schemas
class RewardBase(BaseModel):
    receiver_id: int
    points: int
    reward_type: RewardType
    title: str
    description: Optional[str] = None
    post_id: Optional[int] = None


class RewardCreate(RewardBase):
    pass


class RewardResponse(RewardBase):
    id: int
    giver_id: int
    college_id: int
    created_at: datetime
    
    # Additional fields for rich responses
    giver_name: str
    receiver_name: str
    giver_department: str
    receiver_department: str
    post_title: Optional[str] = None

    class Config:
        from_attributes = True


class RewardPointsResponse(BaseModel):
    id: int
    user_id: int
    total_points: int
    created_at: datetime
    updated_at: datetime
    
    # User info
    user_name: str
    user_department: str

    class Config:
        from_attributes = True


class RewardLeaderboardResponse(BaseModel):
    user_id: int
    user_name: str
    department: str
    total_points: int
    rank: int


class RewardSummaryResponse(BaseModel):
    total_points: int
    rewards_given: int
    rewards_received: int
    recent_rewards: List[RewardResponse]


# File schemas
class FileType(str, Enum):
    DOCUMENT = "DOCUMENT"
    PRESENTATION = "PRESENTATION"
    SPREADSHEET = "SPREADSHEET"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    ARCHIVE = "ARCHIVE"
    TEXT = "TEXT"
    OTHER = "OTHER"


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: FileType
    mime_type: str
    department: str
    college_id: int
    uploaded_by: int
    upload_metadata: Dict[str, Any]
    created_at: datetime
    
    # Additional fields
    uploader_name: str
    college_name: str

    class Config:
        from_attributes = True


class FileResponse(FileUploadResponse):
    description: Optional[str] = None
    updated_at: datetime


class FileUpdate(BaseModel):
    description: Optional[str] = None


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total_count: int
    page: int
    page_size: int


class FileSearchQuery(BaseModel):
    department: Optional[str] = None
    file_type: Optional[FileType] = None
    search_term: Optional[str] = None
    page: int = 1
    page_size: int = 20


# AI schemas
class AIQuery(BaseModel):
    question: str
    context_filter: Optional[str] = None  # "files", "posts", "all"


class AIResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    conversation_id: int


class IndexRequest(BaseModel):
    content_type: str  # "file", "post", "all"
    content_ids: Optional[List[int]] = None


class IndexResponse(BaseModel):
    message: str
    tasks_created: int


class SearchResult(BaseModel):
    doc_id: str
    similarity: float
    metadata: Dict[str, Any]


class KnowledgeSearchQuery(BaseModel):
    query: str
    content_type: Optional[str] = None  # "file", "post", "college_info"
    limit: int = 5


class ConversationResponse(BaseModel):
    id: int
    query: str
    response: str
    sources_count: int
    created_at: datetime


class AIStatsResponse(BaseModel):
    vector_database: Dict[str, Any]
    indexing: Dict[str, int]
    conversations: Dict[str, int]


# Alert schemas
class AlertType(str, Enum):
    EVENT_NOTIFICATION = "EVENT_NOTIFICATION"
    FEE_REMINDER = "FEE_REMINDER"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    DEADLINE_REMINDER = "DEADLINE_REMINDER"
    ACADEMIC_UPDATE = "ACADEMIC_UPDATE"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"
    GENERAL = "GENERAL"


class AlertBase(BaseModel):
    title: str
    message: str
    alert_type: AlertType = AlertType.GENERAL
    expires_at: Optional[datetime] = None
    post_id: Optional[int] = None


class AlertCreate(AlertBase):
    user_id: int


class AlertUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    alert_type: Optional[AlertType] = None
    is_enabled: Optional[bool] = None  # True=enabled, False=disabled
    is_read: Optional[bool] = None  # True=read, False=unread
    expires_at: Optional[datetime] = None


class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_enabled: bool
    is_read: bool
    college_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    # Additional fields for rich responses
    creator_name: str
    post_title: Optional[str] = None
    time_ago: str  # Human readable time difference
    is_expired: bool  # Calculated field

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total_count: int
    unread_count: int
    page: int
    page_size: int


class PostAlertCreate(BaseModel):
    user_id: int
    title: str
    message: str
    alert_type: AlertType = AlertType.ANNOUNCEMENT
    expires_at: Optional[datetime] = None
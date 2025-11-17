from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    STUDENT = "student"


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
    
    # RBAC fields
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), 
                  default=UserRole.STUDENT, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    college = relationship("College", back_populates="users")
    posts = relationship("Post", back_populates="author")
    
    # Reward relationships
    given_rewards = relationship("Reward", foreign_keys="Reward.giver_id", back_populates="giver")
    received_rewards = relationship("Reward", foreign_keys="Reward.receiver_id", back_populates="receiver")
    reward_points = relationship("RewardPoint", back_populates="user")
    
    # Store relationships
    cart = relationship("Cart", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    point_transactions = relationship("PointTransaction", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user")


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
    
    # Denormalized counters for performance
    like_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    ignite_count = Column(Integer, default=0, nullable=False)
    
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    college = relationship("College", back_populates="posts")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    ignites = relationship("PostIgnite", back_populates="post", cascade="all, delete-orphan")


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
    
    # Folder support
    folder_path = Column(String(1000), default="/", nullable=False, index=True)  # Virtual folder path
    is_folder = Column(Boolean, default=False, nullable=False)  # True if this is a folder entry
    parent_folder_id = Column(Integer, ForeignKey("files.id"), nullable=True)  # For hierarchical structure
    
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
    parent_folder = relationship("File", remote_side=[id], foreign_keys=[parent_folder_id])


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


class AlertType(enum.Enum):
    EVENT_NOTIFICATION = "EVENT_NOTIFICATION"
    FEE_REMINDER = "FEE_REMINDER"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    DEADLINE_REMINDER = "DEADLINE_REMINDER"
    ACADEMIC_UPDATE = "ACADEMIC_UPDATE"
    SYSTEM_NOTIFICATION = "SYSTEM_NOTIFICATION"
    GENERAL = "GENERAL"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(Enum(AlertType), default=AlertType.GENERAL, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)  # True=enabled, False=disabled
    is_read = Column(Boolean, default=False, nullable=False)  # True=read, False=unread
    expires_at = Column(DateTime, nullable=True)  # Optional expiry date
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)  # Optional link to post
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who created the alert
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    post = relationship("Post")
    college = relationship("College")


# ==================== REWARDS STORE MODELS ====================

class ProductCategory(enum.Enum):
    ELECTRONICS = "ELECTRONICS"
    BOOKS = "BOOKS"
    STATIONERY = "STATIONERY"
    APPAREL = "APPAREL"
    FOOD_VOUCHERS = "FOOD_VOUCHERS"
    GIFT_CARDS = "GIFT_CARDS"
    EXPERIENCES = "EXPERIENCES"
    SOFTWARE = "SOFTWARE"
    OTHER = "OTHER"


class ProductStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE" 
    OUT_OF_STOCK = "OUT_OF_STOCK"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ProductCategory), nullable=False)
    points_required = Column(Integer, nullable=False)  # Points needed to redeem
    original_price = Column(Numeric(10, 2), nullable=True)  # Original price for reference
    stock_quantity = Column(Integer, default=0, nullable=False)
    max_quantity_per_user = Column(Integer, default=1, nullable=False)  # Max per user per order
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False)
    image_url = Column(String(500), nullable=True)
    brand = Column(String(100), nullable=True)
    specifications = Column(JSON, nullable=True)  # JSON field for product specs
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    college = relationship("College")
    creator = relationship("User", foreign_keys=[created_by])
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    wishlists = relationship("WishlistItem", back_populates="product")


class OrderStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_points = Column(Integer, nullable=False)
    total_items = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)  # Admin notes or special instructions
    pickup_location = Column(String(255), nullable=True)  # Where to pickup items
    estimated_pickup_date = Column(DateTime, nullable=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    college = relationship("College")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    points_per_item = Column(Integer, nullable=False)  # Points at time of order
    total_points = Column(Integer, nullable=False)  # quantity * points_per_item
    product_name = Column(String(255), nullable=False)  # Store product name at time of order
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="cart")
    college = relationship("College")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)  # "EARNED", "SPENT", "REFUNDED"
    points = Column(Integer, nullable=False)  # Positive for earned, negative for spent
    balance_after = Column(Integer, nullable=False)  # Balance after this transaction
    description = Column(String(500), nullable=False)
    reference_type = Column(String(50), nullable=True)  # "order", "reward", "manual"
    reference_id = Column(Integer, nullable=True)  # Order ID, Reward ID, etc.
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="point_transactions")
    college = relationship("College")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlists")
    college = relationship("College")

    # Ensure unique combination of user and product
    __table_args__ = (
        {"extend_existing": True},
    )


# ==================== RBAC MODELS ====================

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., 'read:posts'
    resource = Column(String(50), nullable=False, index=True)  # e.g., 'posts', 'files'
    action = Column(String(50), nullable=False)  # e.g., 'read', 'write', 'delete'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), 
                  nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    permission = relationship("Permission")
    college = relationship("College")

    # Ensure unique combination
    __table_args__ = (
        {"extend_existing": True},
    )


class UserCustomPermission(Base):
    __tablename__ = "user_custom_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    granted = Column(Boolean, default=True, nullable=False)  # TRUE = grant, FALSE = revoke
    created_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    permission = relationship("Permission")
    granter = relationship("User", foreign_keys=[granted_by])

    # Ensure unique combination
    __table_args__ = (
        {"extend_existing": True},
    )

# ==================== POST ENGAGEMENT MODELS ====================

class PostLike(Base):
    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="likes")
    user = relationship("User")

    # Ensure unique combination
    __table_args__ = (
        {"extend_existing": True},
    )


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Max 500 chars enforced in validation
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments")
    user = relationship("User")


class PostIgnite(Base):
    __tablename__ = "post_ignites"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    giver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="ignites")
    giver = relationship("User", foreign_keys=[giver_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

    # Ensure unique combination
    __table_args__ = (
        {"extend_existing": True},
    )


# ==================== CENTRALIZED REWARD POOL MODELS ====================

class CollegeRewardPool(Base):
    __tablename__ = "college_reward_pools"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_balance = Column(Integer, default=0, nullable=False)
    reserved_balance = Column(Integer, default=0, nullable=False)
    # available_balance is computed in DB, we'll calculate it in code
    initial_allocation = Column(Integer, default=0, nullable=False)
    lifetime_credits = Column(Integer, default=0, nullable=False)
    lifetime_debits = Column(Integer, default=0, nullable=False)
    low_balance_threshold = Column(Integer, default=1000, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    college = relationship("College")

    @property
    def available_balance(self):
        """Calculate available balance (total - reserved)"""
        return self.total_balance - self.reserved_balance

    @property
    def is_low_balance(self):
        """Check if pool is running low"""
        return self.available_balance < self.low_balance_threshold


class PoolTransaction(Base):
    __tablename__ = "pool_transactions"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)  # CREDIT, DEBIT
    amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    beneficiary_user_id = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict

    # Relationships
    college = relationship("College")
    beneficiary = relationship("User", foreign_keys=[beneficiary_user_id])
    creator = relationship("User", foreign_keys=[created_by])

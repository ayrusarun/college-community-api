from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.models import (
    User, College, Product, ProductCategory, ProductStatus, 
    Cart, CartItem, Order, OrderItem, OrderStatus, 
    PointTransaction, RewardPoint, WishlistItem
)
from ..models.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse,
    CheckoutRequest, OrderResponse, OrderListResponse, OrderStatusUpdate, OrderItemResponse,
    BalanceResponse, BalanceHistoryResponse, PointTransactionResponse,
    WishlistAdd, WishlistResponse, WishlistItemResponse, CategoryResponse
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rewards/store", tags=["rewards-store"])


# ==================== PRODUCT MANAGEMENT ====================

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all product categories with counts"""
    categories = []
    
    for category in ProductCategory:
        count = db.query(Product).filter(
            and_(
                Product.college_id == current_user.college_id,
                Product.category == category,
                Product.status == ProductStatus.ACTIVE
            )
        ).count()
        
        categories.append(CategoryResponse(
            category=category,
            display_name=category.value.replace("_", " ").title(),
            product_count=count
        ))
    
    return categories


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    category: Optional[ProductCategory] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    min_points: Optional[int] = Query(None, description="Minimum points required"),
    max_points: Optional[int] = Query(None, description="Maximum points required"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get products with filtering and pagination"""
    
    # Base query - only products from user's college
    query = db.query(Product).filter(
        and_(
            Product.college_id == current_user.college_id,
            Product.status == ProductStatus.ACTIVE
        )
    )
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
            Product.brand.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if min_points is not None:
        query = query.filter(Product.points_required >= min_points)
    
    if max_points is not None:
        query = query.filter(Product.points_required <= max_points)
    
    if in_stock is True:
        query = query.filter(Product.stock_quantity > 0)
    elif in_stock is False:
        query = query.filter(Product.stock_quantity <= 0)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination and ordering
    offset = (page - 1) * page_size
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Build response with additional info
    product_responses = []
    for product in products:
        creator = db.query(User).filter(User.id == product.created_by).first()
        
        product_responses.append(ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            category=product.category,
            points_required=product.points_required,
            original_price=float(product.original_price) if product.original_price else None,
            stock_quantity=product.stock_quantity,
            max_quantity_per_user=product.max_quantity_per_user,
            status=product.status,
            image_url=product.image_url,
            brand=product.brand,
            specifications=product.specifications,
            college_id=product.college_id,
            created_by=product.created_by,
            created_at=product.created_at,
            updated_at=product.updated_at,
            creator_name=creator.full_name if creator else "Unknown",
            in_stock=product.stock_quantity > 0,
            can_purchase=product.stock_quantity > 0 and product.status == ProductStatus.ACTIVE
        ))
    
    return ProductListResponse(
        products=product_responses,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific product"""
    
    product = db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.college_id == current_user.college_id
        )
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    creator = db.query(User).filter(User.id == product.created_by).first()
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        points_required=product.points_required,
        original_price=float(product.original_price) if product.original_price else None,
        stock_quantity=product.stock_quantity,
        max_quantity_per_user=product.max_quantity_per_user,
        status=product.status,
        image_url=product.image_url,
        brand=product.brand,
        specifications=product.specifications,
        college_id=product.college_id,
        created_by=product.created_by,
        created_at=product.created_at,
        updated_at=product.updated_at,
        creator_name=creator.full_name if creator else "Unknown",
        in_stock=product.stock_quantity > 0,
        can_purchase=product.stock_quantity > 0 and product.status == ProductStatus.ACTIVE
    )


# ==================== ADMIN PRODUCT MANAGEMENT ====================

@router.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product (admin only)"""
    
    # For now, let's allow any user to create products
    # In a real system, you'd check for admin role here
    
    product = Product(
        name=product_data.name,
        description=product_data.description,
        category=product_data.category,
        points_required=product_data.points_required,
        original_price=product_data.original_price,
        stock_quantity=product_data.stock_quantity,
        max_quantity_per_user=product_data.max_quantity_per_user,
        image_url=product_data.image_url,
        brand=product_data.brand,
        specifications=product_data.specifications,
        college_id=current_user.college_id,
        created_by=current_user.id
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        points_required=product.points_required,
        original_price=float(product.original_price) if product.original_price else None,
        stock_quantity=product.stock_quantity,
        max_quantity_per_user=product.max_quantity_per_user,
        status=product.status,
        image_url=product.image_url,
        brand=product.brand,
        specifications=product.specifications,
        college_id=product.college_id,
        created_by=product.created_by,
        created_at=product.created_at,
        updated_at=product.updated_at,
        creator_name=current_user.full_name,
        in_stock=product.stock_quantity > 0,
        can_purchase=product.stock_quantity > 0 and product.status == ProductStatus.ACTIVE
    )


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product (admin only)"""
    
    product = db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.college_id == current_user.college_id
        )
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    creator = db.query(User).filter(User.id == product.created_by).first()
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        category=product.category,
        points_required=product.points_required,
        original_price=float(product.original_price) if product.original_price else None,
        stock_quantity=product.stock_quantity,
        max_quantity_per_user=product.max_quantity_per_user,
        status=product.status,
        image_url=product.image_url,
        brand=product.brand,
        specifications=product.specifications,
        college_id=product.college_id,
        created_by=product.created_by,
        created_at=product.created_at,
        updated_at=product.updated_at,
        creator_name=creator.full_name if creator else "Unknown",
        in_stock=product.stock_quantity > 0,
        can_purchase=product.stock_quantity > 0 and product.status == ProductStatus.ACTIVE
    )


# ==================== CART MANAGEMENT ====================

async def get_or_create_cart(user_id: int, college_id: int, db: Session) -> Cart:
    """Get existing cart or create a new one for the user"""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    
    if not cart:
        cart = Cart(
            user_id=user_id,
            college_id=college_id
        )
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current cart"""
    
    cart = await get_or_create_cart(current_user.id, current_user.college_id, db)
    
    # Get cart items with product details
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    
    items_response = []
    total_points = 0
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            item_total = product.points_required * item.quantity
            total_points += item_total
            
            items_response.append(CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                added_at=item.added_at,
                product_name=product.name,
                product_points=product.points_required,
                total_points=item_total,
                product_image=product.image_url,
                product_stock=product.stock_quantity,
                max_quantity_allowed=min(product.max_quantity_per_user, product.stock_quantity)
            ))
    
    return CartResponse(
        id=cart.id,
        items=items_response,
        total_items=len(items_response),
        total_points=total_points,
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.post("/cart/add")
async def add_to_cart(
    cart_item: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart"""
    
    # Validate product exists and is available
    product = db.query(Product).filter(
        and_(
            Product.id == cart_item.product_id,
            Product.college_id == current_user.college_id,
            Product.status == ProductStatus.ACTIVE
        )
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not available")
    
    if product.stock_quantity < cart_item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    if cart_item.quantity > product.max_quantity_per_user:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {product.max_quantity_per_user} items allowed per user"
        )
    
    # Get or create cart
    cart = await get_or_create_cart(current_user.id, current_user.college_id, db)
    
    # Check if item already exists in cart
    existing_item = db.query(CartItem).filter(
        and_(
            CartItem.cart_id == cart.id,
            CartItem.product_id == cart_item.product_id
        )
    ).first()
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + cart_item.quantity
        
        if new_quantity > product.max_quantity_per_user:
            raise HTTPException(
                status_code=400,
                detail=f"Total quantity would exceed maximum of {product.max_quantity_per_user} items"
            )
        
        if new_quantity > product.stock_quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for total quantity")
        
        existing_item.quantity = new_quantity
    else:
        # Create new cart item
        new_item = CartItem(
            cart_id=cart.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(new_item)
    
    # Update cart timestamp
    cart.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Item added to cart successfully"}


@router.put("/cart/update/{item_id}")
async def update_cart_item(
    item_id: int,
    update_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_item = db.query(CartItem).filter(
        and_(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate new quantity
    if update_data.quantity <= 0:
        # Remove item if quantity is 0 or negative
        db.delete(cart_item)
    else:
        if update_data.quantity > product.stock_quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        
        if update_data.quantity > product.max_quantity_per_user:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {product.max_quantity_per_user} items allowed per user"
            )
        
        cart_item.quantity = update_data.quantity
    
    # Update cart timestamp
    cart.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Cart updated successfully"}


@router.delete("/cart/remove/{item_id}")
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart_item = db.query(CartItem).filter(
        and_(
            CartItem.id == item_id,
            CartItem.cart_id == cart.id
        )
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    cart.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Item removed from cart"}


@router.delete("/cart/clear")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear entire cart"""
    
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        return {"message": "Cart already empty"}
    
    # Delete all cart items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    cart.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Cart cleared successfully"}


# ==================== CHECKOUT & ORDERS ====================

def generate_order_number() -> str:
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4())[:8].upper()
    return f"ORD{timestamp}{random_part}"


@router.post("/checkout", response_model=OrderResponse)
async def checkout(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process cart checkout"""
    
    # Get user's cart
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Get cart items
    cart_items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate total points and validate
    total_points = 0
    order_items_data = []
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"Product not found: {item.product_id}")
        
        if product.status != ProductStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"Product not available: {product.name}")
        
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
        
        item_total = product.points_required * item.quantity
        total_points += item_total
        
        order_items_data.append({
            "product": product,
            "quantity": item.quantity,
            "points_per_item": product.points_required,
            "total_points": item_total
        })
    
    # Check user's balance
    user_points = db.query(RewardPoint).filter(RewardPoint.user_id == current_user.id).first()
    if not user_points or user_points.total_points < total_points:
        available_points = user_points.total_points if user_points else 0
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient points. Required: {total_points}, Available: {available_points}"
        )
    
    # Create order
    order = Order(
        order_number=generate_order_number(),
        user_id=current_user.id,
        total_points=total_points,
        total_items=len(cart_items),
        notes=checkout_data.notes,
        college_id=current_user.college_id
    )
    
    db.add(order)
    db.flush()  # Get order ID
    
    # Create order items and update stock
    order_items = []
    for item_data in order_items_data:
        product = item_data["product"]
        
        # Create order item
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data["quantity"],
            points_per_item=item_data["points_per_item"],
            total_points=item_data["total_points"],
            product_name=product.name
        )
        db.add(order_item)
        order_items.append(order_item)
        
        # Update product stock
        product.stock_quantity -= item_data["quantity"]
    
    # Deduct points from user
    user_points.total_points -= total_points
    
    # Create point transaction
    transaction = PointTransaction(
        user_id=current_user.id,
        transaction_type="SPENT",
        points=-total_points,
        balance_after=user_points.total_points,
        description=f"Order #{order.order_number} - {len(cart_items)} items",
        reference_type="order",
        reference_id=order.id,
        college_id=current_user.college_id
    )
    db.add(transaction)
    
    # Clear cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    
    db.commit()
    db.refresh(order)
    
    # Build response
    order_items_response = []
    for item in order_items:
        order_items_response.append(OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            points_per_item=item.points_per_item,
            total_points=item.total_points,
            created_at=item.created_at
        ))
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        total_points=order.total_points,
        total_items=order.total_items,
        status=order.status,
        notes=order.notes,
        pickup_location=order.pickup_location,
        estimated_pickup_date=order.estimated_pickup_date,
        items=order_items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
        user_name=current_user.full_name,
        status_display=order.status.value.replace("_", " ").title()
    )


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's order history"""
    
    # Get total count
    total_count = db.query(Order).filter(Order.user_id == current_user.id).count()
    
    # Get orders with pagination
    offset = (page - 1) * page_size
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(desc(Order.created_at)).offset(offset).limit(page_size).all()
    
    # Build response
    order_responses = []
    for order in orders:
        # Get order items
        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        items_response = []
        
        for item in items:
            items_response.append(OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                points_per_item=item.points_per_item,
                total_points=item.total_points,
                created_at=item.created_at
            ))
        
        order_responses.append(OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            total_points=order.total_points,
            total_items=order.total_items,
            status=order.status,
            notes=order.notes,
            pickup_location=order.pickup_location,
            estimated_pickup_date=order.estimated_pickup_date,
            items=items_response,
            created_at=order.created_at,
            updated_at=order.updated_at,
            user_name=current_user.full_name,
            status_display=order.status.value.replace("_", " ").title()
        ))
    
    return OrderListResponse(
        orders=order_responses,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific order details"""
    
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get order items
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    items_response = []
    
    for item in items:
        items_response.append(OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            points_per_item=item.points_per_item,
            total_points=item.total_points,
            created_at=item.created_at
        ))
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        total_points=order.total_points,
        total_items=order.total_items,
        status=order.status,
        notes=order.notes,
        pickup_location=order.pickup_location,
        estimated_pickup_date=order.estimated_pickup_date,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
        user_name=current_user.full_name,
        status_display=order.status.value.replace("_", " ").title()
    )


# ==================== BALANCE & TRANSACTIONS ====================

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's current point balance and summary"""
    
    # Get current balance
    user_points = db.query(RewardPoint).filter(RewardPoint.user_id == current_user.id).first()
    current_balance = user_points.total_points if user_points else 0
    
    # Calculate total earned and spent
    total_earned = db.query(func.sum(PointTransaction.points)).filter(
        and_(
            PointTransaction.user_id == current_user.id,
            PointTransaction.transaction_type == "EARNED"
        )
    ).scalar() or 0
    
    total_spent = abs(db.query(func.sum(PointTransaction.points)).filter(
        and_(
            PointTransaction.user_id == current_user.id,
            PointTransaction.transaction_type == "SPENT"
        )
    ).scalar() or 0)
    
    # Calculate pending orders points
    pending_orders_points = db.query(func.sum(Order.total_points)).filter(
        and_(
            Order.user_id == current_user.id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING])
        )
    ).scalar() or 0
    
    available_balance = current_balance  # In this simple system, all balance is available
    
    return BalanceResponse(
        current_balance=current_balance,
        total_earned=total_earned,
        total_spent=total_spent,
        pending_orders_points=pending_orders_points,
        available_balance=available_balance
    )


@router.get("/balance/history", response_model=BalanceHistoryResponse)
async def get_balance_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's point transaction history"""
    
    # Get total count
    total_count = db.query(PointTransaction).filter(
        PointTransaction.user_id == current_user.id
    ).count()
    
    # Get transactions with pagination
    offset = (page - 1) * page_size
    transactions = db.query(PointTransaction).filter(
        PointTransaction.user_id == current_user.id
    ).order_by(desc(PointTransaction.created_at)).offset(offset).limit(page_size).all()
    
    # Build transaction responses
    transaction_responses = []
    for transaction in transactions:
        transaction_responses.append(PointTransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            points=transaction.points,
            balance_after=transaction.balance_after,
            description=transaction.description,
            reference_type=transaction.reference_type,
            reference_id=transaction.reference_id,
            created_at=transaction.created_at
        ))
    
    # Get balance summary
    balance_summary = await get_balance(current_user, db)
    
    return BalanceHistoryResponse(
        transactions=transaction_responses,
        balance_summary=balance_summary,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


# ==================== WISHLIST ====================

@router.get("/wishlist", response_model=WishlistResponse)
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's wishlist"""
    
    wishlist_items = db.query(WishlistItem).filter(
        WishlistItem.user_id == current_user.id
    ).order_by(desc(WishlistItem.added_at)).all()
    
    items_response = []
    for item in wishlist_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:  # Product still exists
            items_response.append(WishlistItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name,
                product_points=product.points_required,
                product_image=product.image_url,
                product_status=product.status,
                added_at=item.added_at,
                in_stock=product.stock_quantity > 0
            ))
    
    return WishlistResponse(
        items=items_response,
        total_count=len(items_response)
    )


@router.post("/wishlist/add")
async def add_to_wishlist(
    wishlist_data: WishlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add product to wishlist"""
    
    # Validate product exists
    product = db.query(Product).filter(
        and_(
            Product.id == wishlist_data.product_id,
            Product.college_id == current_user.college_id
        )
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if already in wishlist
    existing_item = db.query(WishlistItem).filter(
        and_(
            WishlistItem.user_id == current_user.id,
            WishlistItem.product_id == wishlist_data.product_id
        )
    ).first()
    
    if existing_item:
        return {"message": "Product already in wishlist"}
    
    # Add to wishlist
    wishlist_item = WishlistItem(
        user_id=current_user.id,
        product_id=wishlist_data.product_id,
        college_id=current_user.college_id
    )
    
    db.add(wishlist_item)
    db.commit()
    
    return {"message": "Product added to wishlist"}


@router.delete("/wishlist/remove/{product_id}")
async def remove_from_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove product from wishlist"""
    
    wishlist_item = db.query(WishlistItem).filter(
        and_(
            WishlistItem.user_id == current_user.id,
            WishlistItem.product_id == product_id
        )
    ).first()
    
    if not wishlist_item:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")
    
    db.delete(wishlist_item)
    db.commit()
    
    return {"message": "Product removed from wishlist"}


# ==================== ADMIN ENDPOINTS ====================

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status (admin only)"""
    
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.college_id == current_user.college_id
        )
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update order status and details
    order.status = status_data.status
    if status_data.notes:
        order.notes = status_data.notes
    if status_data.pickup_location:
        order.pickup_location = status_data.pickup_location
    if status_data.estimated_pickup_date:
        order.estimated_pickup_date = status_data.estimated_pickup_date
    
    db.commit()
    db.refresh(order)
    
    # Get order items for response
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    items_response = []
    
    for item in items:
        items_response.append(OrderItemResponse(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=item.quantity,
            points_per_item=item.points_per_item,
            total_points=item.total_points,
            created_at=item.created_at
        ))
    
    user = db.query(User).filter(User.id == order.user_id).first()
    
    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        total_points=order.total_points,
        total_items=order.total_items,
        status=order.status,
        notes=order.notes,
        pickup_location=order.pickup_location,
        estimated_pickup_date=order.estimated_pickup_date,
        items=items_response,
        created_at=order.created_at,
        updated_at=order.updated_at,
        user_name=user.full_name if user else "Unknown",
        status_display=order.status.value.replace("_", " ").title()
    )
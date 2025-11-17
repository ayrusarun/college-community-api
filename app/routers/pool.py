"""
Reward Pool Management Endpoints
Admin-only endpoints to manage college reward pools
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.rbac import RoleChecker
from ..models.models import (
    User, UserRole, College, CollegeRewardPool, PoolTransaction
)
from ..models.schemas import (
    PoolBalanceResponse, PoolTransactionResponse, 
    PoolCreditRequest, PoolAnalyticsResponse
)
from ..services.reward_pool import reward_pool_service

router = APIRouter(prefix="/pool", tags=["reward-pool"])


@router.get("/balance", response_model=PoolBalanceResponse)
async def get_pool_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))
):
    """Get current college reward pool balance"""
    
    pool = reward_pool_service.get_or_create_pool(db, current_user.college_id)
    college = db.query(College).filter(College.id == current_user.college_id).first()
    
    return PoolBalanceResponse(
        college_id=pool.college_id,
        college_name=college.name,
        total_balance=pool.total_balance,
        reserved_balance=pool.reserved_balance,
        available_balance=pool.available_balance,
        initial_allocation=pool.initial_allocation,
        lifetime_credits=pool.lifetime_credits,
        lifetime_debits=pool.lifetime_debits,
        low_balance_threshold=pool.low_balance_threshold,
        is_low_balance=pool.is_low_balance,
        created_at=pool.created_at,
        updated_at=pool.updated_at
    )


@router.post("/credit", response_model=PoolTransactionResponse)
async def credit_pool(
    credit_request: PoolCreditRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN))  # Only ADMIN can credit pool
):
    """
    Add points to college reward pool (Admin only)
    This is typically done to top-up the pool when it runs low
    """
    
    if credit_request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    if credit_request.amount > 100000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot credit more than 100,000 points at once"
        )
    
    transaction = reward_pool_service.credit_pool(
        db=db,
        college_id=current_user.college_id,
        amount=credit_request.amount,
        reason="manual_topup",
        description=credit_request.description or f"Manual credit by {current_user.full_name}",
        created_by=current_user.id
    )
    
    return PoolTransactionResponse(
        id=transaction.id,
        college_id=transaction.college_id,
        transaction_type=transaction.transaction_type,
        amount=transaction.amount,
        balance_before=transaction.balance_before,
        balance_after=transaction.balance_after,
        reason=transaction.reason,
        description=transaction.description,
        reference_type=transaction.reference_type,
        reference_id=transaction.reference_id,
        beneficiary_user_id=transaction.beneficiary_user_id,
        beneficiary_name=None,
        created_by=transaction.created_by,
        creator_name=current_user.full_name,
        created_at=transaction.created_at
    )


@router.get("/transactions", response_model=List[PoolTransactionResponse])
async def get_pool_transactions(
    page: int = 1,
    page_size: int = 50,
    transaction_type: str = None,  # CREDIT or DEBIT
    reason: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))
):
    """Get pool transaction history"""
    
    query = db.query(PoolTransaction).filter(
        PoolTransaction.college_id == current_user.college_id
    )
    
    if transaction_type:
        query = query.filter(PoolTransaction.transaction_type == transaction_type.upper())
    
    if reason:
        query = query.filter(PoolTransaction.reason == reason)
    
    # Pagination
    skip = (page - 1) * page_size
    transactions = query.order_by(
        desc(PoolTransaction.created_at)
    ).offset(skip).limit(page_size).all()
    
    # Build response with user names
    responses = []
    for txn in transactions:
        beneficiary_name = None
        creator_name = None
        
        if txn.beneficiary_user_id:
            beneficiary = db.query(User).filter(User.id == txn.beneficiary_user_id).first()
            if beneficiary:
                beneficiary_name = beneficiary.full_name
        
        if txn.created_by:
            creator = db.query(User).filter(User.id == txn.created_by).first()
            if creator:
                creator_name = creator.full_name
        
        responses.append(PoolTransactionResponse(
            id=txn.id,
            college_id=txn.college_id,
            transaction_type=txn.transaction_type,
            amount=txn.amount,
            balance_before=txn.balance_before,
            balance_after=txn.balance_after,
            reason=txn.reason,
            description=txn.description,
            reference_type=txn.reference_type,
            reference_id=txn.reference_id,
            beneficiary_user_id=txn.beneficiary_user_id,
            beneficiary_name=beneficiary_name,
            created_by=txn.created_by,
            creator_name=creator_name,
            created_at=txn.created_at
        ))
    
    return responses


@router.get("/analytics", response_model=PoolAnalyticsResponse)
async def get_pool_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(RoleChecker(UserRole.ADMIN, UserRole.STAFF))
):
    """Get comprehensive pool analytics"""
    
    pool = reward_pool_service.get_or_create_pool(db, current_user.college_id)
    college = db.query(College).filter(College.id == current_user.college_id).first()
    
    # Get recent transactions
    recent_txns = db.query(PoolTransaction).filter(
        PoolTransaction.college_id == current_user.college_id
    ).order_by(desc(PoolTransaction.created_at)).limit(10).all()
    
    recent_transactions = []
    for txn in recent_txns:
        beneficiary_name = None
        creator_name = None
        
        if txn.beneficiary_user_id:
            beneficiary = db.query(User).filter(User.id == txn.beneficiary_user_id).first()
            if beneficiary:
                beneficiary_name = beneficiary.full_name
        
        if txn.created_by:
            creator = db.query(User).filter(User.id == txn.created_by).first()
            if creator:
                creator_name = creator.full_name
        
        recent_transactions.append(PoolTransactionResponse(
            id=txn.id,
            college_id=txn.college_id,
            transaction_type=txn.transaction_type,
            amount=txn.amount,
            balance_before=txn.balance_before,
            balance_after=txn.balance_after,
            reason=txn.reason,
            description=txn.description,
            reference_type=txn.reference_type,
            reference_id=txn.reference_id,
            beneficiary_user_id=txn.beneficiary_user_id,
            beneficiary_name=beneficiary_name,
            created_by=txn.created_by,
            creator_name=creator_name,
            created_at=txn.created_at
        ))
    
    # Calculate statistics
    stats = {
        "total_credits": db.query(func.sum(PoolTransaction.amount)).filter(
            PoolTransaction.college_id == current_user.college_id,
            PoolTransaction.transaction_type == "CREDIT"
        ).scalar() or 0,
        "total_debits": db.query(func.sum(PoolTransaction.amount)).filter(
            PoolTransaction.college_id == current_user.college_id,
            PoolTransaction.transaction_type == "DEBIT"
        ).scalar() or 0,
        "welcome_bonuses_count": db.query(func.count(PoolTransaction.id)).filter(
            PoolTransaction.college_id == current_user.college_id,
            PoolTransaction.reason == "welcome_bonus"
        ).scalar() or 0,
        "post_rewards_count": db.query(func.count(PoolTransaction.id)).filter(
            PoolTransaction.college_id == current_user.college_id,
            PoolTransaction.reason == "post_reward"
        ).scalar() or 0,
        "admin_rewards_count": db.query(func.count(PoolTransaction.id)).filter(
            PoolTransaction.college_id == current_user.college_id,
            PoolTransaction.reason == "admin_reward"
        ).scalar() or 0,
        "total_transactions": db.query(func.count(PoolTransaction.id)).filter(
            PoolTransaction.college_id == current_user.college_id
        ).scalar() or 0,
    }
    
    return PoolAnalyticsResponse(
        pool_balance=PoolBalanceResponse(
            college_id=pool.college_id,
            college_name=college.name,
            total_balance=pool.total_balance,
            reserved_balance=pool.reserved_balance,
            available_balance=pool.available_balance,
            initial_allocation=pool.initial_allocation,
            lifetime_credits=pool.lifetime_credits,
            lifetime_debits=pool.lifetime_debits,
            low_balance_threshold=pool.low_balance_threshold,
            is_low_balance=pool.is_low_balance,
            created_at=pool.created_at,
            updated_at=pool.updated_at
        ),
        recent_transactions=recent_transactions,
        statistics=stats
    )

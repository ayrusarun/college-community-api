"""
Centralized Reward Pool Service
Handles all reward pool operations with proper validation and logging
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional

from ..models.models import CollegeRewardPool, PoolTransaction, User, RewardPoint, PointTransaction


class RewardPoolService:
    """Service for managing college reward pools"""
    
    @staticmethod
    def get_or_create_pool(db: Session, college_id: int) -> CollegeRewardPool:
        """Get pool for a college, create if doesn't exist"""
        pool = db.query(CollegeRewardPool).filter(
            CollegeRewardPool.college_id == college_id
        ).first()
        
        if not pool:
            # Create new pool with initial allocation
            pool = CollegeRewardPool(
                college_id=college_id,
                total_balance=10000,  # Initial allocation
                initial_allocation=10000,
                lifetime_credits=10000
            )
            db.add(pool)
            
            # Log initial credit
            transaction = PoolTransaction(
                college_id=college_id,
                transaction_type="CREDIT",
                amount=10000,
                balance_before=0,
                balance_after=10000,
                reason="manual_topup",
                description="Initial college reward pool allocation",
                reference_type="system"
            )
            db.add(transaction)
            db.commit()
            db.refresh(pool)
        
        return pool
    
    @staticmethod
    def check_balance(pool: CollegeRewardPool, required_amount: int) -> bool:
        """Check if pool has sufficient balance"""
        return pool.available_balance >= required_amount
    
    @staticmethod
    def debit_pool(
        db: Session,
        college_id: int,
        amount: int,
        reason: str,
        description: str,
        beneficiary_user_id: Optional[int] = None,
        created_by: Optional[int] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None
    ) -> PoolTransaction:
        """
        Debit points from college pool
        Returns: PoolTransaction record
        Raises: HTTPException if insufficient balance
        """
        pool = RewardPoolService.get_or_create_pool(db, college_id)
        
        # Check if sufficient balance
        if not RewardPoolService.check_balance(pool, amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient pool balance. Available: {pool.available_balance}, Required: {amount}"
            )
        
        # Record balance before
        balance_before = pool.total_balance
        
        # Deduct from pool
        pool.total_balance -= amount
        
        # Create transaction log
        transaction = PoolTransaction(
            college_id=college_id,
            transaction_type="DEBIT",
            amount=amount,
            balance_before=balance_before,
            balance_after=pool.total_balance,
            reason=reason,
            description=description,
            reference_type=reference_type,
            reference_id=reference_id,
            beneficiary_user_id=beneficiary_user_id,
            created_by=created_by
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def credit_pool(
        db: Session,
        college_id: int,
        amount: int,
        reason: str,
        description: str,
        created_by: Optional[int] = None
    ) -> PoolTransaction:
        """
        Credit points to college pool
        Returns: PoolTransaction record
        """
        pool = RewardPoolService.get_or_create_pool(db, college_id)
        
        # Record balance before
        balance_before = pool.total_balance
        
        # Add to pool
        pool.total_balance += amount
        
        # Create transaction log
        transaction = PoolTransaction(
            college_id=college_id,
            transaction_type="CREDIT",
            amount=amount,
            balance_before=balance_before,
            balance_after=pool.total_balance,
            reason=reason,
            description=description,
            created_by=created_by
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def give_reward_from_pool(
        db: Session,
        college_id: int,
        user_id: int,
        amount: int,
        reason: str,
        description: str,
        created_by: Optional[int] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None
    ):
        """
        Complete flow: Debit from pool + Credit to user
        This is atomic - both succeed or both fail
        """
        try:
            # 1. Debit from pool
            pool_txn = RewardPoolService.debit_pool(
                db=db,
                college_id=college_id,
                amount=amount,
                reason=reason,
                description=description,
                beneficiary_user_id=user_id,
                created_by=created_by,
                reference_type=reference_type,
                reference_id=reference_id
            )
            
            # 2. Credit to user
            user_points = db.query(RewardPoint).filter(
                RewardPoint.user_id == user_id
            ).first()
            
            if not user_points:
                user_points = RewardPoint(user_id=user_id, total_points=0)
                db.add(user_points)
            
            user_points.total_points += amount
            
            # 3. Log user transaction
            user_transaction = PointTransaction(
                user_id=user_id,
                transaction_type="EARNED",
                points=amount,
                balance_after=user_points.total_points,
                description=description,
                reference_type=reference_type,
                reference_id=reference_id,
                college_id=college_id
            )
            db.add(user_transaction)
            
            db.commit()
            
            return {
                "pool_transaction": pool_txn,
                "user_balance": user_points.total_points
            }
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process reward: {str(e)}"
            )


# Create a singleton instance
reward_pool_service = RewardPoolService()

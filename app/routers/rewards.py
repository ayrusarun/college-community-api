from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List

from ..core.database import get_db
from ..core.utils import time_ago
from ..models.models import Reward, RewardPoint, User, Post, RewardType
from ..models.schemas import (
    RewardCreate, RewardResponse, RewardPointsResponse, 
    RewardLeaderboardResponse, RewardSummaryResponse
)
from ..routers.auth import get_current_user

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.post("/", response_model=RewardResponse)
async def give_reward(
    reward: RewardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Give a reward to another user"""
    
    # Validate that receiver exists and is in the same college
    receiver = db.query(User).filter(
        User.id == reward.receiver_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found or not in your college"
        )
    
    # Users cannot reward themselves
    if reward.receiver_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot give rewards to yourself"
        )
    
    # Validate post if provided
    post_title = None
    if reward.post_id:
        post = db.query(Post).filter(
            Post.id == reward.post_id,
            Post.college_id == current_user.college_id
        ).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        post_title = post.title
    
    # Validate points (must be between 1 and 100)
    if reward.points < 1 or reward.points > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Points must be between 1 and 100"
        )
    
    # Create the reward record
    db_reward = Reward(
        giver_id=current_user.id,
        receiver_id=reward.receiver_id,
        points=reward.points,
        reward_type=reward.reward_type,
        title=reward.title,
        description=reward.description,
        post_id=reward.post_id,
        college_id=current_user.college_id
    )
    
    db.add(db_reward)
    
    # Update or create receiver's reward points
    receiver_points = db.query(RewardPoint).filter(
        RewardPoint.user_id == reward.receiver_id
    ).first()
    
    if receiver_points:
        receiver_points.total_points += reward.points
    else:
        receiver_points = RewardPoint(
            user_id=reward.receiver_id,
            total_points=reward.points
        )
        db.add(receiver_points)
    
    db.commit()
    db.refresh(db_reward)
    
    # Return detailed response
    return RewardResponse(
        id=db_reward.id,
        giver_id=db_reward.giver_id,
        receiver_id=db_reward.receiver_id,
        points=db_reward.points,
        reward_type=db_reward.reward_type,
        title=db_reward.title,
        description=db_reward.description,
        post_id=db_reward.post_id,
        college_id=db_reward.college_id,
        created_at=db_reward.created_at,
        giver_name=current_user.full_name,
        receiver_name=receiver.full_name,
        giver_department=current_user.department,
        receiver_department=receiver.department,
        post_title=post_title
    )


@router.get("/", response_model=List[RewardResponse])
async def get_rewards(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all rewards in the college (recent first)"""
    
    rewards = db.query(
        Reward, 
        User.full_name.label("giver_name"),
        User.department.label("giver_department"),
        User.full_name.label("receiver_name"),
        User.department.label("receiver_department"),
        Post.title.label("post_title")
    ).join(
        User, Reward.giver_id == User.id, isouter=False
    ).join(
        User.alias(), Reward.receiver_id == User.id, isouter=False  
    ).outerjoin(
        Post, Reward.post_id == Post.id
    ).filter(
        Reward.college_id == current_user.college_id
    ).order_by(
        desc(Reward.created_at)
    ).offset(skip).limit(limit).all()
    
    # Format response (simplified for now - would need proper joins)
    reward_responses = []
    for reward_data in rewards:
        reward = reward_data[0]
        
        # Get giver and receiver info
        giver = db.query(User).filter(User.id == reward.giver_id).first()
        receiver = db.query(User).filter(User.id == reward.receiver_id).first()
        post = db.query(Post).filter(Post.id == reward.post_id).first() if reward.post_id else None
        
        reward_responses.append(RewardResponse(
            id=reward.id,
            giver_id=reward.giver_id,
            receiver_id=reward.receiver_id,
            points=reward.points,
            reward_type=reward.reward_type,
            title=reward.title,
            description=reward.description,
            post_id=reward.post_id,
            college_id=reward.college_id,
            created_at=reward.created_at,
            giver_name=giver.full_name,
            receiver_name=receiver.full_name,
            giver_department=giver.department,
            receiver_department=receiver.department,
            post_title=post.title if post else None
        ))
    
    return reward_responses


@router.get("/me", response_model=RewardSummaryResponse)
async def get_my_rewards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's reward summary"""
    
    # Get total points
    user_points = db.query(RewardPoint).filter(
        RewardPoint.user_id == current_user.id
    ).first()
    
    total_points = user_points.total_points if user_points else 0
    
    # Count rewards given and received
    rewards_given = db.query(func.count(Reward.id)).filter(
        Reward.giver_id == current_user.id
    ).scalar()
    
    rewards_received = db.query(func.count(Reward.id)).filter(
        Reward.receiver_id == current_user.id
    ).scalar()
    
    # Get recent rewards (both given and received)
    recent_rewards_query = db.query(Reward).filter(
        (Reward.giver_id == current_user.id) | (Reward.receiver_id == current_user.id)
    ).order_by(desc(Reward.created_at)).limit(10).all()
    
    recent_rewards = []
    for reward in recent_rewards_query:
        giver = db.query(User).filter(User.id == reward.giver_id).first()
        receiver = db.query(User).filter(User.id == reward.receiver_id).first()
        post = db.query(Post).filter(Post.id == reward.post_id).first() if reward.post_id else None
        
        recent_rewards.append(RewardResponse(
            id=reward.id,
            giver_id=reward.giver_id,
            receiver_id=reward.receiver_id,
            points=reward.points,
            reward_type=reward.reward_type,
            title=reward.title,
            description=reward.description,
            post_id=reward.post_id,
            college_id=reward.college_id,
            created_at=reward.created_at,
            giver_name=giver.full_name,
            receiver_name=receiver.full_name,
            giver_department=giver.department,
            receiver_department=receiver.department,
            post_title=post.title if post else None
        ))
    
    return RewardSummaryResponse(
        total_points=total_points,
        rewards_given=rewards_given,
        rewards_received=rewards_received,
        recent_rewards=recent_rewards
    )


@router.get("/leaderboard", response_model=List[RewardLeaderboardResponse])
async def get_leaderboard(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get college leaderboard based on reward points"""
    
    leaderboard = db.query(
        RewardPoint.user_id,
        RewardPoint.total_points,
        User.full_name,
        User.department
    ).join(
        User, RewardPoint.user_id == User.id
    ).filter(
        User.college_id == current_user.college_id
    ).order_by(
        desc(RewardPoint.total_points)
    ).limit(limit).all()
    
    return [
        RewardLeaderboardResponse(
            user_id=item.user_id,
            user_name=item.full_name,
            department=item.department,
            total_points=item.total_points,
            rank=index + 1
        )
        for index, item in enumerate(leaderboard)
    ]


@router.get("/points/{user_id}", response_model=RewardPointsResponse)
async def get_user_points(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reward points for a specific user"""
    
    # Verify user is in the same college
    user = db.query(User).filter(
        User.id == user_id,
        User.college_id == current_user.college_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_points = db.query(RewardPoint).filter(
        RewardPoint.user_id == user_id
    ).first()
    
    if not user_points:
        # Create default points record if it doesn't exist
        user_points = RewardPoint(user_id=user_id, total_points=0)
        db.add(user_points)
        db.commit()
        db.refresh(user_points)
    
    return RewardPointsResponse(
        id=user_points.id,
        user_id=user_points.user_id,
        total_points=user_points.total_points,
        created_at=user_points.created_at,
        updated_at=user_points.updated_at,
        user_name=user.full_name,
        user_department=user.department
    )


@router.get("/types", response_model=List[str])
async def get_reward_types():
    """Get available reward types"""
    return [reward_type.value for reward_type in RewardType]
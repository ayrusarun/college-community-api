from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..core.database import get_db
from ..core.security import verify_password, create_access_token, verify_token, get_current_user
from ..core.config import settings
from ..models.models import User, College
from ..models.schemas import Token, LoginRequest

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# get_current_user is now imported from security module


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get college information for tenant details
    college = db.query(College).filter(College.id == user.college_id).first()
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "college_slug": college.slug,
            "college_name": college.name,
            "user_id": user.id
        }, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a real implementation, you might want to blacklist the token
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    college = db.query(College).filter(College.id == current_user.college_id).first()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "college": {
            "id": college.id,
            "name": college.name,
            "slug": college.slug
        }
    }
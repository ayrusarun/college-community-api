from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine
from .models.models import Base
from .routers import auth, users, posts, rewards, files, ai, alerts, news, store, admin

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="College Community API",
    description="A multi-tenant SaaS college community application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(rewards.router)
app.include_router(files.router)
app.include_router(ai.router)
app.include_router(alerts.router)
app.include_router(news.router)
app.include_router(store.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return {"message": "Welcome to College Community API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
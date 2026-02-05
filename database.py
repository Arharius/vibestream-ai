import os
import re
import urllib.parse
from sqlalchemy import create_engine, Column, String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

raw_url = os.getenv("DATABASE_URL", "")

# Очистка URL от мусора
clean_url = re.sub(r'^psql\s+', '', raw_url.strip()).strip("'\" ")
clean_url = clean_url.split('&channel_binding=')[0]

if "@" in clean_url and "://" in clean_url:
    try:
        prefix, rest = clean_url.split("://", 1)
        auth, host = rest.rsplit("@", 1)
        if ":" in auth:
            user, pwd = auth.split(":", 1)
            clean_url = f"{prefix}://{user}:{urllib.parse.quote_plus(pwd)}@{host}"
    except: pass

if clean_url.startswith("postgres://"):
    clean_url = clean_url.replace("postgres://", "postgresql://", 1)

DATABASE_URL = clean_url or "sqlite:///./fallback.db"

# connect_timeout=10 предотвращает ошибку 504 при долгом соединении
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,
    connect_args={"sslmode": "require", "connect_timeout": 10} if "postgresql" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True, index=True)
    is_pro = Column(Boolean, default=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    video_id = Column(String)
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_user(user_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id); db.add(user); db.commit(); db.refresh(user)
        return user
    finally: db.close()

def save_project(user_id, video_id, title, content):
    db = SessionLocal()
    try:
        new_project = Project(user_id=user_id, video_id=video_id, title=title, content=content)
        db.add(new_project); db.commit()
    finally: db.close()
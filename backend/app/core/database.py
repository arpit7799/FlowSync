"""Database configuration, session management, and base declarative class."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from .config import settings

# Handle SQLite vs Postgres connection args
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI database dependency yielding an isolated session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and seed default intersection records."""
    Base.metadata.create_all(bind=engine)
    
    # Seed initial intersections if empty
    from backend.app.models.traffic import Intersection
    db = SessionLocal()
    try:
        if db.query(Intersection).count() == 0:
            default_intersections = [
                Intersection(id="J1", name="Junction 1 (North-West)", location_x=500.0, location_y=500.0, num_lanes=12, status="online"),
                Intersection(id="J2", name="Junction 2 (North-East)", location_x=1000.0, location_y=500.0, num_lanes=12, status="online"),
                Intersection(id="J3", name="Junction 3 (South-West)", location_x=500.0, location_y=0.0, num_lanes=12, status="online"),
                Intersection(id="J4", name="Junction 4 (South-East)", location_x=1000.0, location_y=0.0, num_lanes=12, status="online"),
            ]
            db.add_all(default_intersections)
            db.commit()
    except Exception as exc:
        db.rollback()
    finally:
        db.close()

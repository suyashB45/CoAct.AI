"""
Database Models for CoAct.AI
Uses SQLAlchemy with PostgreSQL
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:2005@localhost:5432/coact_ai")

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Session(Base):
    """Coaching session model"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    user_role = Column(String(255), nullable=True)
    ai_role = Column(String(255), nullable=True)
    scenario = Column(Text, nullable=True)
    framework = Column(String(255), nullable=True)
    mode = Column(String(50), default="coaching")
    transcript = Column(JSON, default=list)
    status = Column(String(50), default="active")
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "role": self.user_role,
            "ai_role": self.ai_role,
            "scenario": self.scenario,
            "framework": self.framework,
            "mode": self.mode,
            "transcript": self.transcript or [],
            "status": self.status,
            "report_data": self.report_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class Report(Base):
    """Generated report model"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    report_type = Column(String(50), default="pdf")
    filename = Column(String(255), nullable=True)
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions for session management
def get_session_by_id(session_id: str):
    """Get session by ID from database"""
    db = SessionLocal()
    try:
        return db.query(Session).filter(Session.id == session_id).first()
    finally:
        db.close()


def create_session(session_id: str, data: dict):
    """Create new session in database"""
    db = SessionLocal()
    try:
        session = Session(
            id=session_id,
            user_role=data.get("role"),
            ai_role=data.get("ai_role"),
            scenario=data.get("scenario"),
            framework=data.get("framework"),
            mode=data.get("mode", "coaching"),
            transcript=data.get("transcript", []),
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        print(f"Error creating session: {e}")
        return None
    finally:
        db.close()


def update_session(session_id: str, data: dict):
    """Update session in database"""
    db = SessionLocal()
    try:
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            for key, value in data.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.utcnow()
            db.commit()
            return session
        return None
    except Exception as e:
        db.rollback()
        print(f"Error updating session: {e}")
        return None
    finally:
        db.close()


def save_report(session_id: str, filename: str, report_data: dict):
    """Save report to database"""
    db = SessionLocal()
    try:
        report = Report(
            session_id=session_id,
            filename=filename,
            report_data=report_data
        )
        db.add(report)
        db.commit()
        return report
    except Exception as e:
        db.rollback()
        print(f"Error saving report: {e}")
        return None
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_db()

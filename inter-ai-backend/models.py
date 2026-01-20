import os
import json
import datetime as dt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text

db = SQLAlchemy()

# ---------------------------------------------------------
# Database Models
# ---------------------------------------------------------

class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(100), default='user')
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role
        }

class PracticeHistory(db.Model):
    __tablename__ = 'practice_history'
    
    session_id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=dt.datetime.utcnow)
    scenario_type = Column(String(50), nullable=False)
    role = Column(String(100))
    ai_role = Column(String(100))
    transcript = Column(JSONB)
    report_data = Column(JSONB)
    completed = Column(Boolean, default=False)

    # Relationships
    user = db.relationship("User", backref="practice_sessions")
    coaching_report = db.relationship("CoachingReport", backref="session", uselist=False, cascade="all, delete-orphan")
    sales_report = db.relationship("SalesReport", backref="session", uselist=False, cascade="all, delete-orphan")
    learning_plan = db.relationship("LearningPlan", backref="session", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else None,
            "scenario_type": self.scenario_type,
            "role": self.role,
            "ai_role": self.ai_role,
            "transcript": self.transcript,
            "report_data": self.report_data,
            "completed": self.completed,
            "reports": {
                "coaching": self.coaching_report.to_dict() if self.coaching_report else None,
                "sales": self.sales_report.to_dict() if self.sales_report else None,
                "learning": self.learning_plan.to_dict() if self.learning_plan else None
            }
        }

class CoachingReport(db.Model):
    __tablename__ = 'coaching_reports'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('practice_history.session_id'), nullable=False)
    overall_score = Column(Float)
    empathy_score = Column(Float)
    psych_safety_score = Column(Float)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    def to_dict(self):
        return {
            "overall_score": self.overall_score,
            "empathy_score": self.empathy_score,
            "psych_safety_score": self.psych_safety_score
        }

class SalesReport(db.Model):
    __tablename__ = 'sales_reports'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('practice_history.session_id'), nullable=False)
    rapport_building_score = Column(Float)
    value_articulation_score = Column(Float)
    objection_handling_score = Column(Float)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    def to_dict(self):
        return {
            "rapport_building_score": self.rapport_building_score,
            "value_articulation_score": self.value_articulation_score,
            "objection_handling_score": self.objection_handling_score
        }

class LearningPlan(db.Model):
    __tablename__ = 'learning_plans'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), ForeignKey('practice_history.session_id'), nullable=False)
    skill_focus_areas = Column(Text) # Stored as comma-separated string or JSON string
    practice_suggestions = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    def to_dict(self):
        return {
            "skill_focus_areas": self.skill_focus_areas,
            "practice_suggestions": self.practice_suggestions
        }

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def init_db(app):
    """Initialize the database with the Flask app context."""
    db.init_app(app)
    with app.app_context():
        db.create_all()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_history(user_id):
    """Get all practice sessions for a specific user, ordered by date."""
    return PracticeHistory.query.filter_by(user_id=user_id).order_by(PracticeHistory.date.desc()).all()

def get_session_by_id(session_id):
    return PracticeHistory.query.get(session_id)

def create_user(data):
    """Create a new user in the database."""
    # Check if exists
    if User.query.filter((User.email == data['email']) | (User.username == data.get('username'))).first():
        return None, "User already exists"
        
    new_user = User(
        username=data.get('username'),
        email=data['email'],
        password_hash=data['password'],
        full_name=data.get('full_name'),
        role=data.get('role', 'user')
    )
    db.session.add(new_user)
    db.session.commit()
    return new_user, None

def create_session(session_id, data, user_id=None):
    """Create a new session record."""
    new_session = PracticeHistory(
        session_id=session_id,
        user_id=user_id, # Link to logged-in user
        scenario_type=data.get("scenario_type", "custom"),
        role=data.get("role"),
        ai_role=data.get("ai_role"),
        transcript=data.get("transcript", []),
        report_data={},
        completed=False
    )
    db.session.add(new_session)
    db.session.commit()
    return new_session

def update_session(session_id, data):
    """Update an existing session with new transcript/status."""
    session = PracticeHistory.query.get(session_id)
    if session:
        if "transcript" in data:
            session.transcript = data["transcript"]
        if "report_data" in data:
            session.report_data = data["report_data"]
        if "status" in data:
            session.completed = (data["status"] == "completed")
        
        db.session.commit()

def save_report_metrics(session_id, report_type, metrics):
    """Save specific report metrics to corresponding tables."""
    try:
        if report_type == "coaching":
            # Delete existing if any (simplest update strategy)
            CoachingReport.query.filter_by(session_id=session_id).delete()
            report = CoachingReport(
                session_id=session_id,
                overall_score=metrics.get("overall_score"),
                empathy_score=metrics.get("empathy_score"),
                psych_safety_score=metrics.get("psych_safety_score")
            )
            db.session.add(report)
            
        elif report_type == "sales":
            SalesReport.query.filter_by(session_id=session_id).delete()
            report = SalesReport(
                session_id=session_id,
                rapport_building_score=metrics.get("rapport_building_score"),
                value_articulation_score=metrics.get("value_articulation_score"),
                objection_handling_score=metrics.get("objection_handling_score")
            )
            db.session.add(report)
            
        elif report_type == "learning":
            LearningPlan.query.filter_by(session_id=session_id).delete()
            report = LearningPlan(
                session_id=session_id,
                skill_focus_areas=json.dumps(metrics.get("skill_focus_areas", [])),
                practice_suggestions=json.dumps(metrics.get("practice_suggestions", []))
            )
            db.session.add(report)
            
        db.session.commit()
        print(f"✅ Saved {report_type} report metrics for session {session_id}")
    except Exception as e:
        print(f"❌ Error saving report metrics: {e}")
        db.session.rollback()

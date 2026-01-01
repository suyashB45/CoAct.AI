from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text
import datetime as dt
import uuid

db = SQLAlchemy()

class SessionModel(db.Model):
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=dt.datetime.now)
    role = Column(String)
    ai_role = Column(String)
    scenario = Column(Text)
    transcript = Column(JSONB, default=list)  # Stores list of messages
    report_data = Column(JSONB, default=dict) # Stores the analysis/report
    completed = Column(Boolean, default=False)
    framework = Column(String)  # or JSONB if it's a list
    report_file = Column(String)
    
    # We can store extra meta here if needed
    meta = Column(JSONB, default=dict)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "role": self.role,
            "ai_role": self.ai_role,
            "scenario": self.scenario,
            # "transcript": self.transcript, # Usually too large for list view
            "completed": self.completed,
            "report_file": self.report_file,
            "framework": self.framework,
            "fit_score": self.report_data.get("meta", {}).get("fit_score", 0) if self.report_data else 0
        }

class QuestionModel(db.Model):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    framework = Column(String)
    stage = Column(String)
    question = Column(Text)
    
    # We might want to store embedding here later, but for now just the text data
    # embedding = Column(JSON) 

    def to_dict(self):
        return {
            "id": self.id,
            "framework": self.framework,
            "stage": self.stage,
            "question": self.question
        }

class ScenarioModel(db.Model):
    __tablename__ = 'scenarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String)
    ai_role = Column(String, nullable=False)
    ai_role_short = Column(String)
    user_role = Column(String, nullable=False)
    scenario_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    icon_name = Column(String) # Store icon name string, frontend will map it

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ai_role": self.ai_role,
            "ai_role_short": self.ai_role_short,
            "user_role": self.user_role,
            "scenario": self.scenario_text,
            "category": self.category,
            "icon": self.icon_name
        }

import json
import os
from app import app
from database import db, QuestionModel

def sync_questions():
    """
    Syncs the contents of framework_questions.json to the 'questions' table in the database.
    This replaces all existing data in the table.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, "framework_questions.json")

    if not os.path.exists(data_file):
        print(f"❌ Error: {data_file} not found.")
        return

    print(f"Reading {data_file}...")
    with open(data_file, "r") as f:
        data = json.load(f)

    with app.app_context():
        try:
            # 1. Clear existing data
            print("Clearing existing questions from database...")
            num_deleted = db.session.query(QuestionModel).delete()
            print(f"Deleted {num_deleted} existing rows.")

            # 2. Insert new data
            print(f"Inserting {len(data)} new questions...")
            for item in data:
                question = QuestionModel(
                    framework=item.get("framework"),
                    stage=item.get("stage"),
                    question=item.get("question")
                )
                db.session.add(question)
            
            # 3. Commit
            db.session.commit()
            print("✅ Database sync complete!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error syncing to database: {e}")
            raise e

if __name__ == "__main__":
    sync_questions()

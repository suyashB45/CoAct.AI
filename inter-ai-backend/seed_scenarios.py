import json
from app import app
from database import db, ScenarioModel

# Data extracted from Practice.tsx
SCENARIOS = [
    {
        "category": "Change Management",
        "scenarios": [
            {
                "title": "Legacy Plan Migration",
                "description": "Upsell a resistant customer.",
                "ai_role": "Stubborn Customer who has been on a cheap legacy plan for years. They refuse to pay more, don't care about new features, and feel the company is betraying loyalty.",
                "ai_role_short": "Stubborn Customer",
                "user_role": "Sales Rep",
                "scenario": "You are calling a loyal customer to inform them their $45/month legacy plan is being retired. They must move to a new $60/month plan. The customer is happy with what they have and will resist any price increase aggressively.",
                "icon": "DollarSign",
            },
            {
                "title": "Process Change Resistance",
                "description": "Implement new software.",
                "ai_role": "'Sarah', a veteran graphic designer of 8 years. She loves ease and speed, hates complex tools, and thinks the new process is a waste of time.",
                "ai_role_short": "Sarah (Veteran Designer)",
                "user_role": "Team Manager",
                "scenario": "You need to tell Sarah that starting next week, all design submissions must go through 'ProjectFlow', a complex new management tool, instead of just emailing attachments. She will argue that email is faster and works fine.",
                "icon": "UserCog",
            },
            {
                "title": "Remote Policy Pushback",
                "description": "Enforce core hours.",
                "ai_role": "'Mike', a talented remote developer. He is a night owl, productive, but fiercely protective of his flexible schedule and autonomy.",
                "ai_role_short": "Mike (Remote Dev)",
                "user_role": "HR Manager",
                "scenario": "You are introducing a new company policy requiring all remote workers to be logged in between 10 AM and 3 PM. Mike works best late at night and will argue that this arbitrary rule will hurt his productivity.",
                "icon": "Users",
            },
            {
                "title": "Role Restructuring",
                "description": "Change job responsibilities.",
                "ai_role": "'David', a social media specialist. He loves creative work and hates technical writing. He feels this change is a 'bait and switch' from his original job.",
                "ai_role_short": "David (Social Media)",
                "user_role": "Head of Marketing",
                "scenario": "Due to team restructuring, you must tell David that 50% of his role will now involve writing technical white papers. He was hired for social media and will resist doing work he dislikes and wasn't hired for.",
                "icon": "Briefcase",
            },
            {
                "title": "Training Skeptic",
                "description": "Mandate new workflow.",
                "ai_role": "'Alex', a top-performing sales employee. They are arrogant because of their results and believe their own method is superior to your 'corporate script'.",
                "ai_role_short": "Alex (Top Performer)",
                "user_role": "Corporate Trainer",
                "scenario": "You just presented a mandatory new 5-step client call workflow. Alex interrupts to say they are already hitting targets with their own style and shouldn't have to change what works.",
                "icon": "Presentation",
            },
        ]
    }
]

def seed_scenarios():
    with app.app_context():
        print("🌱 Seeding scenarios...")
        
        # Clear existing scenarios to avoid duplicates on re-run
        try:
            db.session.query(ScenarioModel).delete()
            print("Cleared existing scenarios.")
        except Exception as e:
            print(f"Error clearing table (maybe didn't exist): {e}")

        count = 0
        for category_group in SCENARIOS:
            cat_name = category_group["category"]
            for item in category_group["scenarios"]:
                scenario = ScenarioModel(
                    title=item["title"],
                    description=item["description"],
                    ai_role=item["ai_role"],
                    ai_role_short=item["ai_role_short"],
                    user_role=item["user_role"],
                    scenario_text=item["scenario"],
                    category=cat_name,
                    icon_name=item["icon"]
                )
                db.session.add(scenario)
                count += 1
        
        db.session.commit()
        print(f"✅ Successfully seeded {count} scenarios into the database.")

if __name__ == "__main__":
    seed_scenarios()

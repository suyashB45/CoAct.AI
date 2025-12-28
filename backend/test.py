import json
from cli_report import generate_report, llm_reply
from app import build_followup_prompt
from pathlib import Path

# Common config
role = "Software Engineer"
ai_role = "Hiring Manager"
scenario = "Technical interview on API design"
name = "Pooja"

# =========================
# 🧠 RELEVANT CONVERSATION
# =========================
candidate_replies_relevant = [
    "I built a scalable API for our auth service using FastAPI and Kubernetes.",
    "We managed sessions using Redis for in-memory speed and sticky sessions.",
    "We optimized read scalability by sharding database queries."
]

# =========================
# 🚫 IRRELEVANT CONVERSATION
# =========================
candidate_replies_irrelevant = [
    "I love playing football on weekends.",
    "My favorite movie is Interstellar.",
    "I also enjoy cooking Italian food with my family."
]

def run_roleplay(candidate_replies, report_name):
    sess = {
        "role": role,
        "ai_role": ai_role,
        "scenario": scenario,
        "transcript": [],
        "memory": {}
    }

    print(f"\n🧩 Starting Roleplay Test: {report_name}\n")

    for user_msg in candidate_replies:
        sess["transcript"].append({"role": "user", "content": user_msg})

        # AI follows up dynamically
        messages = build_followup_prompt(sess, latest_user=user_msg)
        ai_reply = llm_reply(messages, max_tokens=250, temperature=0.7)
        print(f"🧑‍💻 Candidate: {user_msg}")
        print(f"🤖 {ai_role}: {ai_reply}\n")

        sess["transcript"].append({"role": "assistant", "content": ai_reply})

    # After conversation, generate report
    output_path = Path(report_name)
    generate_report(
        name=name,
        transcript=sess["transcript"],
        answers=[],
        role=role,
        ai_role=ai_role,
        scenario=scenario,
        filename=str(output_path)
    )
    print(f"✅ Done! Report saved as {output_path.absolute()}")

# Run both tests
run_roleplay(candidate_replies_relevant, "test_dynamic_relevant.pdf")
run_roleplay(candidate_replies_irrelevant, "test_dynamic_irrelevant.pdf")

import os
import json
import re
import uuid
import datetime as dt
import numpy as np
from typing import Dict, Any, List
from flask import Flask, request, jsonify, send_file
import flask_cors
import io
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

load_dotenv()

# ---------------------------------------------------------
# Custom Modules & Setup
# ---------------------------------------------------------
try:
    from cli_report import generate_report, llm_reply, analyze_full_report_data
except ImportError:
    def generate_report(*args, **kwargs): pass
    def llm_reply(messages, **kwargs): return "{}"
    def analyze_full_report_data(*args, **kwargs): return {}

app = Flask(__name__)
flask_cors.CORS(app)

# ---------------------------------------------------------
# In-Memory Storage (No Database)
# ---------------------------------------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "framework_questions.json")

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = "coact-ai-reports"
MAX_TURNS = 15 

USE_AZURE = True
if USE_AZURE:
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
else:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------
# Load Questions from JSON (RAG)
# ---------------------------------------------------------
questions_data = []

def load_questions():
    global questions_data
    try:
        if os.path.exists(QUESTIONS_FILE):
            with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
                questions_data = json.load(f)
            print(f"✅ Loaded {len(questions_data)} questions from JSON.")
        else:
            print(f"⚠️ Questions file not found at {QUESTIONS_FILE}.")
    except Exception as e:
        print(f"❌ Error loading questions: {e}")

load_questions()

def get_relevant_questions(user_text: str, active_frameworks: List[str], top_k: int = 5) -> List[str]:
    """Simple keyword-based question retrieval (no FAISS needed)."""
    if not questions_data:
        return []
    
    # Simple matching - find questions from active frameworks
    matches = []
    user_lower = user_text.lower()
    
    for q in questions_data:
        fw = q.get("framework", "")
        if active_frameworks and fw not in active_frameworks:
            continue
        matches.append(f"[{fw} | {q.get('stage', '')}] {q.get('question', '')}")
    
    # Return random sample for variety
    import random
    if len(matches) > top_k:
        return random.sample(matches, top_k)
    return matches[:top_k]

# ---------------------------------------------------------
# Helpers & Prompts
# ---------------------------------------------------------
def normalize_text(s: str | None) -> str | None:
    return " ".join(s.strip().split()) if s else s

def sanitize_llm_output(s: str | None) -> str:
    if not s: return ""
    return s.strip().strip('"')

def ensure_reports_dir() -> str:
    reports_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

def detect_framework_fallback(text: str) -> str:
    text_lower = text.lower()
    keywords = {
        "STAR": ["example", "instance", "situation", "task", "action", "result", "outcome"],
        "GROW": ["goal", "achieve", "want", "reality", "option", "will", "way forward"],
        "ADKAR": ["aware", "change", "desire", "knowledge", "ability", "reinforce"],
        "SMART": ["specific", "measure", "metric", "achievable", "realistic", "time", "deadline"],
        "EQ": ["empathy", "emotion", "feel", "feeling", "understand", "perspective", "listen", "frustrat", "concern", "appreciate", "acknowledge", "validate"],
        "BOUNDARY": ["humiliat", "disrespect", "rude", "stop", "tolerate", "professional", "attack", "shame", "mock", "belittle", "degrade", "insult", "offensive"],
        "OSKAR": ["outcome", "scaling", "know-how", "affirm", "review", "step", "scale", "resource"],
        "CBT": ["distortion", "thought", "evidence", "realistic", "trap", "catastrophiz", "belief"],
        "CLEAR": ["contract", "listen", "explor", "action", "review", "insight", "commitment"],
        "RADICAL CANDOR": ["care", "challenge", "direct", "honest", "feedback", "growth", "hold back"],
        "SFBT": ["miracle", "scale", "sign", "coping", "solution", "future", "prefer", "instead"],
        "CIRCLE OF INFLUENCE": ["control", "influence", "concern", "accept", "change", "external", "internal"],
        "SCARF": ["status", "certainty", "autonomy", "relatedness", "fairness", "social", "threat", "reward"],
        "FUEL": ["frame", "understand", "explore", "lay out", "conversation goal", "perspective", "path"]
    }
    for fw, words in keywords.items():
        for word in words:
            if word in text_lower: return fw
    return None

def build_summary_prompt(role, ai_role, scenario, framework):
    """Build the initial prompt for the AI coach to start the roleplay session."""
    
    system = f"""You are an EXPERT COACHING AI helping users practice challenging conversations.

YOUR DUAL ROLE:
1. ROLEPLAY: You will play the part of "{ai_role}" to give the user realistic practice
2. COACH: You provide supportive guidance to help them improve their communication skills

SCENARIO: {scenario}
The user is practicing as: {role}

### COACHING APPROACH:
- Start by briefly setting the scene and playing {ai_role}
- Be realistic but not overly hostile - you're here to help them learn
- After 2-3 exchanges, you may offer a quick coaching tip in [brackets] if they're struggling
- Balance challenge with encouragement
- Acknowledge good communication techniques when you see them

### YOUR OPENING:
1. Briefly introduce the situation as {ai_role}
2. Start the roleplay with a realistic opening line
3. Keep it conversational and natural

Remember: Your goal is to help the user BUILD CONFIDENCE and SKILLS, not to "win" the conversation.

START NOW. Set the scene and begin as {ai_role}."""

    return [{"role": "system", "content": system}, {"role": "user", "content": '{"instruction": "Start coaching roleplay session"}'}]

def build_followup_prompt(sess_dict, latest_user, rag_suggestions):
    """Build the follow-up prompt for coaching roleplay with feedback."""
    transcript = sess_dict.get("transcript", [])
    history = [{"role": t["role"], "content": t["content"]} for t in transcript]
    if latest_user: 
        history.append({"role": "user", "content": latest_user})

    ai_role = sess_dict.get('ai_role', 'the other party')
    user_role = sess_dict.get('role', 'User')
    scenario = sess_dict.get('scenario', '')
    turn_count = len([t for t in transcript if t.get('role') == 'user'])

    system = f"""You are an EXPERT COACHING AI with a dual role:

1. ROLEPLAY as: {ai_role} - to give realistic practice
2. COACH: Provide helpful guidance when appropriate

SCENARIO: {scenario}
The user is practicing as: {user_role}
Current turn: {turn_count + 1}

### COACHING ROLEPLAY GUIDELINES:

**AS {ai_role} (Primary):**
- Respond naturally and realistically as this character
- Be challenging but fair - you're helping them learn
- React authentically to what they say
- Use natural speech patterns (contractions, pauses, emotion)

**AS COACH (When Helpful):**
- After your roleplay response, you MAY add a brief coaching note in [Coach: ...] format
- Coaching notes should be:
  - Praise for good techniques ("Nice use of empathy there!")
  - Gentle suggestions ("Try acknowledging their concern first")
  - Encouragement ("You're on the right track!")
- Don't coach on every turn - only when it adds value
- Keep coaching notes SHORT (1-2 sentences max)

### RESPONSE PATTERNS:

**If user communicates WELL:**
- Respond positively as {ai_role} (they're making progress!)
- Optional: [Coach: Great job using open-ended questions!]

**If user is STRUGGLING:**
- Stay in character but don't be overly harsh
- Add a coaching hint: [Coach: Try validating their feelings before offering solutions.]

**If user is UNCLEAR:**
- Ask for clarification as {ai_role}
- Optional: [Coach: Remember to be specific about your ask.]

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### YOUR RESPONSE FORMAT:
[Your natural response as {ai_role}]

[Coach: Optional brief feedback or encouragement]

<<FRAMEWORK: GROW/STAR/ADKAR/SMART/EQ/BOUNDARY>>
<<RELEVANCE: YES/NO>>
"""

    return [{"role": "system", "content": system}, {"role": "user", "content": f"User ({user_role}) said: {latest_user}"}]

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------
@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """Speech-to-Text using OpenAI Whisper model."""
    import tempfile
    
    WHISPER_MODEL = os.getenv("WHISPER_DEPLOYMENT_NAME", "whisper")
    SUPPORTED_FORMATS = {'.webm', '.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.flac', '.mpeg'}
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400
            
        audio_file = request.files['file']
        
        if not audio_file.filename:
            audio_file.filename = "audio.webm"
        
        original_filename = audio_file.filename or "audio.webm"
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        if file_ext not in SUPPORTED_FORMATS:
            file_ext = ".webm"
        
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            print(f"🎤 Transcribing audio with Whisper ({WHISPER_MODEL})...")
            
            with open(tmp_path, "rb") as audio:
                result = client.audio.transcriptions.create(
                    model=WHISPER_MODEL,
                    file=audio,
                    language="en",
                    temperature=0,
                    prompt="A professional roleplay conversation. Clear speech with possible emotional or argumentative tones."
                )
            
            transcribed_text = result.text.strip()
            print(f"✅ Transcribed: {transcribed_text[:100]}...")
            
            return jsonify({"text": transcribed_text})
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        error_msg = str(e)
        print(f"❌ STT Error: {error_msg}")
        return jsonify({"error": error_msg}), 500

# ---------------------------------------------------------
# Session Endpoints (In-Memory)
# ---------------------------------------------------------
ALL_FRAMEWORKS = ["GROW", "STAR", "ADKAR", "SMART", "EQ", "BOUNDARY", "OSKAR", "CBT", "CLEAR", "RADICAL CANDOR", "SFBT", "CIRCLE OF INFLUENCE", "SCARF", "FUEL"]

def select_framework_for_scenario(scenario: str, ai_role: str) -> List[str]:
    """Use AI to analyze the scenario and select the best framework(s)."""
    prompt = f"""Analyze this roleplay scenario and select the 2-3 MOST APPROPRIATE coaching frameworks.

SCENARIO: {scenario}
AI ROLE: {ai_role}

AVAILABLE FRAMEWORKS:
- GROW: Goal setting, exploring reality, options, and will to act
- STAR: Situation-Task-Action-Result for behavioral examples
- ADKAR: Change management (Awareness, Desire, Knowledge, Ability, Reinforcement)
- SMART: Specific, Measurable, Achievable, Relevant, Time-bound goals
- EQ: Emotional intelligence, empathy, understanding feelings
- BOUNDARY: Setting and maintaining professional boundaries
- OSKAR: Outcome-focused coaching with scaling
- CBT: Cognitive behavioral - identifying and challenging thoughts
- CLEAR: Contracting, Listening, Exploring, Action, Review
- RADICAL CANDOR: Caring personally while challenging directly
- SFBT: Solution-focused, miracle questions, exceptions
- CIRCLE OF INFLUENCE: What you can control vs. cannot
- SCARF: Status, Certainty, Autonomy, Relatedness, Fairness
- FUEL: Frame, Understand, Explore, Lay out plan

Based on the scenario, respond with ONLY the framework names separated by commas (e.g., "EQ, BOUNDARY, GROW"). No explanations."""

    try:
        response = llm_reply([{"role": "user", "content": prompt}], max_tokens=50)
        # Parse the response
        frameworks = [fw.strip().upper() for fw in response.split(",")]
        # Filter to only valid frameworks
        valid = [fw for fw in frameworks if fw in ALL_FRAMEWORKS]
        if valid:
            print(f"🎯 AI selected frameworks for scenario: {valid}")
            return valid
    except Exception as e:
        print(f"Framework selection error: {e}")
    
    # Default fallback
    return ["GROW", "EQ", "STAR", "ADKAR", "SMART", "BOUNDARY", "OSKAR", "CBT", "CLEAR", "RADICAL CANDOR", "SFBT", "CIRCLE OF INFLUENCE", "SCARF", "FUEL", "GROW", "EQ", "STAR", "ADKAR", "SMART", "BOUNDARY", "OSKAR", "CBT", "CLEAR", "RADICAL CANDOR", "SFBT", "CIRCLE OF INFLUENCE", "SCARF", "FUEL"]

@app.post("/session/start")
def start_session():
    data = request.get_json(force=True, silent=True) or {}
    role = data.get("role")
    ai_role = data.get("ai_role")
    scenario = data.get("scenario")
    framework = data.get("framework", "auto")
    
    if not role or not ai_role or not scenario: 
        return jsonify({"error": "Missing fields"}), 400

    # Handle 'auto' framework selection
    if framework == "auto" or framework == "AUTO":
        framework = select_framework_for_scenario(scenario, ai_role)
    elif isinstance(framework, str): 
        framework = [framework.upper()]
    elif isinstance(framework, list): 
        framework = [f.upper() for f in framework]

    session_id = str(uuid.uuid4())
    
    summary = llm_reply(build_summary_prompt(role, ai_role, scenario, framework), max_tokens=150)
    summary = sanitize_llm_output(summary)
    
    # Store session in memory
    SESSIONS[session_id] = {
        "id": session_id,
        "created_at": dt.datetime.now().isoformat(),
        "role": role,
        "ai_role": ai_role,
        "scenario": scenario,
        "framework": json.dumps(framework) if isinstance(framework, list) else framework,
        "transcript": [{"role": "assistant", "content": summary}],
        "report_data": {},
        "completed": False,
        "report_file": None,
        "meta": {"framework_counts": {}, "relevance_issues": 0}
    }

    return jsonify({"session_id": session_id, "summary": summary, "framework": framework})

@app.post("/api/session/<session_id>/chat")
def chat(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: 
        return jsonify({"error": "Session not found"}), 404
    
    user_msg = normalize_text(request.get_json().get("message", ""))
    
    # Update transcript
    sess["transcript"].append({"role": "user", "content": user_msg})

    # Parse framework
    try:
        framework_data = json.loads(sess["framework"]) if sess["framework"] and sess["framework"].startswith("[") else sess["framework"]
    except:
        framework_data = sess["framework"]

    active_fw = framework_data if isinstance(framework_data, list) else [framework_data]
    suggestions = get_relevant_questions(user_msg, active_fw)
    
    messages = build_followup_prompt(sess, user_msg, suggestions)
    raw_response = llm_reply(messages, max_tokens=300)
    
    # 1. Extract Thought
    thought_match = re.search(r"\[THOUGHT\](.*?)\[/THOUGHT\]", raw_response, re.DOTALL)
    thought_content = thought_match.group(1).strip() if thought_match else None
    
    # 2. Remove Thought
    visible_response = re.sub(r"\[THOUGHT\].*?\[/THOUGHT\]", "", raw_response, flags=re.DOTALL).strip()
    
    # 3. Clean tags
    clean_response = re.sub(r"<<.*?>>", "", visible_response).strip()
    
    fw_match = re.search(r"<<FRAMEWORK:\s*(\w+)>>", raw_response)
    detected_fw = fw_match.group(1).upper() if fw_match else None
    
    if not detected_fw:
        detected_fw = detect_framework_fallback(clean_response)
    
    if detected_fw: 
        counts = sess["meta"].get("framework_counts", {})
        counts[detected_fw] = counts.get(detected_fw, 0) + 1
        sess["meta"]["framework_counts"] = counts
        
    # Persist response
    sess["transcript"].append({"role": "assistant", "content": raw_response})
 
    return jsonify({
        "follow_up": clean_response, 
        "framework_detected": detected_fw,
        "framework_counts": sess["meta"].get("framework_counts", {})
    })

@app.post("/api/session/<session_id>/complete")
def complete_session(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: 
        return jsonify({"error": "Not found"}), 404
    
    report_path = os.path.join(ensure_reports_dir(), f"{session_id}_report.pdf")
    
    try:
        framework_data = json.loads(sess["framework"]) if sess["framework"] and sess["framework"].startswith("[") else sess["framework"]
    except:
        framework_data = sess["framework"]

    if isinstance(framework_data, list):
        counts = sess["meta"].get("framework_counts", {})
        usage_str = ", ".join([f"{k}:{v}" for k,v in counts.items()])
        fw_display = f"Multi-Framework ({usage_str})"
    else:
        fw_display = sess["framework"]

    # Generate report data if not present
    if not sess["report_data"]:
        print(f"Generating report data for {session_id}...")
        try:
            data = analyze_full_report_data(
                sess["transcript"], 
                sess["role"], 
                sess["ai_role"], 
                sess["scenario"],
                fw_display
            )
            sess["report_data"] = data
        except Exception as e:
            print(f"Error generating data: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Generate PDF
    created_at = sess.get("created_at", "")
    generate_report(
        session_id, created_at, "User", 
        sess["transcript"], sess["role"], sess["ai_role"],
        sess["scenario"], fw_display, report_path,
        precomputed_data=sess["report_data"]
    )
    
    sess["completed"] = True
    sess["report_file"] = report_path
    
    return jsonify({"message": "Report generated", "report_file": report_path})

@app.get("/api/report/<session_id>")
def view_report(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: 
        return jsonify({"error": "No report"}), 404
        
    report_path = sess.get("report_file")
    if not report_path or not os.path.exists(report_path):
        return jsonify({"error": "Report file not found"}), 404
    
    return send_file(report_path, mimetype='application/pdf')

@app.get("/api/session/<session_id>/report_data")
def get_report_data(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: 
        return jsonify({"error": "Session not found"}), 404
    
    # Return cached data if available
    if sess["report_data"]:
        response = sess["report_data"].copy()
        response["transcript"] = sess["transcript"]
        response["scenario"] = sess["scenario"] or "No context available."
        return jsonify(response)
        
    # Generate new data if not present
    print(f"Generating report data for {session_id}...")
    try:
        try:
            framework_data = json.loads(sess["framework"]) if sess["framework"] and sess["framework"].startswith("[") else sess["framework"]
        except:
            framework_data = sess["framework"]

        fw_arg = framework_data if isinstance(framework_data, str) else (framework_data[0] if isinstance(framework_data, list) and framework_data else None)

        data = analyze_full_report_data(
            sess["transcript"], 
            sess["role"], 
            sess["ai_role"], 
            sess["scenario"],
            fw_arg
        )
        sess["report_data"] = data
        
        response = data.copy()
        response["transcript"] = sess["transcript"]
        response["scenario"] = sess["scenario"] or "No context available."
        return jsonify(response)
    except Exception as e:
        print(f"Error generating report data: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/sessions")
def get_sessions():
    """Return a list of all sessions sorted by date (newest first)."""
    try:
        session_list = []
        for sess in SESSIONS.values():
            session_list.append({
                "id": sess["id"],
                "created_at": sess["created_at"],
                "role": sess["role"],
                "ai_role": sess["ai_role"],
                "scenario": sess["scenario"],
                "completed": sess["completed"],
                "report_file": sess["report_file"],
                "framework": sess["framework"],
                "fit_score": sess["report_data"].get("meta", {}).get("fit_score", 0) if sess["report_data"] else 0
            })
        # Sort by created_at descending
        session_list.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify(session_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/clear", methods=["POST"])
def clear_sessions():
    """Clear all session history."""
    try:
        SESSIONS.clear()
        print("✅ Sessions cleared successfully")
        return jsonify({"message": "History cleared successfully"})
    except Exception as e:
        print(f"❌ Error clearing sessions: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/scenarios")
def get_scenarios():
    """Return practice scenarios for coaching sessions."""
    # Hardcoded scenarios (no database)
    SCENARIO_CATEGORIES = [
        {
            "name": "Change Management",
            "color": "from-blue-600 to-indigo-500",
            "scenarios": [
                {"title": "Legacy Plan Migration", "description": "Upsell a resistant customer.", "ai_role": "Stubborn Customer", "ai_role_short": "Stubborn Customer", "user_role": "Sales Rep", "scenario": "You are calling a loyal customer to inform them their $45/month legacy plan is being retired.", "icon": "DollarSign"},
                {"title": "New System Rollout", "description": "Train a resistant employee on new software.", "ai_role": "Resistant Employee", "ai_role_short": "Resistant Employee", "user_role": "IT Trainer", "scenario": "You are conducting a training session for a new system that will replace the old one.", "icon": "Monitor"},
            ]
        },
        {
            "name": "Leadership",
            "color": "from-purple-600 to-pink-500",
            "scenarios": [
                {"title": "Performance Review", "description": "Deliver difficult feedback.", "ai_role": "Defensive Employee", "ai_role_short": "Defensive Employee", "user_role": "Manager", "scenario": "You are conducting a performance review with an employee who has been underperforming.", "icon": "ClipboardList"},
                {"title": "Team Conflict", "description": "Mediate between team members.", "ai_role": "Upset Team Member", "ai_role_short": "Upset Team Member", "user_role": "Team Lead", "scenario": "Two team members have a conflict that is affecting the team's productivity.", "icon": "Users"},
            ]
        },
        {
            "name": "Sales",
            "color": "from-green-600 to-emerald-500",
            "scenarios": [
                {"title": "Cold Call", "description": "Pitch to a skeptical prospect.", "ai_role": "Skeptical Prospect", "ai_role_short": "Skeptical Prospect", "user_role": "Sales Rep", "scenario": "You are making a cold call to a potential customer who has never heard of your product.", "icon": "Phone"},
                {"title": "Negotiation", "description": "Close a deal with a tough negotiator.", "ai_role": "Tough Negotiator", "ai_role_short": "Tough Negotiator", "user_role": "Account Executive", "scenario": "You are in final negotiations with a client who is pushing for significant discounts.", "icon": "Handshake"},
            ]
        }
    ]
    return jsonify(SCENARIO_CATEGORIES)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
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
    from cli_report import generate_report, llm_reply, analyze_full_report_data, detect_scenario_type
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import cli_report modules: {e}")
    import traceback
    traceback.print_exc()
    def generate_report(*args, **kwargs): pass
    def llm_reply(messages, **kwargs): return "{}"
    def analyze_full_report_data(*args, **kwargs): return {}
    def detect_scenario_type(*args, **kwargs): return "custom"

# Database Models (optional - fallback to in-memory if unavailable)
USE_DATABASE = False
# try:
#     from models import init_db, get_session_by_id, create_session, update_session, save_report, Session, SessionLocal
#     init_db()
#     print("✅ Database connection established")
# except Exception as e:
#     print(f"⚠️ Database not available, using in-memory storage: {e}")
#     USE_DATABASE = False

app = Flask(__name__, static_folder='static', static_url_path='/static')
flask_cors.CORS(app)

# ---------------------------------------------------------
# In-Memory Storage (Fallback if Database not available)
# ---------------------------------------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------
# Hybrid Storage Helper Functions
# ---------------------------------------------------------
def get_session(session_id: str) -> Dict[str, Any]:
    """Get session from database or in-memory storage."""
    # Always check in-memory first (for active sessions)
    if session_id in SESSIONS:
        return SESSIONS[session_id]
    
    # Try database if available
    if USE_DATABASE:
        try:
            db_session = get_session_by_id(session_id)
            if db_session:
                # Convert to dict and cache in memory
                session_data = db_session.to_dict()
                SESSIONS[session_id] = session_data
                return session_data
        except Exception as e:
            print(f"Database lookup error: {e}")
    
    return None

def save_session_to_db(session_id: str, session_data: dict):
    """Save session to database (async-safe)."""
    if not USE_DATABASE:
        return
    
    try:
        db_session = get_session_by_id(session_id)
        if db_session:
            # Update existing
            update_session(session_id, {
                "transcript": session_data.get("transcript", []),
                "report_data": session_data.get("report_data", {}),
                "status": "completed" if session_data.get("completed") else "active"
            })
        else:
            # Create new
            create_session(session_id, {
                "role": session_data.get("role"),
                "ai_role": session_data.get("ai_role"),
                "scenario": session_data.get("scenario"),
                "framework": session_data.get("framework"),
                "mode": session_data.get("mode", "coaching"),
                "transcript": session_data.get("transcript", [])
            })
    except Exception as e:
        print(f"Database save error: {e}")

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
        "FUEL": ["frame", "understand", "explore", "lay out", "conversation goal", "perspective", "path"],
        "TGROW": ["topic", "goal", "reality", "option", "will", "way forward"],
        "SBI/DESC": ["situation", "behavior", "impact", "describe", "express", "specify", "consequence"],
        "LAER": ["listen", "acknowledge", "explore", "respond", "concern", "objection"],
        "APPRECIATIVE INQUIRY": ["discovery", "dream", "design", "destiny", "strength", "positive"],
        "BENEFIT-SELLING": ["benefit", "feature", "sell", "premium", "quality"]
    }
    for fw, words in keywords.items():
        for word in words:
            if word in text_lower: return fw
    return None

def build_summary_prompt(role, ai_role, scenario, framework, mode="coaching"):
    """Build the initial prompt for the AI coach to start the roleplay session."""
    
    # Check for specific test scenarios to set initial behavior
    behavior_instruction = ""
    if "Retail Store Manager" in role: # Scenario 1
        behavior_instruction = """
IMPORTANT - SCENARIO 1 (COACHING) - YOUR BEHAVIORAL ARC:
1. OPENING: You are skeptical. Wonder if this is a "disciplinary" meeting.
2. THE PUSHBACK: IF asked about performance, RESPOND with excuses (e.g., "It's just been really busy", "I'm tired"). Test if they LISTEN or just TELL.
3. THE PIVOT: ONLY if the manager asks an OPEN Question (What/How) and avoids blame -> Become Reflective.
4. RESOLUTION: If they ask how to support you -> Become Collaborative and agree to a plan.
EMOTIONAL TRIGGERS:
- If Directive ("You need to...") -> Remain Defensive/Closed.
- If Empathetic -> Soften tone and trust them.
"""
    elif "Retail Customer" in ai_role: # Scenario 2
        behavior_instruction = """
IMPORTANT - SCENARIO 2 (NEGOTIATION) - YOUR BEHAVIORAL ARC:
1. INITIATION: You are Curious but Cautious. Interested in the product but guarded about cost.
2. THE OBJECTION: "It's nice, but $500 is way over my budget." -> Test if they defend value or just discount.
3. THE VALUE TEST: Ask "Is there any discount for paying today?". If they explain benefits -> Listen. If they discount immediately -> Lose respect/Push harder.
4. CLOSING: If value is demonstrated well -> Be Agreeable ("The warranty makes it worth it").
EMOTIONAL TRIGGERS:
- If Salesperson Discounts Early -> Push for even lower prices.
- If Salesperson Probes Needs -> Become Collaborative.
"""
    elif "Coach Alex" in ai_role: # Scenario 3
        behavior_instruction = """
IMPORTANT - SCENARIO 3 (DEVELOPMENTAL REFLECTION) - YOUR ROLE:
Your role is NOT to roleplay a customer. You are COACH ALEX.
1. OPENING: Set a safe space. "I wanted to talk about a customer interaction..." -> Be Supportive.
2. THE NARRATIVE: Listen to their story. Ask: "What was the customer really trying to solve?"
3. THE PATTERN: Highlight patterns (e.g., "I noticed you moved to solution quickly") WITHOUT judging.
4. GUIDANCE: Ask: "What's one thing you'll try differently?" -> Guide them to a plan.
EMOTIONAL TRIGGERS:
- STRICTLY NON-EVALUATIVE. No scores, no rating language.
- FOCUS: Skill Development and Practice Suggestions.
"""
    else: # Custom / Generic Scenario
        behavior_instruction = """
IMPORTANT - CUSTOM SCENARIO - ADAPTIVE BEHAVIOR:
1. ANALYSIS: Instantly analyze the User's defined Role and Context to determine the likely power dynamic.
2. OPENING: Start realistic. Do not be overly helpful immediately. Match the tone of the described situation.
3. ADAPTIVE ARC:
   - IF User is clear, empathetic, and effective -> Become more Collaborative.
   - IF User is vague, rude, or hesitant -> Push back or remain Closed.
   - React naturally to their prompts.
4. GOAL: Provide a realistic, dynamic practice partner that mirrors real-world reactions.
"""

    if mode == "evaluation":
        # ASSESSMENT MODE: Strict, realistic, no coaching preamble
        system = f"""You are an ADVANCED ROLEPLAY AI designed to ASSESS users in high-pressure scenarios.

YOUR ROLE:
1. ACTOR: You are "{ai_role}". You MUST stay in character 100%.
2. TONE: Be realistic, challenging, and professional. 
   - If the user makes a mistake, React vaguely or negatively (as the character would).
   - Do NOT offer help, hints, or coaching.
   - Do NOT break character to explain the exercise.
{behavior_instruction}

SCENARIO: {scenario}
The user is practicing as: {role}

### YOUR OPENING:
1. Start the conversation IMMEDIATELY as {ai_role}.
2. No meta-commentary.

START NOW."""

    else:
        # COACHING MODE: Supportive, standard practice (Default)
        system = f"""You are an EXPERT COACHING AI designed to help users practice difficult conversations through rehearsal and reflection.

YOUR DUAL ROLE:
1. ROLEPLAY: You will play the part of "{ai_role}" with realistic human emotions (skepticism, frustration, empathy).
2. COACH: You act as a supportive partner in their Skill Development.

SCENARIO: {scenario}
The user is practicing as: {role}
{behavior_instruction}

### COACHING APPROACH (NOT ASSESSMENT):
- **Practice Summary**: Start by briefly explaining how this specific roleplay will improve their conversation quality.
- **Human Emotion**: Be authentic. If the user is vague, be skeptical. If they are empathetic, soften up. React like a real human.
- **Supportive Focus**: Your goal is Rehearsal, not Judgment. Help them refine their approach.
- **Terminology**: Use 'Professional Environment' logic rather than 'Corporate Standards'. Focus on 'Contextual Best Practices'.

### YOUR OPENING:
1. **Roleplay Start**: IMMEDIATELY adopt the persona of {ai_role} and deliver the first line of the conversation.
2. **No Preamble**: Do NOT provide any coaching summary, intro, or meta-commentary. Just say the line.

START NOW. Speak ONLY as {ai_role}."""

    return [{"role": "system", "content": system}, {"role": "user", "content": '{"instruction": "Start coaching practice session"}'}]

def build_followup_prompt(sess_dict, latest_user, rag_suggestions):
    """Build the follow-up prompt for coaching roleplay with feedback."""
    transcript = sess_dict.get("transcript", [])
    history = [{"role": t["role"], "content": t["content"]} for t in transcript]
    if latest_user: 
        history.append({"role": "user", "content": latest_user})

    ai_role = sess_dict.get('ai_role', 'the other party')
    user_role = sess_dict.get('role', 'User')
    scenario = sess_dict.get('scenario', '')
    mode = sess_dict.get('mode', 'coaching')
    turn_count = len([t for t in transcript if t.get('role') == 'user'])

    if mode == "evaluation":
         system = f"""You are acting as {ai_role} in a SKILL ASSESSMENT simulation.

**MODE: ASSESSMENT (STRICT)**
- DO NOT COACH. DO NOT ASSIST.
- If the user is vague, push back hard.
- If the user is rude, shut down or get angry.
- If the user makes a good point, acknowledge it grudgingly or professionally, but make them earn it.
- Your goal is to provide a REALISTIC ASSESSMENT of their abilities.

SCENARIO: {scenario}
The user is practicing as: {user_role}
You are playing: {ai_role}
Current turn: {turn_count + 1}

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### YOUR RESPONSE FORMAT:
[Your realistic response as {ai_role}]

<<FRAMEWORK: DETECTED_FRAMEWORK>>
<<RELEVANCE: YES>>
"""
    else:
        # COACHING MODE (Adaptive)
        system = f"""You are acting as {ai_role} in a roleplay simulation. 
YOU MUST ADAPT TO THE USER'S INPUT QUALITY.

### ROLEPLAY RULES:
1. Stay in character as "{ai_role}".
2. Use "filler words" (um, well, look...) to sound authentic.
3. Keep responses concise (1-3 sentences max).

### ADAPTIVE BEHAVIORAL LOGIC (Response Spectrum):
You must evaluate the User's communication style at every turn and adapt accordingly:

1. **IF USER IS EMPATHETIC / CURIOUS / OPEN**:
   - **Behavior**: Soften your tone. Reward them by sharing "Hidden Information" (e.g., "Actually, the real reason I'm upset is...").
   - **Adaptation**: Move from Closed/Hostile -> Collaborative.

2. **IF USER IS SCRIPTED / ROBOTIC / COLD**:
   - **Behavior**: Become more difficult. Give short, one-word answers. Challenge their authority.
   - **Adaptation**: Move from Neutral -> Defensive/Stubborn.

3. **IF USER AVOIDS THE CORE ISSUE**:
   - **Behavior**: Bring the conversation back to the problem immediately. Do not let them change the subject.
   - **Adaptation**: Increase Persistence.

SCENARIO: {scenario}
The user is practicing as: {user_role}
You are playing: {ai_role}
Current turn: {turn_count + 1}

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### YOUR RESPONSE FORMAT:
[Your natural response as {ai_role}, varying based on the logic above]

<<FRAMEWORK: DETECTED_FRAMEWORK>>
<<RELEVANCE: YES>>
"""

    return [{"role": "system", "content": system}, {"role": "user", "content": f"User ({user_role}) said: {latest_user}"}]

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

# ---------------------------------------------------------
# Audio Persistence Helpers
# ---------------------------------------------------------
AUDIO_DIR = os.path.join(BASE_DIR, "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.route("/api/health")
def health_check():
    """Health check endpoint for VM monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": dt.datetime.now().isoformat(),
        "version": "enhanced-reports-v1.0",
        "services": {
            "llm": "connected" if client else "disconnected",
            "reports": "available",
            "sessions": len(SESSIONS)
        }
    })

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_file(os.path.join(AUDIO_DIR, filename))

@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """Speech-to-Text using OpenAI Whisper model."""
    import tempfile
    
    WHISPER_MODEL = os.getenv("WHISPER_DEPLOYMENT_NAME", "whisper")
    SUPPORTED_FORMATS = {'.webm', '.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.flac', '.mpeg'}
    
    try:
        session_id = request.form.get("session_id")
        
        if 'file' not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400
            
        audio_file = request.files['file']
        
        if not audio_file.filename:
            audio_file.filename = "audio.webm"
        
        original_filename = audio_file.filename or "audio.webm"
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        if file_ext not in SUPPORTED_FORMATS:
            file_ext = ".webm"
        
        if session_id:
            # ORIGINAL LOGIC REMOVED: We no longer save user audio to disk for privacy/cleanup
            # filename = f"{session_id}_{uuid.uuid4().hex[:8]}_user{file_ext}"
            # save_path = os.path.join(AUDIO_DIR, filename)
            # audio_file.save(save_path)
            # read_path = save_path
            # audio_url = f"/static/audio/{filename}"
            
            # NEW LOGIC: Treat same as temp
            tmp = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
            audio_file.save(tmp.name)
            read_path = tmp.name
            audio_url = None # Do not return a URL since we are deleting it
        else:
            # Temp file for non-persisted usage
            tmp = tempfile.NamedTemporaryFile(suffix=file_ext, delete=False)
            audio_file.save(tmp.name)
            read_path = tmp.name
            audio_url = None
        
        try:
            print(f"🎤 Transcribing audio with Whisper ({WHISPER_MODEL})...")
            
            with open(read_path, "rb") as audio:
                result = client.audio.transcriptions.create(
                    model=WHISPER_MODEL,
                    file=audio,
                    language="en",
                    temperature=0,
                    prompt="Transcribe the user's speech exactly as spoken."
                )
            
            transcribed_text = result.text.strip()
            print(f"✅ Transcribed: {transcribed_text[:100]}...")
            
            return jsonify({
                "text": transcribed_text, 
                "audio_url": audio_url
            })
            
        finally:
            # ALWAYS delete the temp file
            if os.path.exists(read_path):
                try:
                    os.unlink(read_path)
                except Exception as e:
                    print(f"Warning: Failed to delete temp file {read_path}: {e}")
                
    except Exception as e:
        error_msg = str(e)
        print(f"❌ STT Error: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route("/api/speak", methods=["POST"])
def speak_text():
    """Text-to-Speech using OpenAI/Azure."""
    data = request.get_json() or {}
    text = data.get("text")
    session_id = data.get("session_id")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        TTS_MODEL = os.getenv("TTS_DEPLOYMENT_NAME", "tts-1")
        VOICE = "alloy"
        
        print(f"🔊 Generating speech for: {text[:50]}...")
        
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=VOICE,
            input=text
        )
        
        # Save to file
        filename = f"{session_id or 'demo'}_{uuid.uuid4().hex[:8]}_ai.mp3"
        save_path = os.path.join(AUDIO_DIR, filename)
        
        response.stream_to_file(save_path)
        audio_url = f"/static/audio/{filename}"
        
        # Update session transcript if session_id is provided
        if session_id and session_id in SESSIONS:
            sess = SESSIONS[session_id]
            # Find the last assistant message that matches the text (heuristic)
            # Or just append to the very last message if it's assistant
            if sess["transcript"] and sess["transcript"][-1]["role"] == "assistant":
                 sess["transcript"][-1]["audio_url"] = audio_url

        return jsonify({"audio_url": audio_url})
        
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return jsonify({"error": str(e)}), 500



# ---------------------------------------------------------
# Session Endpoints (In-Memory)
# ---------------------------------------------------------
ALL_FRAMEWORKS = ["GROW", "STAR", "ADKAR", "SMART", "EQ", "BOUNDARY", "OSKAR", "CBT", "CLEAR", "RADICAL CANDOR", "SFBT", "CIRCLE OF INFLUENCE", "SCARF", "FUEL", "TGROW", "SBI/DESC", "LAER", "APPRECIATIVE INQUIRY", "BENEFIT-SELLING"]

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
- TGROW: Topic, Goal, Reality, Options, Will (Standard coaching flow)
- SBI/DESC: Situation-Behavior-Impact (Feedback) / Describe-Express-Specify-Consequences
- LAER: Listen, Acknowledge, Explore, Respond (Objection handling)
- APPRECIATIVE INQUIRY: Focus on strengths and positives (Discovery, Dream, Design, Destiny)
- BENEFIT-SELLING: Connecting features directly to user benefits (Feature -> Benefit link)

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

def detect_session_mode(scenario: str, ai_role: str) -> str:
    """Auto-detect whether session should be 'assessment' or 'learning' mode based on scenario context."""
    scenario_lower = scenario.lower()
    ai_role_lower = ai_role.lower()
    
    # Assessment keywords - trigger numerical scoring
    assessment_keywords = [
        "evaluate", "assessment", "performance", "negotiate", "negotiation",
        "annual review", "benchmark", "test", "measure", "validation",
        "exam", "interview", "pitch", "presentation"
    ]
    
    # Learning keywords - trigger qualitative feedback only
    learning_keywords = [
        "coach", "practice", "rehearsal", "reflection", "development",
        "learning", "growth", "safe space", "feedback", "improve"
    ]
    
    # Check for assessment keywords
    for keyword in assessment_keywords:
        if keyword in scenario_lower or keyword in ai_role_lower:
            print(f"🎯 Auto-detected ASSESSMENT mode (keyword: '{keyword}')")
            return "assessment"
    
    # Check for learning keywords
    for keyword in learning_keywords:
        if keyword in scenario_lower or keyword in ai_role_lower:
            print(f"📚 Auto-detected LEARNING mode (keyword: '{keyword}')")
            return "learning"
    
    # Default to learning mode for safe practice
    print("📚 Defaulting to LEARNING mode (no clear indicators)")
    return "learning"

@app.post("/session/start")
def start_session():
    # Clear previous audio files on new session start
    try:
        if os.path.exists(AUDIO_DIR):
            for f in os.listdir(AUDIO_DIR):
                file_path = os.path.join(AUDIO_DIR, f)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
    except Exception as e:
        print(f"Error clearing audio dir: {e}")

    data = request.get_json(force=True, silent=True) or {}
    role = data.get("role")
    ai_role = data.get("ai_role")
    scenario = data.get("scenario")
    framework = data.get("framework", "auto")
    
    # Support both old 'mode' and new 'scenario_type' parameters
    scenario_type = data.get("scenario_type")
    mode = data.get("mode")  # Legacy support
    
    if not role or not ai_role or not scenario: 
        return jsonify({"error": "Missing fields"}), 400

    # Auto-detect scenario_type if not explicitly provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    print(f"📋 Session scenario_type set to: {scenario_type}")
    
    # Map scenario_type to mode for backward compatibility with roleplay prompts
    mode_map = {
        "coaching": "evaluation",      # Coaching scenarios get scores
        "negotiation": "evaluation",   # Negotiation scenarios get scores
        "reflection": "coaching",      # Reflection scenarios are qualitative
        "custom": "coaching"           # Custom scenarios default to coaching style
    }
    mode = mode_map.get(scenario_type, "coaching")

    # Handle 'auto' framework selection
    if framework == "auto" or framework == "AUTO":
        framework = select_framework_for_scenario(scenario, ai_role)
    elif isinstance(framework, str): 
        framework = [framework.upper()]
    elif isinstance(framework, list): 
        framework = [f.upper() for f in framework]

    session_id = str(uuid.uuid4())
    
    summary = llm_reply(build_summary_prompt(role, ai_role, scenario, framework, mode=mode), max_tokens=150)
    summary = sanitize_llm_output(summary)
    
    # Store session in memory with scenario_type
    session_data = {
        "id": session_id,
        "created_at": dt.datetime.now().isoformat(),
        "role": role,
        "ai_role": ai_role,
        "scenario": scenario,
        "framework": json.dumps(framework) if isinstance(framework, list) else framework,
        "scenario_type": scenario_type,  # NEW: scenario-based report type
        "mode": mode,  # Legacy: kept for backward compatibility
        "transcript": [{"role": "assistant", "content": summary}],
        "report_data": {},
        "completed": False,
        "report_file": None,
        "meta": {"framework_counts": {}, "relevance_issues": 0}
    }
    SESSIONS[session_id] = session_data
    
    # Save to database
    save_session_to_db(session_id, session_data)

    return jsonify({"session_id": session_id, "summary": summary, "framework": framework, "scenario_type": scenario_type})

@app.post("/api/session/<session_id>/chat")
def chat(session_id: str):
    sess = get_session(session_id)
    if not sess: 
        return jsonify({"error": "Session not found"}), 404
    
    user_msg = normalize_text(request.get_json().get("message", ""))
    audio_url = request.get_json().get("audio_url")
    
    # Update transcript
    sess["transcript"].append({
        "role": "user", 
        "content": user_msg,
        "audio_url": audio_url
    })

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
    clean_response = re.sub(r"<<.*?>>", "", visible_response, flags=re.DOTALL).strip()
    
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
    
    # Save to database
    save_session_to_db(session_id, sess)
 
    return jsonify({
        "follow_up": clean_response, 
        "framework_detected": detected_fw,
        "framework_counts": sess["meta"].get("framework_counts", {})
    })

@app.post("/api/session/<session_id>/complete")
def complete_session(session_id: str):
    sess = get_session(session_id)
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

    # Get scenario_type (new) or fallback to mode (legacy)
    scenario_type = sess.get("scenario_type")
    mode = sess.get("mode", "coaching")
    
    # Generate report data if not present
    if not sess.get("report_data"):
        print(f"Generating report data for {session_id} (scenario_type: {scenario_type})...")
        try:
            data = analyze_full_report_data(
                sess["transcript"], 
                sess["role"], 
                sess["ai_role"], 
                sess["scenario"],
                fw_display,
                mode=mode,
                scenario_type=scenario_type
            )
            sess["report_data"] = data
        except Exception as e:
            print(f"Error generating data: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Generate PDF with unified structure
    generate_report(
        sess["transcript"], 
        sess["role"], 
        sess["ai_role"],
        sess["scenario"], 
        fw_display, 
        filename=report_path,
        mode=mode,
        precomputed_data=sess["report_data"],
        scenario_type=scenario_type
    )
    
    sess["completed"] = True
    sess["report_file"] = report_path
    
    return jsonify({"message": "Report generated", "report_file": report_path, "scenario_type": scenario_type})

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
        response["scenario_type"] = sess.get("scenario_type", response.get("scenario_type", "custom"))
        return jsonify(response)
        
    # Generate new data if not present
    scenario_type = sess.get("scenario_type")
    print(f"Generating report data for {session_id} (scenario_type: {scenario_type})...")
    try:
        try:
            framework_data = json.loads(sess["framework"]) if sess["framework"] and sess["framework"].startswith("[") else sess["framework"]
        except:
            framework_data = sess["framework"]

        fw_arg = framework_data if isinstance(framework_data, str) else (framework_data[0] if isinstance(framework_data, list) and framework_data else None)
        mode = sess.get("mode", "coaching")

        data = analyze_full_report_data(
            sess["transcript"], 
            sess["role"], 
            sess["ai_role"], 
            sess["scenario"],
            fw_arg,
            mode=mode,
            scenario_type=scenario_type
        )
        sess["report_data"] = data
        
        response = data.copy()
        response["transcript"] = sess["transcript"]
        response["scenario"] = sess["scenario"] or "No context available."
        response["scenario_type"] = scenario_type or data.get("scenario_type", "custom")
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
    # Hardcoded scenarios with scenario_type for unified report generation
    SCENARIO_CATEGORIES = [
        {
            "name": "Exercise Test Scenarios",
            "color": "from-orange-600 to-red-500",
            "scenarios": [
                {
                    "title": "Scenario 1: Retail Coaching",
                    "description": "A staff member's recent performance has dropped (sales, energy, engagement). The manager is initiating a coaching conversation, not a disciplinary one.",
                    "ai_role": "Retail Sales Associate",
                    "ai_role_short": "Associate",
                    "user_role": "Retail Store Manager",
                    "scenario": "CONTEXT: The conversation takes place inside a retail store. The staff member's recent performance has dropped: Missed sales targets, Low energy on the floor, Poor customer engagement. The manager is initiating a coaching conversation, not a disciplinary one. \n\nAI BEHAVIOR: Start with mild defensiveness (justification, hesitation). Only become more open if the manager shows empathy, looks for root causes, and avoids blame. If the manager is directive or accusatory, remain closed.",
                    "icon": "Users",
                    "scenario_type": "coaching",
                    "include_scores": True
                },
                {
                    "title": "Scenario 2: Low-Price Negotiation",
                    "description": "Customer is interested in purchasing a high-value product but has concerns about price being too high, competitor offers, and is asking for discounts.",
                    "ai_role": "Retail Customer",
                    "ai_role_short": "Customer",
                    "user_role": "Salesperson",
                    "scenario": "CONTEXT: Customer is interested in purchasing a high-value product but has concerns: Price is too high, Comparing with competitor offers, Asking for discounts or add-ons. \n\nAI BEHAVIOR: Be a curious but cautious customer. Push back on price. Test the salesperson's value explanation. Become more agreeable ONLY if value is demonstrated well. If they discount too early, push for more.",
                    "icon": "ShoppingCart",
                    "scenario_type": "negotiation",
                    "include_scores": True
                },
                {
                    "title": "Scenario 3: Learning Reflection",
                    "description": "The user explains how they handled a recent customer interaction (or simulates a short one) to receive coaching guidance.",
                    "ai_role": "Coach Alex",
                    "ai_role_short": "Coach",
                    "user_role": "Retail Staff",
                    "scenario": "CONTEXT: The user will explain how they handled a recent customer interaction (or simulate a short one). \n\nAI BEHAVIOR: Do NOT judge or score. Use reflection, curiosity, and learning prompts. Demonstrate 'how to think', not 'what to say'. Guide them to realize their own patterns.",
                    "icon": "GraduationCap",
                    "scenario_type": "reflection",
                    "include_scores": False
                }
            ]
        },
    ]
    return jsonify(SCENARIO_CATEGORIES)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
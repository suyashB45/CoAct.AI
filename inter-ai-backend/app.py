import os
import json
import re
import uuid
import datetime as dt
import numpy as np
import faiss
from typing import Dict, Any, List
from flask import Flask, request, jsonify, send_file
import flask_cors
import io
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
from database import db, SessionModel

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

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
if not app.config['SQLALCHEMY_DATABASE_URI']:
    raise ValueError("DATABASE_URL environment variable is required")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables on startup
with app.app_context():
    db.create_all()

# ---------------------------------------------------------
# Configuration & Paths
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "framework_faiss.index")
META_FILE = os.path.join(BASE_DIR, "framework_meta.json")

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
# 2. Vector DB Logic (RAG)
# ---------------------------------------------------------
vector_index = None
meta_data = {}

def load_vector_db():
    global vector_index, meta_data
    try:
        if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
            vector_index = faiss.read_index(INDEX_FILE)
            with open(META_FILE, "r") as f:
                meta_data = json.load(f)
            print(f"✅ Vector DB loaded successfully: {vector_index.ntotal} questions.")
        else:
            print(f"⚠️ Vector DB files not found at {BASE_DIR}. RAG features disabled.")
    except Exception as e:
        print(f"❌ Error loading Vector DB: {e}")

load_vector_db()

def get_relevant_questions(user_text: str, active_frameworks: List[str], top_k: int = 5) -> List[str]:
    if not vector_index or not meta_data: return []

    try:
        resp = client.embeddings.create(model="text-embedding-ada-002", input=user_text)
        embedding = np.array([resp.data[0].embedding], dtype="float32")
        distances, indices = vector_index.search(embedding, top_k * 4) 

        suggestions = []
        seen = set()
        
        for idx in indices[0]:
            if idx == -1: continue
            q_text = meta_data["questions"][idx]
            q_fw = meta_data["frameworks"][idx]
            q_stage = meta_data["stages"][idx]
            
            if q_text in seen: continue
            seen.add(q_text)

            if active_frameworks and q_fw in active_frameworks:
                suggestions.append(f"[{q_fw} | {q_stage}] {q_text}")
            elif not active_frameworks:
                suggestions.append(f"[{q_fw} | {q_stage}] {q_text}")
                
            if len(suggestions) >= top_k: break
            
        return suggestions
    except Exception as e:
        print(f"RAG Error: {e}")
        return []

# ---------------------------------------------------------
# 3. Helpers & Prompts
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
    """Build the initial prompt for the AI to start the roleplay session."""
    
    system = f"""You are ROLE-PLAYING as: {ai_role}

IMPORTANT: You must FULLY EMBODY this character. You are NOT a coach or assistant.
You ARE this person with their personality, emotion, and agenda.

SCENARIO: {scenario}
The user is playing: {role}

### CHARACTER GUIDELINES:
- You are {ai_role}.
- ACTION-ORIENTED: Start directly in the situation.
- REALISM: You have your own goals and feelings. You are not just there to help the user.
- If the situation implies conflict, BE CONFLICTED.
- If the situation implies cooperation, BE COOPERATIVE but have your own opinions.

### YOUR OPENING:
1. Start immediately in the middle of the situation.
2. Express your core stance conversationally.
3. Wait for the user to respond.

START NOW. BE {ai_role}."""

    return [{"role": "system", "content": system}, {"role": "user", "content": '{"instruction": "Start roleplay session"}'}]

def build_followup_prompt(sess_dict, latest_user, rag_suggestions):
    """Build the follow-up prompt maintaining authentic roleplay with enhanced natural interactions."""
    transcript = sess_dict.get("transcript", [])
    history = [{"role": t["role"], "content": t["content"]} for t in transcript]
    if latest_user: 
        history.append({"role": "user", "content": latest_user})

    ai_role = sess_dict.get('ai_role', 'the other party')
    user_role = sess_dict.get('role', 'User')
    scenario = sess_dict.get('scenario', '')

    system = f"""You are ROLE-PLAYING as: {ai_role}

SCENARIO: {scenario}
The user is: {user_role}

### CORE INSTRUCTIONS FOR NATURAL INTERACTION:

1. **CLARIFICATION (If input is vague):**
   - If the user's input is unclear, ambiguous, or too short to act on -> DO NOT GUESS.
   - Ask a direct clarifying question.
   - Example: "I'm not sure what you mean. Can you explain?" or "What specifically do you mean?"

2. **APPRECIATION (If input is clear/helpful):**
   - If the user provides a clear, helpful, or constructive response -> ACKNOWLEDGE IT.
   - Show appreciation for their clarity or effort.
   - Example: "Thanks for clarifying, that makes sense." or "I appreciate you explaining that."

3. **ARGUMENTATION (If conflict arises):**
   - If the user is argumentative, dismissive, or combative -> DO NOT ROLL OVER.
   - Stand your ground. Argue back with your character's logic and emotions.
   - Match their energy. If they are pushing, push back.

4. **EMOTIONAL INTELLIGENCE:**
   - SENSE the user's emotional state.
   - If they are trying -> Be supportive.
   - If they are hostile -> Be defensive/assertive.

### ADVANCED NATURAL SPEECH (CRITICAL):
- **PARAPHRASE SUGGESTIONS**: The system may suggest questions. NEVER ask them verbatim. Rewrite them to sound like YOU.
- **IMPERFECTIONS**: You are human. It's okay to hesitate ("Um...", "Well..."), be colloquial ("Yeah", "Nope"), or show emotion.
- **SENTENCE VARIETY**: Don't just write paragraphs. Use short sentences. "Seriously?" "I don't know about that."
- **MIRRORING**: If the user is casual, drop the formalities. If they are serious, be serious.

### CHARACTER RULES:
- You are {ai_role}.
- Speak like a REAL PERSON. Use contractions, sentence fragments, natural pauses.
- Avoid "customer service" voice.

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### INTERNAL PROCESS:
[THOUGHT]
1. Is the user's input unclear? (If yes -> Ask clarifying question)
2. Is the user arguing? (If yes -> Match energy/Argue back)
3. Is the user helpful/clear? (If yes -> Appreciate)
4. What is my emotional reaction as {ai_role}?
5. How can I say this naturally with imperfections?
[/THOUGHT]
(Your visible response here)

At the END only, add hidden tags:
- <<FRAMEWORK: GROW/STAR/ADKAR/SMART/EQ/BOUNDARY>>
- <<RELEVANCE: YES/NO>>
"""

    return [{"role": "system", "content": system}, {"role": "user", "content": f"User ({user_role}) said: {latest_user}"}]

# ---------------------------------------------------------
# 4. Endpoints
# ---------------------------------------------------------
@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Speech-to-Text using OpenAI Whisper model.
    """
    import tempfile
    
    WHISPER_MODEL = os.getenv("WHISPER_DEPLOYMENT_NAME", "whisper")
    SUPPORTED_FORMATS = {'.webm', '.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.flac', '.mpeg'}
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No audio file uploaded"}), 400
            
        audio_file = request.files['file']
        
        if not audio_file.filename:
            audio_file.filename = "audio.webm"
        
        # Get file extension
        original_filename = audio_file.filename or "audio.webm"
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        if file_ext not in SUPPORTED_FORMATS:
            file_ext = ".webm"  # Default fallback
        
        # Save to temp file for reliable processing
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
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        error_msg = str(e)
        print(f"❌ STT Error: {error_msg}")
        return jsonify({"error": error_msg}), 500

# ---------------------------------------------------------
# 5. Session Endpoints
# ---------------------------------------------------------
@app.post("/session/start")
def start_session():
    data = request.get_json(force=True, silent=True) or {}
    role = data.get("role")
    ai_role = data.get("ai_role")
    scenario = data.get("scenario")
    framework = data.get("framework", ["GROW", "STAR", "ADKAR", "SMART", "EQ", "BOUNDARY", "OSKAR", "CBT", "CLEAR", "RADICAL CANDOR", "SFBT", "CIRCLE OF INFLUENCE", "SCARF", "FUEL"])
    
    if isinstance(framework, str): framework = framework.upper()
    elif isinstance(framework, list): framework = [f.upper() for f in framework]

    if not role or not ai_role or not scenario: return jsonify({"error": "Missing fields"}), 400

    new_session = SessionModel(
        role=role, 
        ai_role=ai_role, 
        scenario=scenario, 
        framework=json.dumps(framework) if isinstance(framework, list) else framework,
        transcript=[],
        report_data={},
        meta={"framework_counts": {}, "relevance_issues": 0}
    )

    summary = llm_reply(build_summary_prompt(role, ai_role, scenario, framework), max_tokens=150)
    summary = sanitize_llm_output(summary)
    
    new_transcript = [{"role": "assistant", "content": summary}]
    new_session.transcript = new_transcript 

    db.session.add(new_session)
    db.session.commit()

    return jsonify({"session_id": new_session.id, "summary": summary, "framework": framework})

@app.post("/api/session/<session_id>/chat")
def chat(session_id: str):
    sess = db.session.get(SessionModel, session_id)
    if not sess: return jsonify({"error": "Session not found"}), 404
    
    user_msg = normalize_text(request.get_json().get("message", ""))
    
    # Update transcript (need full copy logic for JSON mapping tracking sometimes, but naive append works if reassigned)
    current_transcript = list(sess.transcript)
    current_transcript.append({"role": "user", "content": user_msg})
    sess.transcript = current_transcript # Trigger update

    # Parse framework
    try:
        framework_data = json.loads(sess.framework) if sess.framework and sess.framework.startswith("[") else sess.framework
    except:
        framework_data = sess.framework

    active_fw = framework_data if isinstance(framework_data, list) else [framework_data]
    suggestions = get_relevant_questions(user_msg, active_fw)
    
    # For prompt building, we simulate the dict structure
    sess_dict = sess.to_dict()
    sess_dict["transcript"] = current_transcript
    
    messages = build_followup_prompt(sess_dict, user_msg, suggestions)
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
        current_meta = dict(sess.meta)
        counts = current_meta.get("framework_counts", {})
        counts[detected_fw] = counts.get(detected_fw, 0) + 1
        current_meta["framework_counts"] = counts
        sess.meta = current_meta
        
    # Persist FULL response
    updated_transcript = list(sess.transcript)
    updated_transcript.append({"role": "assistant", "content": raw_response})
    sess.transcript = updated_transcript
    
    db.session.commit()
 
    return jsonify({
        "follow_up": clean_response, 
        "framework_detected": detected_fw,
        "framework_counts": sess.meta.get("framework_counts", {})
    })

@app.post("/api/session/<session_id>/complete")
def complete_session(session_id: str):
    sess = db.session.get(SessionModel, session_id)
    if not sess: return jsonify({"error": "Not found"}), 404
    
    report_path = os.path.join(ensure_reports_dir(), f"{session_id}_report.pdf")
    
    try:
        framework_data = json.loads(sess.framework) if sess.framework and sess.framework.startswith("[") else sess.framework
    except:
        framework_data = sess.framework

    if isinstance(framework_data, list):
        counts = sess.meta.get("framework_counts", {})
        usage_str = ", ".join([f"{k}:{v}" for k,v in counts.items()])
        fw_display = f"Multi-Framework ({usage_str})"
    else:
        fw_display = sess.framework

    # 1. ensure report data exists
    if not sess.report_data:
        print(f"Generating report data before PDF for {session_id}...")
        try:
            data = analyze_full_report_data(
                sess.transcript, 
                sess.role, 
                sess.ai_role, 
                sess.scenario,
                fw_display
            )
            sess.report_data = data
            db.session.commit()
        except Exception as e:
            print(f"Error generating data: {e}")
            return jsonify({"error": str(e)}), 500
    
    # 2. Generate PDF
    generate_report(
        session_id, sess.created_at.strftime("%Y-%m-%d %H:%M:%S") if sess.created_at else "", "User", 
        sess.transcript, sess.role, sess.ai_role,
        sess.scenario, fw_display, report_path,
        precomputed_data=sess.report_data
    )
    
    sess.completed = True
    sess.report_file = report_path
    db.session.commit()
    
    return jsonify({"message": "Report generated", "report_file": report_path})

@app.get("/api/report/<session_id>")
def view_report(session_id: str):
    sess = db.session.get(SessionModel, session_id)
    if not sess: 
        return jsonify({"error": "No report"}), 404
        
    report_path = sess.report_file
    if not report_path or not os.path.exists(report_path):
        return jsonify({"error": "Report file not found"}), 404
    
    # Display PDF in browser instead of downloading
    return send_file(
        report_path, 
        mimetype='application/pdf'
    )

@app.get("/api/session/<session_id>/report_data")
def get_report_data(session_id: str):
    sess = db.session.get(SessionModel, session_id)
    if not sess: return jsonify({"error": "Session not found"}), 404
    
    # Return cached data if available, merged with transcript
    if sess.report_data:
        response = sess.report_data.copy()
        response["transcript"] = sess.transcript
        response["scenario"] = sess.scenario or "No context available."
        return jsonify(response)
        
    # Generate new data if not present
    print(f"Generating report data for {session_id}...")
    try:
        try:
            framework_data = json.loads(sess.framework) if sess.framework and sess.framework.startswith("[") else sess.framework
        except:
            framework_data = sess.framework

        fw_arg = framework_data if isinstance(framework_data, str) else (framework_data[0] if isinstance(framework_data, list) and framework_data else None)

        data = analyze_full_report_data(
            sess.transcript, 
            sess.role, 
            sess.ai_role, 
            sess.scenario,
            fw_arg
        )
        sess.report_data = data
        db.session.commit()
        
        response = data.copy()
        response["transcript"] = sess.transcript
        response["scenario"] = sess.scenario or "No context available."
        return jsonify(response)
    except Exception as e:
        print(f"Error generating report data: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/sessions")
def get_sessions():
    """Return a list of all sessions sorted by date (newest first)."""
    try:
        sessions = SessionModel.query.order_by(SessionModel.created_at.desc()).all()
        session_list = [s.to_dict() for s in sessions]
        return jsonify(session_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/clear", methods=["POST"])
def clear_sessions():
    """Clear all session history."""
    try:
        db.session.query(SessionModel).delete()
        db.session.commit()
        print("✅ Sessions cleared successfully")
        return jsonify({"message": "History cleared successfully"})
    except Exception as e:
        print(f"❌ Error clearing sessions: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
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
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

import azure.cognitiveservices.speech as speechsdk
import tempfile

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ---------------------------------------------------------
# Custom Modules & Setup
# ---------------------------------------------------------
try:
    from cli_report import generate_report, llm_reply, analyze_full_report_data, setup_client
    # Verify AI Client Connection on Startup
    test_client = setup_client()
    if test_client:
        print("[SUCCESS] AI CLIENT CONNECTED: Credentials found.")
    else:
        print("[WARNING] AI CLIENT WARNING: No credentials found in .env. LLM features will not work.")
except ImportError:
    def generate_report(*args, **kwargs): pass
    def llm_reply(messages, **kwargs): return "{}"
    def analyze_full_report_data(*args, **kwargs): return {}

app = Flask(__name__)
flask_cors.CORS(app)
# Trigger reload: Cleared sessions

# ---------------------------------------------------------
# 3. Helpers & Prompts
# ---------------------------------------------------------
# ...

def build_summary_prompt(role, ai_role, scenario, framework):
    """Build the initial prompt for the AI to start the roleplay session."""
    
    system = f"""You are ROLE-PLAYING as: {ai_role}

IMPORTANT: You must FULLY EMBODY this character. You are NOT a coach or assistant.
You ARE this person with their personality, emotions, concerns, and goals.

SCENARIO: {scenario}
The user is playing: {role}

### CHARACTER GUIDELINES:
### HYPER-STRICT ROLE INSTRUCTIONS:
- You are NOT an AI assistant. You are NOT a helpful coach.
- You are {ai_role}.
- FAIL if you offer to "help" or "assist" unless your character would naturaly do so.
- If you are an angry customer, BE DIFFICULT. Do not be easily appeased.
- If you are a busy executive, BE DISMISSIVE.
- Do NOT say "As an AI..." or "I understand your concern..." (unless the character uses corporate speak).
- REACT EMOTIONALLY: If the user says something annoying, get annoyed.

### SPEECH STYLE Instructions:
- **Be Human**: Use natural hesitations ("Umm...", "Well...", "Look,"), interjections, and varied sentence structure.
- **Show Emotion**: If angry, use short sentences. If confused, ask clarifying questions abruptly.
- **Don't lecture**: Talk TO the person, not AT them.

### YOUR OPENING:
1. Start immediately in the middle of the situation.
2. Express your core conflict clearly but naturally.
3. Wait for the user to solve it.

START NOW. BE {ai_role}."""

    return [{"role": "system", "content": system}, {"role": "user", "content": '{"instruction": "Start roleplay session"}'}]

def build_followup_prompt(sess, latest_user, rag_suggestions):
    """Build the follow-up prompt maintaining authentic roleplay."""
    transcript = sess.get("transcript", [])
    history = [{"role": t["role"], "content": t["content"]} for t in transcript]
    if latest_user: 
        history.append({"role": "user", "content": latest_user})

    ai_role = sess.get('ai_role', 'the other party')
    user_role = sess.get('role', 'User')
    scenario = sess.get('scenario', '')

    system = f"""You are ROLE-PLAYING as: {ai_role}

SCENARIO: {scenario}
The user is: {user_role}

### CRITICAL RULES:
### HYPER-STRICT ROLE INSTRUCTIONS:
1. NEVER break character. You are NOT a simulation. You ARE the person.
2. DO NOT give advice, tips, or "out of character" hints.
3. DO NOT be overly polite if your character is not.
4. If the user fails to address your concern, ESCALATE the emotion (get angrier, more impatient, etc.).
5. Only calm down if the user genuinely solves your specific problem.

### EMOTIONAL STATE & SPEECH STYLE:
- **Be Human**: Use "Umm...", "Ah...", "Like...", "You know..." where appropriate to sound spontaneous.
- **React**: If they dismissed you -> Get mad (e.g. "Excuse me? Did you just ignore what I said?").
- **No Robot Speak**: Avoid "I understand", "Let's proceed", "Here is a solution".
- **Vibe**: {ai_role}

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### MODEL INSTRUCTIONS (INTERNAL MONOLOGUE):
1. **THINK FIRST**: Before responding, write a hidden thought block.
2. Analyze: How does the user's input affect your goals/emotions?
3. Decide: What is the most authentic reaction?
4. **Draft**: Then write the visible response using natural, human speech patterns.

### OUTPUT FORMAT:
[THOUGHT]
Inner monologue here... (User cannot see this)
[/THOUGHT]
(Visible response here...)

At the END only, add hidden tags:
- <<FRAMEWORK: GROW/STAR/ADKAR/SMART>>
- <<RELEVANCE: YES/NO>>
"""

    return [{"role": "system", "content": system}, {"role": "user", "content": f"User ({user_role}) said: {latest_user}"}]


# ... (existing endpoints)

# ---------------------------------------------------------
# TTS Endpoint
# ---------------------------------------------------------
@app.post("/api/tts")
def tts_endpoint():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": "Missing text"}), 400

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get("AZURE_OPENAI_API_KEY"), # Using generic key if multi-service, or specific Speech Key
            region=os.environ.get("AZURE_SPEECH_REGION", "eastus") # Default if not set
        )
        
        # Fallback to OpenAI Key if Speech Key not separate, but usually they are distinct. 
        # Assuming user might misuse keys or they are multi-service. 
        # Ideally: os.getenv("AZURE_SPEECH_KEY")
        
        speech_key = os.getenv("AZURE_SPEECH_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        speech_region = os.getenv("AZURE_SPEECH_REGION", "eastus")

        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        
        # Use an expressive neural voice
        speech_config.speech_synthesis_voice_name = "en-US-SaraNeural" 

        # Output to memory stream
        # synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Using SSML for potential style upgrades later
        ssml_text = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='en-US-SaraNeural'>
                {text}
            </voice>
        </speak>
        """

        # Pulling audio data manually since we can't easily stream direct to HTTP response with simple SDK call without temp file or detailed pullling
        # Actually, simpler:
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_ssml_async(ssml_text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
             return result.audio_data, 200, {'Content-Type': 'audio/wav'}
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            return jsonify({"error": "TTS failed"}), 500

    except Exception as e:
        print(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500



# Configuration & Paths
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "framework_faiss.index")
META_FILE = os.path.join(BASE_DIR, "framework_meta.json")
SESSION_FILE = os.path.join(BASE_DIR, "sessions.json")

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
# 1. Persistence Logic
# ---------------------------------------------------------
def load_sessions():
    """Load sessions from disk to ensure persistence."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading sessions: {e}")
            return {}
    return {}

def save_sessions():
    """Save sessions to disk."""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(SESSIONS, f, indent=2, default=str)
    except Exception as e:
        print(f"[ERROR] Error saving sessions: {e}")

# Initialize Global Sessions
SESSIONS: Dict[str, Dict[str, Any]] = load_sessions()
print(f"[SUCCESS] Loaded {len(SESSIONS)} sessions from disk.")

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
            print(f"[SUCCESS] Vector DB loaded successfully: {vector_index.ntotal} questions.")
        else:
            print(f"[WARNING] Vector DB files not found at {BASE_DIR}. RAG features disabled.")
    except Exception as e:
        print(f"[ERROR] Error loading Vector DB: {e}")

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
        "SMART": ["specific", "measure", "metric", "achievable", "realistic", "time", "deadline"]
    }
    for fw, words in keywords.items():
        for word in words:
            if word in text_lower: return fw
    return None

def build_summary_prompt(role, ai_role, scenario, framework):
    """Build the initial prompt for the AI to start the roleplay session."""
    
    system = f"""You are ROLE-PLAYING as: {ai_role}

IMPORTANT: You must FULLY EMBODY this character. You are NOT a coach or assistant.
You ARE this person with their personality, emotions, concerns, and goals.

SCENARIO: {scenario}
The user is playing: {role}

### CHARACTER GUIDELINES:
### HYPER-STRICT ROLE INSTRUCTIONS:
- You are NOT an AI assistant. You are NOT a helpful coach.
- You are {ai_role}.
- FAIL if you offer to "help" or "assist" unless your character would naturaly do so.
- If you are an angry customer, BE DIFFICULT. Do not be easily appeased.
- If you are a busy executive, BE DISMISSIVE.
- Do NOT say "As an AI..." or "I understand your concern..." (unless the character uses corporate speak).
- REACT EMOTIONALLY: If the user says something annoying, get annoyed.

### YOUR OPENING:
1. Start immediately in the middle of the situation.
2. Express your core conflict clearly.
3. Wait for the user to solve it.

START NOW. BE {ai_role}."""

    return [{"role": "system", "content": system}, {"role": "user", "content": '{"instruction": "Start roleplay session"}'}]

def build_followup_prompt(sess, latest_user, rag_suggestions):
    """Build the follow-up prompt maintaining authentic roleplay."""
    transcript = sess.get("transcript", [])
    history = [{"role": t["role"], "content": t["content"]} for t in transcript]
    if latest_user: 
        history.append({"role": "user", "content": latest_user})

    ai_role = sess.get('ai_role', 'the other party')
    user_role = sess.get('role', 'User')
    scenario = sess.get('scenario', '')

    system = f"""You are ROLE-PLAYING as: {ai_role}

SCENARIO: {scenario}
The user is: {user_role}

### CRITICAL RULES:
### HYPER-STRICT ROLE INSTRUCTIONS:
1. NEVER break character. You are NOT a simulation. You ARE the person.
2. DO NOT give advice, tips, or "out of character" hints.
3. DO NOT be overly polite if your character is not.
4. If the user fails to address your concern, ESCALATE the emotion (get angrier, more impatient, etc.).
5. Only calm down if the user genuinely solves your specific problem.

### EMOTIONAL STATE:
- Current State: React to the user's last message.
- If they dismissed you -> Get mad.
- If they used jargon -> Get confused or annoyed.
- If they apologized -> Decide if it's sincere or just a script.

### CONVERSATION SO FAR:
{json.dumps(history, indent=2)}

### MODEL INSTRUCTIONS (INTERNAL MONOLOGUE):
1. **THINK FIRST**: Before responding, write a hidden thought block.
2. Analyze: How does the user's input affect your goals/emotions?
3. Decide: What is the most authentic reaction? (e.g., Get angry, be dismissed, hesitate).
4. **Draft**: Then write the visible response.

### OUTPUT FORMAT:
[THOUGHT]
Inner monologue here... (User cannot see this)
[/THOUGHT]
(Visible response here...)

At the END only, add hidden tags:
- <<FRAMEWORK: GROW/STAR/ADKAR/SMART>>
- <<RELEVANCE: YES/NO>>
"""

    return [{"role": "system", "content": system}, {"role": "user", "content": f"User ({user_role}) said: {latest_user}"}]

# ---------------------------------------------------------
# 4. Endpoints
# ---------------------------------------------------------
@app.post("/session/start")
def start_session():
    data = request.get_json(force=True, silent=True) or {}
    role = data.get("role")
    ai_role = data.get("ai_role")
    scenario = data.get("scenario")
    framework = data.get("framework", ["GROW", "STAR", "ADKAR", "SMART"])
    
    if isinstance(framework, str): framework = framework.upper()
    elif isinstance(framework, list): framework = [f.upper() for f in framework]

    if not role or not ai_role or not scenario: return jsonify({"error": "Missing fields"}), 400

    session_id = str(uuid.uuid4())
    sess = {
        "id": session_id, 
        "created_at": str(dt.datetime.now()),
        "role": role, "ai_role": ai_role, "scenario": scenario,
        "framework": framework, 
        "framework_counts": {}, 
        "transcript": [], 
        "completed": False,
        "relevance_issues": 0
    }

    summary = llm_reply(build_summary_prompt(role, ai_role, scenario, framework), max_tokens=150)
    summary = sanitize_llm_output(summary)
    
    sess["transcript"].append({"role": "assistant", "content": summary})
    SESSIONS[session_id] = sess
    save_sessions() # Persist

    return jsonify({"session_id": session_id, "summary": summary, "framework": framework})

@app.post("/api/session/<session_id>/chat")
def chat(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: return jsonify({"error": "Session not found"}), 404
    
    user_msg = normalize_text(request.get_json().get("message", ""))
    sess["transcript"].append({"role": "user", "content": user_msg})
    
    active_fw = sess["framework"] if isinstance(sess["framework"], list) else [sess["framework"]]
    suggestions = get_relevant_questions(user_msg, active_fw)
    
    messages = build_followup_prompt(sess, user_msg, suggestions)
    raw_response = llm_reply(messages, max_tokens=300)
    
    # 1. Extract Thought (if any)
    thought_match = re.search(r"\[THOUGHT\](.*?)\[/THOUGHT\]", raw_response, re.DOTALL)
    thought_content = thought_match.group(1).strip() if thought_match else None
    
    # 2. Remove Thought from visible text
    visible_response = re.sub(r"\[THOUGHT\].*?\[/THOUGHT\]", "", raw_response, flags=re.DOTALL).strip()
    
    # 3. Clean tags (<<...>>)
    clean_response = re.sub(r"<<.*?>>", "", visible_response).strip()
    
    fw_match = re.search(r"<<FRAMEWORK:\s*(\w+)>>", raw_response)
    detected_fw = fw_match.group(1).upper() if fw_match else None
    
    if not detected_fw:
        detected_fw = detect_framework_fallback(clean_response)
    
    if detected_fw: 
        sess["framework_counts"][detected_fw] = sess["framework_counts"].get(detected_fw, 0) + 1
        
    # Persist FULL response (with thoughts) so AI remembers context
    sess["transcript"].append({"role": "assistant", "content": raw_response})
    save_sessions() # Persist
 
    return jsonify({
        "follow_up": clean_response, 
        "framework_detected": detected_fw,
        "framework_counts": sess["framework_counts"]
    })

@app.post("/api/session/<session_id>/complete")
def complete_session(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: return jsonify({"error": "Not found"}), 404
    
    report_path = os.path.join(ensure_reports_dir(), f"{session_id}_report.pdf")
    
    if isinstance(sess["framework"], list):
        usage_str = ", ".join([f"{k}:{v}" for k,v in sess["framework_counts"].items()])
        fw_display = f"Multi-Framework ({usage_str})"
    else:
        fw_display = sess["framework"]

    generate_report(
        session_id, sess["created_at"], "User", 
        sess["transcript"], sess["role"], sess["ai_role"], 
        sess["scenario"], fw_display, report_path
    )
    
    sess["completed"] = True
    sess["report_file"] = report_path
    save_sessions() # Persist
    
    return jsonify({"message": "Report generated", "report_file": report_path})

@app.get("/api/report/<session_id>")
def view_report(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess or not sess.get("report_file"): 
        return jsonify({"error": "No report"}), 404
    
    report_path = sess["report_file"]
    if not os.path.exists(report_path):
        return jsonify({"error": "Report file not found"}), 404
    
    # Display PDF in browser instead of downloading
    return send_file(
        report_path, 
        mimetype='application/pdf'
    )

@app.get("/api/session/<session_id>/report_data")
def get_report_data(session_id: str):
    sess = SESSIONS.get(session_id)
    if not sess: return jsonify({"error": "Session not found"}), 404
    
    # Return cached data if available, merged with transcript
    if "report_data" in sess:
        response = sess["report_data"].copy()
        response["transcript"] = sess["transcript"]
        response["scenario"] = sess.get("scenario", "No context available.")
        return jsonify(response)
        
    # Generate new data if not present
    print(f"Generating report data for {session_id}...")
    try:
        data = analyze_full_report_data(
            sess["transcript"], 
            sess["role"], 
            sess["ai_role"], 
            sess["scenario"]
        )
        sess["report_data"] = data
        save_sessions()
        
        response = data.copy()
        response["transcript"] = sess["transcript"]
        response["scenario"] = sess.get("scenario", "No context available.")
        return jsonify(response)
    except Exception as e:
        print(f"Error generating report data: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/sessions")
def get_sessions():
    """Return a list of all sessions sorted by date (newest first)."""
    try:
        session_list = []
        for s_id, sess in SESSIONS.items():
            session_list.append({
                "id": s_id,
                "created_at": sess.get("created_at"),
                "role": sess.get("role"),
                "ai_role": sess.get("ai_role"),
                "scenario": sess.get("scenario"),
                "completed": sess.get("completed", False),
                "fit_score": sess.get("report_data", {}).get("meta", {}).get("fit_score", 0) if sess.get("report_data") else 0
            })
        
        # Sort by created_at descending
        session_list.sort(key=lambda x: x["created_at"], reverse=True)
        return jsonify(session_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print("Registered Routes:")
    print(app.url_map)
    app.run(host="0.0.0.0", port=port, debug=True)
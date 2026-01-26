import json
import os
import math
import unicodedata
import datetime as dt
from fpdf import FPDF
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv()

USE_AZURE = True 
def setup_client():
    if USE_AZURE:
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = setup_client()
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

# --- Premium Modern Palette ---
COLORS = {
    'text_main': (30, 41, 59),       # Slate 800
    'text_light': (100, 116, 139),   # Slate 500
    'white': (255, 255, 255),
    
    # Premium Glassmorphism Palette
    'primary': (15, 23, 42),         # Deep Slate 900
    'secondary': (51, 65, 85),       # Slate 700
    'accent': (59, 130, 246),        # Blue 500 (Primary Brand)
    'accent_light': (96, 165, 250), # Blue 400
    
    # Gradients & UI
    'header_grad_1': (15, 23, 42),   # Slate 900
    'header_grad_2': (30, 58, 138),  # Blue 900
    'score_grad_1': (236, 253, 245), # Emerald 50
    'score_grad_2': (209, 250, 229), # Emerald 100
    'score_text': (4, 120, 87),      # Emerald 700
    
    # Chart Colors
    'chart_fill': (59, 130, 246),    # Blue 500
    'chart_stroke': (37, 99, 235),   # Blue 600
    'sentiment_pos': (16, 185, 129), # Emerald 500
    'sentiment_neg': (239, 68, 68),  # Red 500
    
    # Section colors
    'section_skills': (99, 102, 241),    # Indigo 500
    'section_eq': (236, 72, 153),        # Pink 500
    'section_comm': (14, 165, 233),      # Sky 500
    'section_coach': (245, 158, 11),     # Amber 500
    
    'divider': (226, 232, 240),
    'bg_light': (248, 250, 252),
    'sidebar_bg': (248, 250, 252),
    
    # Status
    'success': (16, 185, 129),       # Emerald 500
    'warning': (245, 158, 11),       # Amber 500
    'danger': (239, 68, 68),         # Red 500
    'rewrite_good': (236, 253, 245), # Emerald 50
    'bad_bg': (254, 226, 226),       # Red 100
    'grey_text': (100, 116, 139),    # Slate 500
    'grey_bg': (241, 245, 249),      # Slate 100
    'purple': (139, 92, 246)         # Violet 500
}

# UNIVERSAL REPORT STRUCTURE DEFINITIONS
SCENARIO_TITLES = {
    "universal": {
        "pulse": "THE PULSE",
        "narrative": "THE NARRATIVE",
        "blueprint": "THE BLUEPRINT"
    }
}


def sanitize_text(text):
    if text is None: return ""
    text = str(text)
    # Extended replacements for common Unicode characters
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2022': '*', '\u2026': '...',
        '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2015': '-',
        '\u2032': "'", '\u2033': '"', '\u2039': '<', '\u203a': '>',
        '\u00a0': ' ', '\u00b7': '*', '\u2027': '*', '\u25cf': '*',
        '\u25cb': 'o', '\u25a0': '*', '\u25a1': 'o', '\u2713': 'v',
        '\u2714': 'v', '\u2717': 'x', '\u2718': 'x', '\u2192': '->',
        '\u2190': '<-', '\u2194': '<->', '\u21d2': '=>', '\u2212': '-',
        '\u00d7': 'x', '\u00f7': '/', '\u2264': '<=', '\u2265': '>=',
        '\u2260': '!=', '\u00b0': ' deg', '\u00ae': '(R)', '\u00a9': '(C)',
        '\u2122': '(TM)', '\u00ab': '<<', '\u00bb': '>>', '\u201a': ',',
        '\u201e': '"', '\u2020': '+', '\u2021': '++', '\u00b6': 'P',
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    # First try to normalize and encode to ASCII
    try:
        normalized = unicodedata.normalize('NFKD', text)
        # Encode to latin-1, replacing any characters that can't be encoded
        return normalized.encode('latin-1', 'replace').decode('latin-1')
    except Exception:
        # Ultimate fallback: strip all non-ASCII
        return ''.join(c if ord(c) < 128 else '?' for c in text)

def sanitize_data(obj):
    """Recursively sanitize all strings in a dictionary or list for PDF compatibility."""
    if isinstance(obj, str):
        return sanitize_text(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_data(item) for item in obj]
    else:
        return obj

def get_score_theme(score):
    try: s = float(score)
    except: s = 0.0
    if s == 0.0: return COLORS['grey_bg'], COLORS['grey_text']
    if s >= 7.0: return COLORS['score_grad_1'], COLORS['score_text'] 
    if s >= 5.0: return (254, 249, 195), (161, 98, 7) 
    return (254, 226, 226), (185, 28, 28) 

def get_bar_color(score):
    try: s = float(score)
    except: s = 0.0
    if s >= 8.0: return COLORS['success']
    if s >= 5.0: return COLORS['warning']
    if s > 0.0: return COLORS['danger']
    return COLORS['grey_text']

def llm_reply(messages, max_tokens=4000):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, max_tokens=max_tokens, temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "{}"

def detect_scenario_type(scenario: str, ai_role: str, role: str) -> str:
    """Detect scenario type based on content to determine report structure."""
    scenario_lower = scenario.lower()
    ai_role_lower = ai_role.lower()
    role_lower = role.lower()
    
    combined_text = f"{scenario_lower} {ai_role_lower} {role_lower}"

    # 1. REFLECTION / MENTORSHIP (No Scorecard)
    # Trigger if AI is strictly a "Coach" or "Mentor" (Role-based)
    if "coach" in ai_role_lower or "mentor" in ai_role_lower:
        return "reflection"
    
    # Trigger if explicit "learning" or "reflection" keywords in text (Topic-based)
    # Note: Avoid "coach" in text search to prevent matching "Manager coaching staff" (which should be Scored)
    reflection_keywords = ["reflection", "learning plan", "development plan", "self-reflection"]
    if any(kw in combined_text for kw in reflection_keywords):
        return "reflection"
    
    # 2. NEGOTIATION / SALES (Scorecard)
    negotiation_keywords = ["sales", "negotiat", "price", "discount", "buyer", "seller", "deal", "purchase"]
    if any(kw in combined_text for kw in negotiation_keywords):
        return "negotiation"
    
    # 3. COACHING / LEADERSHIP (Scorecard)
    # User is the one doing the coaching/managing
    coaching_keywords = ["coaching", "performance", "feedback", "manager", "supervisor", "staff", "employee"]
    if any(kw in combined_text for kw in coaching_keywords):
        return "coaching"
    
    # 4. DE-ESCALATION (Scorecard)
    deescalation_keywords = ["angry", "upset", "complaint", "calm", "de-escalate"]
    if any(kw in combined_text for kw in deescalation_keywords):
        return "custom" # Currently maps to Custom but we can add specific later
    
    # Default
    return "custom"


def detect_user_role_context(role: str, ai_role: str) -> str:
    """Detect the specific sub-role of the user (e.g., Manager vs Staff, Seller vs Buyer)."""
    role_lower = role.lower()
    
    # Coaching Context
    if any(k in role_lower for k in ["manager", "supervisor", "lead", "coach"]):
        return "manager"
    if any(k in role_lower for k in ["staff", "associate", "employee", "report", "subordinate"]):
        return "staff"
        
    # Sales/Negotiation Context
    if any(k in role_lower for k in ["sales", "account executive", "rep", "seller"]):
        return "seller"
    if any(k in role_lower for k in ["customer", "buyer", "client", "prospect"]):
        return "buyer"
        
    return "unknown"

def analyze_full_report_data(transcript, role, ai_role, scenario, framework=None, mode="coaching", scenario_type=None, ai_character="alex"):
    """
    Generate report data using SCENARIO-SPECIFIC structures.
    """
    # Auto-detect scenario type if not provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    
    # Detect granular user role
    user_context = detect_user_role_context(role, ai_role)
    print(f"🕵️ User Context Detected: {user_context} (Scenario: {scenario_type})")

    # CHARACTER SCHEMA OVERRIDE REMOVED - Relying on scenario_type detection
    # if ai_character == 'sarah': ...
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    
    # Base metadata
    meta = {
        "scenario_id": scenario_type,
        "outcome_status": "Completed", 
        "overall_grade": "N/A",
        "summary": "Session analysis.",
        "scenario_type": scenario_type
    }

    if not user_msgs:
        meta["outcome_status"] = "Not Started"
        meta["summary"] = "Session started but no interaction recorded."
        return { "meta": meta, "type": scenario_type }

    # Determine Report Mode based on User Role Context
    # RULE: If User is PERFORMER -> EVALUATION (Scored)
    # RULE: If User is EVALUATOR -> MENTORSHIP (Unscored)
    
    is_user_performer = False
    if scenario_type == "coaching":
        # User is Staff (Performer) vs Manager (Evaluator)
        if user_context == "staff": is_user_performer = True
    elif scenario_type == "negotiation":
        # User is Seller (Performer) vs Buyer (Evaluator)
        if user_context == "seller": is_user_performer = True
    
    # -------------------------------------------------------------
    # BUILD SPECIFIC PROMPTS BASED ON SCENARIO TYPE & ROLE
    # -------------------------------------------------------------
    
    unified_instruction = ""
    
    if scenario_type == "coaching":
        if is_user_performer: # User is STAFF
            unified_instruction = """
### SCENARIO: COACHABILITY ASSESSMENT (USER IS STAFF)
**GOAL**: Evaluate how well the user RECEIVES coaching.
**MODE**: EVALUATION (Score Coachability).
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "coaching", "outcome_status": "Success/Partial/Failure", "overall_grade": "X/10", "summary": "..." },
  "type": "coaching",
  "detailed_analysis": "2-3 paragraphs analysis of the user's professionalism, ownership, and attitude.",
  "scorecard": [
    { 
      "dimension": "Professionalism", 
      "score": "X/10", 
      "description": "A detailed paragraph explaining exactly why this score was given, explicitly mentioning the specific behavior or mistake that led to this score.",
      "quote": "The exact verbatim line from the transcript that helps justify this score.",
      "suggestion": "Specific, actionable advice on what they should have done differently.",
      "alternative_questions": [{"question": "Better phrasing example", "rationale": "Why this phrasing is more effective"}]
    },
    { 
      "dimension": "Ownership", 
      "score": "X/10", 
      "description": "A detailed paragraph analyzing whether they took true ownership or deflected blame, citing specific examples from their response.",
      "quote": "The exact line showing their level of ownership.",
      "suggestion": "How they could have taken stronger ownership.",
      "alternative_questions": [{"question": "I could have done X...", "rationale": "Takes direct responsibility"}]
    },
    { 
      "dimension": "Active Listening", 
      "score": "X/10", 
      "description": "A detailed paragraph evaluating their ability to validate feelings and listen, mentioning specific cues they missed or caught.",
      "quote": "The specific line where they demonstrated or failed at listening.",
      "suggestion": "The specific validation technique they should practice.",
      "alternative_questions": [{"question": "What I hear you saying is...", "rationale": "Demonstrates validation before solution"}]
    },
    { 
      "dimension": "Solution Focus", 
      "score": "X/10", 
      "description": "A detailed paragraph assessing if their solution was collaborative and addressed the root cause, or if it was imposed/dismissive.",
      "quote": "The line where they proposed the solution.",
      "suggestion": "A more collaborative or effective solution approach.",
      "alternative_questions": [{"question": "What if we tried X?", "rationale": "Invites collaboration"}]
    }
  ],
  "strengths": ["..."],
  "missed_opportunities": ["..."],
  "actionable_tips": ["Tip 1...", "Tip 2..."]
}
"""
        else: # User is MANAGER (Evaluator -> Mentorship)
            unified_instruction = """
### SCENARIO: LEADERSHIP MENTORSHIP (USER IS MANAGER)
**GOAL**: specific guidance on improving the user's coaching style.
**MODE**: MENTORSHIP (No Scorecard).
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "learning", "outcome_status": "Completed", "overall_grade": "N/A", "summary": "..." },
  "type": "learning",
  "detailed_analysis": "2-3 paragraph professional analysis of the user's coaching style, highlighting key moments of empathy or friction.",
  "key_insights": ["Insight 1...", "Insight 2..."],
  "reflective_questions": ["Question 1...", "Question 2..."],
  "growth_outcome": "Vision of the user as a better leader...",
  "practice_plan": ["Try asking...", "Focus on..."]
}
"""
            # Override semantic type for Report.tsx to render Learning View
            scenario_type = "learning" 

    elif scenario_type == "negotiation": 
        if is_user_performer: # User is SELLER
            unified_instruction = """
### SCENARIO: SALES PERFORMANCE ASSESSMENT (USER IS SELLER)
**GOAL**: Generate a Sales Performance Report.
**MODE**: EVALUATION (Strict Grading).
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "sales", "outcome_status": "Closed/Negotiating/Lost", "overall_grade": "X/10", "summary": "..." },
  "type": "sales",
  "detailed_analysis": "Analysis of sales technique.",
  "scorecard": [
    { 
      "dimension": "Rapport Building", 
      "score": "X/10", 
      "description": "A detailed paragraph interpreting whether their rapport attempt was authentic or forced, citing specific phrasing used.",
      "quote": "The specific line used for rapport.",
      "suggestion": "A more effective rapport-building approach.",
      "alternative_questions": [{"question": "How has your week been?", "rationale": "Builds personal connection"}]
    },
    { 
      "dimension": "Needs Discovery", 
      "score": "X/10", 
      "description": "A detailed paragraph evaluating the depth of their questioning and whether they uncovered the true need.",
      "quote": "The specific question asked (or missed opportunity).",
      "suggestion": "The critical question they should have asked.",
      "alternative_questions": [{"question": "What is your top priority?", "rationale": "Focuses on strategic goals"}]
    },
    { 
      "dimension": "Value Articulation", 
      "score": "X/10", 
      "description": "A detailed paragraph explaining if they successfully linked the product value to the user's specific pain points.",
      "quote": "The line where they pitched the value.",
      "suggestion": "How to make the value proposition sharper.",
      "alternative_questions": [{"question": "This helps you save X...", "rationale": "Quantifies the benefit explicitly"}]
    },
    { 
      "dimension": "Objection Handling", 
      "score": "X/10", 
      "description": "A detailed paragraph analyzing their emotional reaction and logical answer to the objection.",
      "quote": "The specific response to the objection.",
      "suggestion": "A better frame or technique for handling this objection.",
      "alternative_questions": [{"question": "I understand your concern...", "rationale": "Validates before countering"}]
    },
    { 
      "dimension": "Closing", 
      "score": "X/10", 
      "description": "A detailed paragraph assessing the timing, confidence, and clarity of their closing attempt.",
      "quote": "The specific closing line used.",
      "suggestion": "A more confident or appropriate closing technique.",
      "alternative_questions": [{"question": "Are we ready to move forward?", "rationale": "Direct check for agreement"}]
    }
  ],
  "sales_recommendations": ["Rec 1...", "Rec 2..."]
}
"""
        else: # User is BUYER (Evaluator -> Mentorship)
            unified_instruction = """
### SCENARIO: BUYER STRATEGY MENTORSHIP (USER IS BUYER)
**GOAL**: specific guidance on how to negotiate better deals as a buyer.
**MODE**: MENTORSHIP (No Scorecard).
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "learning", "outcome_status": "Completed", "overall_grade": "N/A", "summary": "..." },
  "type": "learning",
  "detailed_analysis": "Analysis of the user's negotiation power and leverage.",
  "key_insights": ["Insight 1...", "Insight 2..."],
  "reflective_questions": ["Question 1...", "Question 2..."],
  "growth_outcome": "Vision of the user as a stronger negotiator...",
  "practice_plan": ["Be willing to walk away...", "Ask for concessions..."]
}
"""
            # Override semantic type for Report.tsx to render Learning View
            scenario_type = "learning"

    elif scenario_type == "reflection" or scenario_type == "learning":
        unified_instruction = """
### SCENARIO: PERSONAL LEARNING PLAN
**GOAL**: Generate a Developmental Learning Plan.
**MODE**: MENTORSHIP (Supportive, Qualitative Only).
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "learning", "outcome_status": "Completed", "overall_grade": "N/A", "summary": "..." },
  "type": "learning",
  "detailed_analysis": "Professional analysis of the conversation.",
  "key_insights": ["Pattern observed...", "Strength present..."],
  "reflective_questions": ["Question 1...", "Question 2..."],
  "practice_plan": ["Experiment 1...", "Micro-habit..."],
  "growth_outcome": "Vision of success..."
}
"""
    else: # Custom
        unified_instruction = """
### CUSTOM SCENARIO / ROLE PLAY
**GOAL**: Generate an Adaptive Feedback Report.
**OUTPUT JSON STRUCTURE**:
{
  "meta": { "scenario_id": "custom", "outcome_status": "Success/Partial", "overall_grade": "N/A", "summary": "..." },
  "type": "custom",
  "detailed_analysis": "Analysis of performance.",
  "strengths_observed": ["..."],
  "development_opportunities": ["..."],
  "guidance": {
    "continue": ["..."],
    "adjust": ["..."],
    "try_next": ["..."]
  }
}
"""

    # ANALYST PERSONA (Layered on top of Scenario Logic)
    # The 'Content' (what is measured) is determined by the Scenario (above).
    # The 'Voice' (how it is written) is determined by the Character (below).
    
    analyst_persona = ""
    if ai_character == "sarah":
        analyst_persona = """
    ### ANALYST STYLE: COACH SARAH (MENTOR)
    - **Tone**: Warm, encouraging, high-EQ, "Sandwich Method" (Praise-Critique-Praise).
    - **Focus**: Psychological safety, "growth mindset", and emotional intelligence.
    - **Detail Level**: VERY HIGH. Write 4-5 paragraphs in `detailed_analysis`. Go deep into the "why" behind the user's choices.
    - **Signature**: Use phrases like "I loved how you...", "Consider trying...", "A small tweak could be...".
    """
    else: # Default to Alex
        analyst_persona = """
    ### ANALYST STYLE: COACH ALEX (EVALUATOR)
    - **Tone**: Professional, direct, analytical, "Bottom Line Up Front".
    - **Focus**: Efficiency, clear outcomes, negotiation leverage, and rapid improvement.
    - **Detail Level**: VERY HIGH. Write 4-5 paragraphs in `detailed_analysis`. Break down the interaction mechanism by mechanism.
    - **Signature**: Use phrases like "The metrics show...", "You missed an opportunity to...", "To optimize, you must...".
    """

    # Unified System Prompt
    system_prompt = (
        f"### SYSTEM ROLE\\n"
        f"You are an expert Soft Skills Development Coach generating reports for 'COACT.AI'.\\n"
        f"Context: {scenario}\\n"
        f"User Role: {role} | AI Role: {ai_role}\\n"
        f"{analyst_persona}\\n"
        f"{unified_instruction}\\n"
        f"### GENERAL RULES\\n"
        "1. **EVIDENCE-BASED SCORING**: For every score in the 'scorecard', 'description' MUST cite specific behavior or quotes from the user.\\n"
        "2. **JUSTIFICATION**: Do not just say 'Good job'. Explain 'You scored 8/10 because you asked X question at the start...'.\\n"
        "3. OUTPUT MUST BE VALID JSON ONLY.\\n"
    )

    try:
        # Create conversation text for analysis
        full_conversation = "\\n".join([f"{'USER' if t['role'] == 'user' else 'ASSISTANT'}: {t['content']}" for t in transcript])
        
        analysis_input = f"""### FULL CONVERSATION
{full_conversation}
"""
        
        response = llm_reply([
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": analysis_input}
        ])
        clean_text = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Ensure meta exists
        if 'meta' not in data: data['meta'] = {}
        data['meta']['scenario_type'] = scenario_type
        # Add type if missing
        if 'type' not in data: data['type'] = scenario_type

        return data
        
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return {
            "meta": {
                "scenario_id": scenario_type,
                "outcome_status": "Failure", 
                "overall_grade": "F",
                "summary": "Error generating report. Please try again.",
                "scenario_type": scenario_type
            },
            "type": scenario_type
        }


class DashboardPDF(FPDF):
    def cell(self, w, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        # Auto-sanitize all text going into cells
        txt = sanitize_text(txt) if txt else ''
        super().cell(w, h, txt, border, ln, align, fill, link)
    
    def multi_cell(self, w, h, txt, border=0, align='J', fill=False):
        # Auto-sanitize all text going into multi_cells  
        txt = sanitize_text(txt) if txt else ''
        super().multi_cell(w, h, txt, border, align, fill)
    
    def footer(self):
        self.set_y(-15)
        # Add subtle line separator
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_y(-12)
        # Page number on left
        self.set_font('Arial', '', 8)
        self.set_text_color(128, 128, 128)
        super().cell(30, 10, f'Page {self.page_no()}', 0, 0, 'L')
        # Branding in center
        self.set_font('Arial', 'I', 8)
        super().cell(140, 10, 'Generated by CoAct.AI Coaching Engine', 0, 0, 'C')
        # Timestamp on right
        self.set_font('Arial', '', 7)
        super().cell(0, 10, dt.datetime.now().strftime('%Y-%m-%d'), 0, 0, 'R')

    def set_scenario_type(self, scenario_type):
        self.scenario_type = scenario_type

    def get_title(self, section_key):
        stype = getattr(self, 'scenario_type', 'custom')
        return SCENARIO_TITLES.get(stype, SCENARIO_TITLES['custom']).get(section_key, section_key.upper())

    def linear_gradient(self, x, y, w, h, c1, c2, orientation='H'):
        self.set_line_width(0)
        if orientation == 'H':
            for i in range(int(w)):
                r = c1[0] + (c2[0] - c1[0]) * (i / w)
                g = c1[1] + (c2[1] - c1[1]) * (i / w)
                b = c1[2] + (c2[2] - c1[2]) * (i / w)
                self.set_fill_color(int(r), int(g), int(b))
                self.rect(x + i, y, 1, h, 'F')
        else:
            for i in range(int(h)):
                r = c1[0] + (c2[0] - c1[0]) * (i / h)
                g = c1[1] + (c2[1] - c1[1]) * (i / h)
                b = c1[2] + (c2[2] - c1[2]) * (i / h)
                self.set_fill_color(int(r), int(g), int(b))
                self.rect(x, y + i, w, 1, 'F')

    def set_user_name(self, name):
        self.user_name = sanitize_text(name)

    def set_character(self, character):
        self.ai_character = sanitize_text(character).capitalize()

    def header(self):
        if self.page_no() == 1:
            # Premium gradient header
            self.linear_gradient(0, 0, 210, 40, COLORS['header_grad_1'], COLORS['header_grad_2'], 'H')
            # Main title
            self.set_xy(10, 8)
            self.set_font('Arial', 'B', 24)
            self.set_text_color(255, 255, 255)
            super().cell(0, 10, 'COACT.AI', 0, 0, 'L')
            # Subtitle - Dynamic based on Coach
            self.set_xy(10, 22)
            self.set_font('Arial', '', 11)
            self.set_text_color(147, 197, 253)
            
            coach_name = getattr(self, 'ai_character', 'Alex')
            super().cell(0, 5, f'Performance Analysis by Coach {coach_name}', 0, 0, 'L')
            
            # Date on right
            self.set_xy(140, 10)
            self.set_font('Arial', '', 9)
            self.set_text_color(200, 220, 255)
            super().cell(50, 5, dt.datetime.now().strftime('%B %d, %Y'), 0, 0, 'R')
            
            # User Name Display
            if hasattr(self, 'user_name') and self.user_name:
                self.set_xy(140, 16)
                self.set_font('Arial', 'I', 9)
                super().cell(50, 5, f"Prepared for: {self.user_name}", 0, 0, 'R')

            # Avatar Image (Dynamic)
            if hasattr(self, 'ai_character'):
                char_name = self.ai_character.lower()
                img_path = f"{char_name}.png"
                if os.path.exists(img_path):
                     self.image(img_path, x=188, y=8, w=15)

            self.ln(35)
        else:
            # Slim header for subsequent pages
            self.set_fill_color(*COLORS['header_grad_1'])
            self.rect(0, 0, 210, 14, 'F')
            self.set_xy(10, 4)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(255, 255, 255)
            super().cell(100, 6, 'CoAct.AI Report', 0, 0, 'L')
            
            # Avatar Icon Scalling Small
            if hasattr(self, 'ai_character'):
                char_name = self.ai_character.lower()
                img_path = f"{char_name}.png"
                if os.path.exists(img_path):
                    self.image(img_path, x=5, y=2, w=10)
                    
            # Page indicator
            self.set_font('Arial', '', 9)
            self.set_text_color(180, 200, 255)
            super().cell(0, 6, f'Page {self.page_no()}', 0, 0, 'R')
            self.ln(18)

    def set_context(self, role, ai_role, scenario):
        self.user_role = sanitize_text(role)
        self.ai_role = sanitize_text(ai_role)
        self.scenario_text = sanitize_text(scenario)

    def draw_context_summary(self):
        """Draw a summary of the scenario context and roles."""
        if not hasattr(self, 'user_role'): return
        
        self.check_space(40)
        self.ln(5)
        
        # Section Header
        self.set_font('Arial', 'B', 10)
        self.set_text_color(71, 85, 105) # Slate 600
        self.cell(0, 6, "SCENARIO CONTEXT", 0, 1)
        
        # Grid Background
        self.set_fill_color(248, 250, 252) # Slate 50
        start_y = self.get_y()
        self.rect(10, start_y, 190, 35, 'F')
        
        # Draw Roles
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(20, 5, "Your Role:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(60, 5, self.user_role, 0, 0)
        
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(20, 5, "Partner:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(60, 5, self.ai_role, 0, 1)
        
        # Draw Scenario Description
        self.set_xy(15, start_y + 12)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 5, "Situation:", 0, 1)
        
        self.set_x(15)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_light'])
        # Truncate if too long to fit in box
        text = self.scenario_text
        if len(text) > 300: text = text[:297] + "..."
        self.multi_cell(180, 5, text)
        
        # Move cursor past the box
        self.set_y(start_y + 40)

    def draw_scoring_methodology(self):
        """Draw the scoring rubric/methodology section."""
        self.check_space(50)
        self.ln(5)
        
        self.draw_section_header("SCORING METHODOLOGY (THE 'WHY')", COLORS['secondary'])
        
        # Grid Background
        self.set_fill_color(248, 250, 252)
        start_y = self.get_y()
        self.rect(10, start_y, 190, 35, 'F')
        
        # Scoring Levels
        levels = [
            ("9-10 (Expert)", "Exceptional application of skills. Creates deep psychological safety, handles conflict with mastery, and drives clear outcomes."),
            ("7-8 (Proficient)", "Strong performance. Meets all core objectives effectively. Good empathy and strategy, with minor opportunities for refinement."),
            ("4-6 (Competent)", "Functional performance. Achieves basic goals but may miss subtle cues, sound robotic, or struggle with difficult objections."),
            ("1-3 (Needs Ops)", "Struggles with core skills. May be defensive, dismissive, or completely miss the objective. Immediate practice required.")
        ]
        
        current_y = start_y + 4
        
        for grade, desc in levels:
            self.set_xy(15, current_y)
            self.set_font('Arial', 'B', 8)
            
            # Color coding for levels
            if "9-10" in grade: self.set_text_color(*COLORS['success'])
            elif "7-8" in grade: self.set_text_color(*COLORS['success']) # Lighter green ideally, but success works
            elif "4-6" in grade: self.set_text_color(*COLORS['warning'])
            else: self.set_text_color(*COLORS['danger'])
            
            self.cell(25, 6, grade, 0, 0)
            
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_light'])
            self.cell(3, 6, "|", 0, 0)
            
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(150, 6, desc)
            current_y += 7

        self.set_y(start_y + 42)

    def draw_detailed_analysis(self, analysis_text):
        """Draw the detailed analysis section."""
        if not analysis_text: return
        
        self.check_space(60)
        self.ln(5)
        
        self.draw_section_header("DETAILED ANALYSIS", COLORS['secondary'])
        
        # Background Box
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(226, 232, 240)
        self.rect(10, self.get_y(), 190, 45, 'DF')
        
        # Icon
        self.set_xy(15, self.get_y() + 5)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*COLORS['secondary'])
        self.cell(10, 10, "i", 0, 0, 'C') 
        
        # Text
        self.set_xy(25, self.get_y() + 2)
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        
        # Handle long text
        text = sanitize_text(analysis_text)
        if len(text) > 800: text = text[:797] + "..."
        self.multi_cell(170, 6, text)
        
        # Move cursor
        self.set_y(self.get_y() + 10)

    def draw_dynamic_questions(self, questions):
        """Draw the dynamic follow-up questions section."""
        if not questions: return
        
        self.check_space(60)
        self.ln(5)
        
        self.draw_section_header("DEEP DIVE QUESTIONS", COLORS['accent'])
        
        # Grid Background - Purple/Indigo theme
        self.set_fill_color(248, 250, 252) # Very light slate
        start_y = self.get_y()
        # Estimate height based on questions
        height = 15 + (len(questions) * 12)
        self.rect(10, start_y, 190, height, 'F')
        
        current_y = start_y + 5
        
        for i, q in enumerate(questions):
            self.set_xy(15, current_y)
            self.set_font('Arial', 'B', 12)
            self.set_text_color(*COLORS['accent'])
            self.cell(10, 8, "?", 0, 0, 'C')
            
            self.set_font('Arial', 'I', 10) # Italic for questions
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(160, 6, sanitize_text(q))
            
            # Update Y for next question, assuming single line or double line
            # Simple heuristic: add fixed spacing
            current_y = self.get_y() + 4
            
        self.set_y(start_y + height + 5)

    def draw_section_header(self, title, color):
        self.ln(3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*color)
        self.cell(0, 8, title, 0, 1)
        # Add colored underline
        self.set_draw_color(*color)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 50, self.get_y())
        self.set_line_width(0.2)
        self.ln(4)

    def draw_banner(self, meta, scenario_type="custom"):
        """Draw the summary banner at the top of the report."""
        summary = meta.get('summary', '')
        emotional_trajectory = meta.get('emotional_trajectory', '')
        session_quality = meta.get('session_quality', '')
        key_themes = meta.get('key_themes', [])
        overall_grade = meta.get('overall_grade', 'N/A')
        
        self.set_y(self.get_y() + 3)
        start_y = self.get_y()
        
        # Calculate banner height based on content
        base_height = 50
        if emotional_trajectory: base_height += 8
        if session_quality: base_height += 8
        if key_themes: base_height += 10
        banner_height = base_height
        
        # Main Card with shadow effect
        self.set_fill_color(245, 247, 250)  # Subtle shadow
        self.rect(12, start_y + 2, 190, banner_height, 'F')
        
        # Main Card Background
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(226, 232, 240)
        self.rect(10, start_y, 190, banner_height, 'DF')
        
        # Scenario-type specific colors and labels
        scenario_colors = {
            "coaching": (59, 130, 246),    # Blue
            "negotiation": (16, 185, 129), # Green  
            "reflection": (139, 92, 246),  # Purple
            "custom": (245, 158, 11),      # Orange/Amber
            "leadership": (99, 102, 241),  # Indigo (Authority)
            "customer_service": (239, 68, 68) # Red (Urgency/Resolution)
        }
        
        # New Labels matching frontend
        scenario_labels = {
            "coaching": "COACHING EFFICACY",
            "negotiation": "NEGOTIATION POWER",
            "reflection": "LEARNING INSIGHTS",
            "custom": "GOAL ATTAINMENT",
            "leadership": "LEADERSHIP & STRATEGY",
            "customer_service": "CUSTOMER SERVICE"
        }
        
        accent_color = scenario_colors.get(scenario_type, scenario_colors["custom"])
        verd_label = scenario_labels.get(scenario_type, scenario_labels["custom"])
        
        # Accent bar on left - scenario-specific color
        self.set_fill_color(*accent_color)
        self.rect(10, start_y, 4, banner_height, 'F')
        
        # Scenario-type label with icon
        self.set_xy(18, start_y + 6)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(71, 85, 105)  # Slate 600
        icon_map = {
            "coaching": "[C]", "negotiation": "[N]", "reflection": "[R]", "custom": "[*]",
            "leadership": "[L]", "customer_service": "[S]"
        }
        icon = icon_map.get(scenario_type, "[*]")
        self.cell(100, 5, f"{icon} {verd_label}", 0, 1)
        
        # Grade Display (Top Right)
        if scenario_type != 'reflection':
             self.set_xy(150, start_y + 6)
             self.set_font('Arial', 'B', 24)
             self.set_text_color(*COLORS['accent']) # Uses main accent
             # Determine color based on grade if possible, else default accent
             self.cell(40, 10, str(overall_grade), 0, 0, 'R')
        
        # Summary text
        self.set_xy(18, start_y + 15)
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(130, 5, sanitize_text(summary))
        
        # Metrics row with visual indicators
        current_y = start_y + 35
        
        if emotional_trajectory:
            self.set_xy(18, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(99, 102, 241)  # Indigo
            self.cell(3, 4, ">", 0, 0)
            self.set_text_color(100, 116, 139)
            self.cell(38, 4, "EMOTIONAL ARC:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(51, 65, 85)
            self.cell(0, 4, sanitize_text(emotional_trajectory), 0, 1)
            current_y += 7
        
        if session_quality:
            self.set_xy(18, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(16, 185, 129)  # Emerald
            self.cell(3, 4, ">", 0, 0)
            self.set_text_color(100, 116, 139)
            self.cell(38, 4, "SESSION QUALITY:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(51, 65, 85)
            self.cell(0, 4, sanitize_text(session_quality), 0, 1)
            current_y += 7
        
        # Key themes with pill-style display
        if key_themes:
            self.set_xy(18, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(236, 72, 153)  # Pink
            self.cell(3, 4, ">", 0, 0)
            self.set_text_color(100, 116, 139)
            self.cell(38, 4, "KEY THEMES:", 0, 0)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(71, 85, 105)
            themes_text = " | ".join([sanitize_text(str(theme)) for theme in key_themes[:3]])
            self.cell(0, 4, themes_text, 0, 1)
        
        self.set_y(start_y + banner_height + 8)
    
    def draw_executive_summary(self, exec_summary):
        """Draw the Executive Summary section - NEW unified section for all reports."""
        if not exec_summary:
            return
        
        self.check_space(80)
        self.ln(5)
        
        # Section header with gradient-like background
        self.set_fill_color(30, 41, 59)  # Slate 800
        self.rect(10, self.get_y(), 190, 12, 'F')
        self.set_xy(15, self.get_y() + 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, self.get_title("exec_summary"), 0, 1)
        self.ln(3)
        
        # Performance Overview
        overview = exec_summary.get('performance_overview', '')
        if overview:
            self.set_font('Arial', '', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(0, 6, sanitize_text(overview))
            self.ln(6)
        
        # Two-column layout for strengths and growth areas
        start_y = self.get_y()
        
        # Key Strengths (left column)
        strengths = exec_summary.get('key_strengths', [])
        if strengths:
            self.set_fill_color(240, 253, 244)  # Green 50
            self.rect(10, start_y, 90, 45, 'F')
            self.set_xy(15, start_y + 5)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['success'])
            self.cell(80, 5, "KEY STRENGTHS", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            for i, strength in enumerate(strengths[:3]):
                self.set_x(15)
                self.multi_cell(80, 5, f"+ {sanitize_text(strength)}")
        
        # Areas for Growth (right column)
        growth = exec_summary.get('areas_for_growth', [])
        if growth:
            self.set_fill_color(254, 249, 195)  # Yellow 100
            self.rect(105, start_y, 95, 45, 'F')
            self.set_xy(110, start_y + 5)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['warning'])
            self.cell(85, 5, "AREAS FOR GROWTH", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            for i, area in enumerate(growth[:3]):
                self.set_x(110)
                self.multi_cell(85, 5, f"- {sanitize_text(area)}")
        
        self.set_y(start_y + 50)
        
        # Recommended Next Steps
        next_steps = exec_summary.get('recommended_next_steps', '')
        if next_steps:
            self.set_fill_color(248, 250, 252)  # Slate 50
            self.rect(10, self.get_y(), 190, 20, 'F')
            self.set_xy(15, self.get_y() + 5)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['accent'])
            self.cell(40, 5, "NEXT STEPS:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(145, 5, sanitize_text(next_steps))
            self.ln(5)
        
        self.ln(5)
    
    def draw_personalized_recommendations(self, recs):
        """Draw the unified personalized recommendations section."""
        if not recs:
            return
        
        self.check_space(70)
        self.ln(5)
        
        # Dark header block
        self.set_fill_color(30, 41, 59)  # Slate 800
        self.rect(10, self.get_y(), 190, 60, 'F')
        
        start_y = self.get_y()
        self.set_xy(15, start_y + 5)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, self.get_title("recs"), 0, 1)
        
        # Immediate Actions
        actions = recs.get('immediate_actions', [])
        if actions:
            self.set_font('Arial', 'B', 9)
            self.set_text_color(147, 197, 253)  # Blue 300
            self.cell(50, 6, "IMMEDIATE ACTIONS:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(255, 255, 255)
            actions_text = ", ".join([sanitize_text(a) for a in actions[:3]])
            self.multi_cell(135, 6, actions_text)
        
        # Focus Areas
        focus = recs.get('focus_areas', [])
        if focus:
            self.set_font('Arial', 'B', 9)
            self.set_text_color(147, 197, 253)
            self.cell(50, 6, "FOCUS AREAS:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(255, 255, 255)
            focus_text = ", ".join([sanitize_text(f) for f in focus[:3]])
            self.multi_cell(135, 6, focus_text)
        
        # Reflection Prompts
        prompts = recs.get('reflection_prompts', [])
        if prompts:
            self.ln(2)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(203, 213, 225)  # Slate 300
            for prompt in prompts[:2]:
                self.set_x(15)
                self.cell(0, 4, f"? {sanitize_text(prompt)}", 0, 1)
        
        self.set_y(start_y + 65)

    # --- ASSESSMENT MODE DRAWING METHODS ---

    def draw_assessment_table(self, scores, show_scores=True):
        if not scores: return
        self.check_space(80)
        self.ln(5)
        
        self.draw_section_header(self.get_title("skills"), COLORS['primary'])

        # Widths
        w_dim = 45 if show_scores else 50
        w_score = 15
        w_interp = 65 if show_scores else 70
        w_tip = 65 if show_scores else 70
        
        # Header
        self.set_fill_color(241, 245, 249)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(w_dim, 8, "DIMENSION", 1, 0, 'L', True)
        if show_scores:
            self.cell(w_score, 8, "SCORE", 1, 0, 'C', True)
        self.cell(w_interp, 8, "INTERPRETATION", 1, 0, 'L', True)
        self.cell(w_tip, 8, "IMPROVEMENT TIP", 1, 1, 'L', True)

        for item in scores:
            dim = sanitize_text(item.get('dimension', ''))
            score = item.get('score', 0)
            interp = sanitize_text(item.get('interpretation', ''))
            tip = sanitize_text(item.get('improvement_tip', ''))

            # Calculate row height based on content
            row_height = max(15, len(interp) // 40 * 5 + 10, len(tip) // 40 * 5 + 10)

            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(w_dim, row_height, dim, 1, 0, 'L')
            
            if show_scores:
                # Score Color
                if score >= 8: self.set_text_color(*COLORS['success'])
                elif score >= 6: self.set_text_color(*COLORS['warning'])
                else: self.set_text_color(*COLORS['danger'])
                
                self.cell(w_score, row_height, f"{score}/10", 1, 0, 'C')
            
            # Interpretation
            self.set_text_color(*COLORS['text_main'])
            self.set_font('Arial', '', 8)
            current_x = self.get_x()
            current_y = self.get_y()
            self.multi_cell(w_interp, 7.5, interp, border=1, align='L')
            
            # Improvement tip
            self.set_xy(current_x + w_interp, current_y)
            self.set_text_color(*COLORS['accent'])
            self.multi_cell(w_tip, 7.5, tip, border=1, align='L')
            
            # Move to next row
            self.set_xy(10, current_y + row_height)

        self.ln(5)

    def draw_conversation_analytics(self, analytics):
        if not analytics: return
        self.check_space(40)
        
        self.draw_section_header(self.get_title("analytics"), COLORS['secondary'])
        
        # Create a 2x3 grid of metrics
        metrics = [
            ("Total Exchanges", analytics.get('total_exchanges', 'N/A')),
            ("Talk Time Balance", f"{analytics.get('user_talk_time_percentage', 0)}% User"),
            ("Question/Statement Ratio", analytics.get('question_to_statement_ratio', 'N/A')),
            ("Emotional Progression", analytics.get('emotional_tone_progression', 'N/A')),
            ("Framework Adherence", analytics.get('framework_adherence', 'N/A')),
        ]
        
        self.set_fill_color(248, 250, 252)
        self.rect(10, self.get_y(), 190, 35, 'F')
        
        start_y = self.get_y()
        for i, (label, value) in enumerate(metrics):
            x_pos = 15 + (i % 3) * 60
            y_pos = start_y + 5 + (i // 3) * 15
            
            self.set_xy(x_pos, y_pos)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['text_light'])
            self.cell(55, 5, label, 0, 1)
            
            self.set_xy(x_pos, y_pos + 5)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(55, 5, str(value), 0, 0)
        
        self.set_y(start_y + 40)

    def draw_learning_path(self, path):
        if not path: return
        self.check_space(60)
        
        self.draw_section_header("PERSONALIZED LEARNING PATH", COLORS['accent'])
        
        for item in path:
            skill = sanitize_text(item.get('skill', ''))
            priority = item.get('priority', 'Medium')
            timeline = sanitize_text(item.get('timeline', ''))
            
            # Priority color coding
            if priority == 'High': color = COLORS['danger']
            elif priority == 'Medium': color = COLORS['warning']
            else: color = COLORS['success']
            
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*color)
            self.cell(100, 6, f"• {skill}", 0, 0)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.cell(0, 6, f"Priority: {priority} | {timeline}", 0, 1)
            self.ln(2)
        
        self.ln(5)

    def _extract_score_value(self, score_str):
        try:
            # Remove /10 or similar
            clean = str(score_str).split('/')[0].strip()
            return float(clean)
        except:
            return 0.0

    # --- SCENARIO SPECIFIC DRAWING METHODS ---

    def draw_scorecard(self, scorecard):
        """Draw a standard scorecard table with zebra striping."""
        if not scorecard: return
        self.check_space(60)
        self.ln(8) # Extra spacing
        self.draw_section_header("PERFORMANCE SCORECARD", COLORS['primary'])
        
        # Table Header
        self.set_fill_color(30, 41, 59) # Dark header
        self.set_font('Arial', 'B', 9)
        self.set_text_color(255, 255, 255) # White text
        self.cell(50, 9, "DIMENSION", 0, 0, 'L', True)
        self.cell(20, 9, "SCORE", 0, 0, 'C', True)
        self.cell(120, 9, "OBSERVATION", 0, 1, 'L', True)
        
        # Rows
        for i, item in enumerate(scorecard):
            dim = sanitize_text(item.get('dimension', ''))
            score = str(item.get('score', 'N/A'))
            desc = sanitize_text(item.get('description', ''))
            
            row_height = max(14, len(desc) // 70 * 5 + 10)
            self.check_space(row_height)
            
            # Zebra striping
            if i % 2 == 0:
                self.set_fill_color(248, 250, 252) # Very light gray
            else:
                self.set_fill_color(255, 255, 255) # White
            
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            
            # Draw row background
            x_start = self.get_x()
            y_start = self.get_y()
            self.cell(50, row_height, dim, 0, 0, 'L', True)
            
            # Score Color
            try:
                s_val = float(score.split('/')[0])
                if s_val >= 8: self.set_text_color(*COLORS['success'])
                elif s_val <= 5: self.set_text_color(*COLORS['danger'])
                else: self.set_text_color(*COLORS['warning'])
            except:
                self.set_text_color(*COLORS['text_main'])
                
            self.cell(20, row_height, score, 0, 0, 'C', True)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            
            # Multi-cell handling with background fill
            self.set_xy(x_start + 70, y_start)
            self.multi_cell(120, row_height, desc, border=0, align='L', fill=True)
            
            # Reset position for next row manually if multi_cell didn't perfectly align
            self.set_xy(x_start, y_start + row_height)
            self.line(x_start, y_start + row_height, x_start + 190, y_start + row_height) # Bottom border
            self.set_text_color(*COLORS['text_main']) # Reset color

    def draw_key_value_grid(self, title, data_dict, color=COLORS['secondary']):
        """Draw a grid of key-value pairs with better spacing."""
        if not data_dict: return
        self.check_space(50)
        self.ln(8)
        self.draw_section_header(title, color)
        
        self.set_fill_color(248, 250, 252) 
        self.rect(self.get_x(), self.get_y(), 190, len(data_dict)*8 + 5, 'F')
        self.ln(2)

        for key, value in data_dict.items():
            key_label = key.replace('_', ' ').title()
            val_text = sanitize_text(str(value))
            
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(60, 8, "  " + key_label + ":", 0, 0) # Indent
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(0, 8, val_text)
        self.ln(2)

    def draw_list_section(self, title, items, color=COLORS['section_comm'], bullet="•"):
        """Draw a bulleted list section with icons."""
        if not items: return
        self.check_space(len(items) * 10 + 20)
        self.ln(8)
        self.draw_section_header(title, color)
        
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        for item in items:
            self.set_text_color(*color)
            self.cell(8, 7, bullet, 0, 0, 'R')
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(0, 7, sanitize_text(str(item)))

    # --- MAIN SCENARIO DRAWING ---

    def draw_coaching_report(self, data):
        self.draw_scorecard(data.get('scorecard', []))
        self.draw_key_value_grid("BEHAVIORAL SIGNALS", data.get('behavioral_signals', {}))
        self.draw_list_section("STRENGTHS", data.get('strengths', []), COLORS['success'], "+")
        self.draw_list_section("MISSED OPPORTUNITIES", data.get('missed_opportunities', []), COLORS['warning'], "!")
        self.draw_key_value_grid("COACHING IMPACT", data.get('coaching_impact', {}), COLORS['purple'])
        self.draw_list_section("ACTIONABLE TIPS", data.get('actionable_tips', []), COLORS['accent'], "->")

    def draw_sales_report(self, data):
        self.draw_scorecard(data.get('scorecard', []))
        self.draw_key_value_grid("SIMULATION ANALYSIS", data.get('simulation_analysis', {}))
        self.draw_list_section("WHAT WORKED", data.get('what_worked', []), COLORS['success'], "V")
        self.draw_list_section("LIMITATIONS", data.get('what_limited_effectiveness', []), COLORS['danger'], "X")
        self.draw_key_value_grid("REVENUE IMPACT", data.get('revenue_impact', {}), COLORS['danger'])
        self.draw_list_section("RECOMMENDATIONS", data.get('sales_recommendations', []), COLORS['accent'])

    def draw_learning_report(self, data):
        self.draw_key_value_grid("CONTEXT", data.get('context_summary', {}))
        self.draw_list_section("KEY INSIGHTS", data.get('key_insights', []), COLORS['purple'])
        self.draw_list_section("REFLECTIVE QUESTIONS", data.get('reflective_questions', []), COLORS['accent'], "?")
        
        # Behavioral Shifts
        shifts = data.get('behavioral_shifts', [])
        if shifts:
            self.draw_section_header("BEHAVIORAL SHIFTS", COLORS['section_skills'])
            for s in shifts:
                self.set_font('Arial', '', 9)
                self.cell(90, 6, sanitize_text(s.get('from','')), 0, 0)
                self.cell(10, 6, "->", 0, 0)
                self.set_font('Arial', 'B', 9)
                self.multi_cell(0, 6, sanitize_text(s.get('to','')))
            self.ln(5)

        self.draw_list_section("PRACTICE PLAN", data.get('practice_plan', []), COLORS['success'])
        
        if data.get('growth_outcome'):
            self.ln(5)
            self.set_font('Arial', 'I', 11)
            self.set_text_color(*COLORS['primary'])
            self.multi_cell(0, 8, f"Growth Vision: {sanitize_text(data['growth_outcome'])}", align='C')

    def draw_custom_report(self, data):
        self.draw_key_value_grid("INTERACTION QUALITY", data.get('interaction_quality', {}))
        
        # Core Skills
        skills = data.get('core_skills', [])
        if skills:
            self.draw_section_header("CORE SKILLS", COLORS['section_skills'])
            for s in skills:
                self.set_font('Arial', 'B', 9)
                self.cell(50, 6, sanitize_text(s.get('skill', '')), 0, 0)
                self.cell(30, 6, sanitize_text(s.get('rating', '')), 0, 0)
                self.set_font('Arial', '', 9)
                self.multi_cell(0, 6, sanitize_text(s.get('feedback', '')))
        
        self.draw_list_section("STRENGTHS", data.get('strengths_observed', []), COLORS['success'])
        self.draw_list_section("DEVELOPMENT AREAS", data.get('development_opportunities', []), COLORS['warning'])
        
        # Guidance
        guidance = data.get('guidance', {})
        if guidance:
            self.draw_list_section("CONTINUE", guidance.get('continue', []), COLORS['success'])
            self.draw_list_section("ADJUST", guidance.get('adjust', []), COLORS['warning'])
            self.draw_list_section("TRY NEXT", guidance.get('try_next', []), COLORS['accent'])


def generate_report(transcript, role, ai_role, scenario, framework=None, filename="coaching_report.pdf", mode="coaching", precomputed_data=None, scenario_type=None, user_name="Valued User", ai_character="alex"):
    """
    Generate a UNIFIED PDF report for all scenario types.
    """
    # Auto-detect scenario type if not provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    
    print(f"Generating Unified PDF Report (scenario_type: {scenario_type}) for user: {user_name}...")
    
    # Analyze data or use precomputed
    if precomputed_data:
        data = precomputed_data
        if 'scenario_type' not in data: 
            data['scenario_type'] = scenario_type
    else:
        print("Generating new report data...")
        data = analyze_full_report_data(transcript, role, ai_role, scenario, framework, mode, scenario_type)
    
    # Sanitize data for PDF
    def sanitize_data_recursive(obj):
        if isinstance(obj, str):
            return sanitize_text(obj)
        elif isinstance(obj, dict):
            return {k: sanitize_data_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_data_recursive(item) for item in obj]
        return obj
    
    data = sanitize_data_recursive(data)
    
    pdf = DashboardPDF()
    pdf.set_scenario_type(scenario_type)
    pdf.set_user_name(user_name)
    pdf.set_character(ai_character)
    pdf.set_context(role, ai_role, scenario)
    pdf.add_page()
    
    # Get scenario_type from data if available
    scenario_type = data.get('meta', {}).get('scenario_type', scenario_type)
    
    # 1. Banner
    meta = data.get('meta', {})
    pdf.draw_banner(meta, scenario_type=scenario_type)
    
    # 1.5 Context Summary (New)
    pdf.draw_context_summary()
    
    # 1.6 Detailed Analysis (New)
    pdf.draw_detailed_analysis(data.get('detailed_analysis', ''))
    
    # 1.7 Dynamic Questions (New)
    pdf.draw_dynamic_questions(data.get('dynamic_questions', []))
    
    # 2. Body based on Scenario Type
    stype = str(scenario_type).lower()
    
    try:
        if 'coaching' in stype:
            pdf.draw_coaching_report(data)
            pdf.draw_scoring_methodology() # Add methodology for coaching
        elif 'sales' in stype or 'negotiation' in stype:
            pdf.draw_sales_report(data)
            pdf.draw_scoring_methodology() # Add methodology for sales
        elif 'learning' in stype or 'reflection' in stype:
            pdf.draw_learning_report(data)
            # No scoring rubric for learning/reflection as they are non-evaluative
        else:
            pdf.draw_custom_report(data)
            pdf.draw_scoring_methodology() # Add methodology for custom
    except Exception as e:
        print(f"Error drawing report body: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to generic dump if drawing fails
        pdf.draw_key_value_grid("RAW DATA DUMP (Drawing Failed)", {k:str(v)[:100] for k,v in data.items() if k != 'meta'})

    
    pdf.output(filename)
    print(f"[SUCCESS] Unified report saved: {filename} (scenario: {scenario_type})")

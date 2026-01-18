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
    'grey_bg': (241, 245, 249)       # Slate 100
}

# UNIVERSAL REPORT STRUCTURE DEFINITIONS
SCENARIO_TITLES = {
    # Headers are now standardized across the 3 layers, but we keep this for any specific UI labels if needed
    "universal": {
        "layer_1": "THE PULSE",
        "layer_2": "THE NARRATIVE",
        "layer_3": "THE BLUEPRINT"
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
    
    # Scenario 1: Coaching/Performance Management
    coaching_keywords = ["coaching", "performance", "dropped", "missed targets", "energy", "engagement", "staff", "team member", "employee"]
    
    # Scenario 2: Sales/Negotiation
    negotiation_keywords = ["customer", "price", "negotiate", "discount", "budget", "sales", "purchase", "buying", "competitor", "offer"]
    
    # Scenario 3: Reflection/Learning (with a coach)
    reflection_keywords = ["coach", "reflection", "learning", "explain", "handled", "feedback", "development", "practice"]
    
    # Scenario 4: De-escalation
    deescalation_keywords = ["angry", "upset", "complaint", "calm", "de-escalate", "tension", "conflict", "furious"]

    combined_text = f"{scenario_lower} {ai_role_lower} {role_lower}"
    
    # Check for reflection first
    if "coach" in ai_role_lower or any(kw in combined_text for kw in reflection_keywords[:3]):
        return "reflection"
    
    # Check for de-escalation (S4 variant)
    if any(kw in combined_text for kw in deescalation_keywords):
        return "deescalation"
    
    # Check for negotiation
    if any(kw in combined_text for kw in negotiation_keywords):
        return "negotiation"
    
    # Check for coaching
    if any(kw in combined_text for kw in coaching_keywords):
        return "coaching"
    
    # Default to custom for anything else
    return "custom"


def analyze_full_report_data(transcript, role, ai_role, scenario, framework=None, mode="coaching", scenario_type=None):
    """
    Generate report data using the UNIVERSAL MODULAR STRUCTURE:
    1. The Pulse (Metrics)
    2. The Narrative (Insights)
    3. The Blueprint (Development)
    """
    # Auto-detect scenario type if not provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    
    if not user_msgs:
        return {
            "meta": {
                "outcome_status": "Not Started",
                "overall_grade": "N/A",
                "summary": "Session started but no interaction recorded.",
                "scenario_type": scenario_type
            },
            "layer_1_pulse": [],
            "layer_2_narrative": {},
            "layer_3_blueprint": {}
        }

    # -------------------------------------------------------------
    # BUILD SPECIFIC PROMPTS BASED ON SCENARIO TYPE
    # -------------------------------------------------------------
    
    specific_instruction = ""
    
    if scenario_type == "coaching":
        specific_instruction = """
### SCENARIO 1: MANAGERIAL COACHING
- **TONE**: Evaluative / Growth
- **VERDICT LABEL**: "Coaching Efficacy"
- **METRICS (S1 - 1-10 Scores)**:
  1. "Listening & Empathy"
  2. "Questioning Quality"
  3. "Psychological Safety"
  4. "Coaching vs Telling"
  5. "Overall Coaching Effectiveness"
- **STRENGTHS & IMPROVEMENTS**: Focus on safe space, blame language, leading questions, vs open questions.
"""
    elif scenario_type == "negotiation":
        specific_instruction = """
### SCENARIO 2: SALES & NEGOTIATION
- **TONE**: Results / Tactical
- **VERDICT LABEL**: "Negotiation Power"
- **METRICS (S2 - 1-10 Scores)**:
  1. "Rapport Building"
  2. "Needs Discovery"
  3. "Objection Handling"
  4. "Value Articulation"
  5. "Negotiation Effectiveness"
- **OBSERVATIONS**: Focus on discounting timing, probing depth, price reframe.
"""
    elif scenario_type == "reflection":
        specific_instruction = """
### SCENARIO 3: LEARNING REFLECTION (NO SCORES)
- **TONE**: Supportive / Deep
- **VERDICT LABEL**: "Learning Insights"
- **METRICS**: NONE. Do NOT generate scores.
- **OUTPUT FOCUS**:
  1. **Key Insights**: Patterns in user behavior (e.g. "You tend to explain before understanding").
  2. **Coaching Questions**: Reflective questions for the user (e.g. "What signals did you miss?").
  3. **Skill Focus Areas**: 3 specific skills to work on.
  4. **Practice Suggestions**: Concrete actions (e.g. "Pause for 3 seconds").
- **IMPORTANT**: Return 'layer_1_pulse' as EMPTY LIST []. Do not invent scores.
"""
    elif scenario_type == "deescalation":
        specific_instruction = """
### SCENARIO 4: DE-ESCALATION
- **TONE**: Objective / Adaptive
- **VERDICT LABEL**: "Goal Attainment"
- **METRICS (S4 - 1-10 Scores)**:
  1. "Temp. Control"
  2. "Neutral Language"
  3. "Solution Focus"
  4. "Policy Flex"
"""
    else: # Custom
        specific_instruction = """
### CUSTOM SCENARIO
- **TONE**: Objective / Adaptive
- **VERDICT LABEL**: "Goal Attainment"
- **METRICS (Custom)**: Identify the 4 most critical professional competencies for this specific scenario. Generate 1-10 scores.
"""

    unified_instruction = f"""
### UNIVERSAL MODULAR REPORT GENERATION
👉 **Purpose**: Generate a 3-layer report: Pulse (Metrics), Narrative (Insights), Blueprint (Development).
- **SCENARIO TYPE**: {scenario_type.upper()}
{specific_instruction}

### OUTPUT JSON STRUCTURE:
{{
  "meta": {{
    "scenario_id": "{scenario_type}",
    "outcome_status": "Success|Partial|Failure (e.g. 'Staff motivated', 'Sale closed')",
    "overall_grade": "A-F or 1-100",
    "summary": "1-2 sentence context summary."
  }},
  
  "layer_1_pulse": [
    {{ "metric": "Metric Name", "score": "1-10 or Level", "insight": "Brief observation" }},
    {{ "metric": "Metric Name", "score": "...", "insight": "..." }},
    {{ "metric": "Metric Name", "score": "...", "insight": "..." }},
    {{ "metric": "Metric Name", "score": "...", "insight": "..." }}
  ],
  
  "layer_2_narrative": {{
    "sentiment_curve": "Timeline (e.g. 'Defensive -> Curious -> Committed')",
    "critical_pivots": {{
        "green_light": {{ "turn": "Dialogue turn #", "event": "Trust gained when...", "quote": "User quote" }},
        "red_light": {{ "turn": "Dialogue turn #", "event": "Leverage lost when...", "quote": "User quote" }}
    }},
    "think_aloud": {{
        "context": "Context of a specific turn",
        "thought": "What AI really thought (e.g. 'When you said 'policy', I felt ignored.')"
    }}
  }},
  
  "layer_3_blueprint": {{
    "micro_correction": "Instead of 'X', try 'Y'.",
    "shadow_impact": "Long-term consequence (e.g. 'Staff would quit in 3 months').",
    "homework_exercises": ["Exercise 1", "Exercise 2", "Exercise 3"]
  }}
}}
"""

    framework_context = f"Framework: {framework}" if framework else ""

    # Unified System Prompt
    system_prompt = (
        f"### SYSTEM ROLE\\n"
        f"You are an expert Soft Skills Development Coach generating reports for 'COACT.AI'.\\n"
        f"Context: {scenario}\\n"
        f"User Role: {role} | AI Role: {ai_role}\\n"
        f"{framework_context}\\n"
        f"{unified_instruction}\\n"
        f"### GENERAL RULES\\n"
        "1. Be specific and citation-based (quote the user directly).\\n"
        "2. Be constructive and actionable.\\n"
        "3. OUTPUT MUST BE VALID JSON ONLY. No markdown, no explanations.\\n"
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
        
        # Validation: Check for Universal Modular Layers
        required_keys = ["layer_1_pulse", "layer_2_narrative", "layer_3_blueprint"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys and not data.get("meta"): # If meta exists, maybe it's a valid failure report? No, LLM should return layers.
            # If we have mainly missing keys, assume generation failed or was cut off
            if len(missing_keys) > 1:
                print(f"⚠️ Invalid Report Data: Missing {missing_keys}")
                raise ValueError("LLM response missing required Universal Report layers.")

        # Add/normalize metadata
        data['scenario_type'] = scenario_type
        if 'meta' not in data: 
            data['meta'] = {}
        data['meta']['scenario_type'] = scenario_type
        
        # Calculate fit_score from skill_analysis if scores are present
        skill_analysis = data.get('skill_analysis', [])
        if skill_analysis and any('score' in s for s in skill_analysis):
            scores = [s.get('score', 0) for s in skill_analysis if 'score' in s]
            if scores:
                avg_score = sum(scores) / len(scores)
                data['meta']['fit_score'] = avg_score / 10
            else:
                data['meta']['fit_score'] = 0
        else:
            data['meta']['fit_score'] = 0
        
        # Backward compatibility: map to old structure if needed
        # skill_analysis -> skill_dimension_scores for frontend
        if 'skill_analysis' in data and 'skill_dimension_scores' not in data:
            data['skill_dimension_scores'] = data['skill_analysis']
            
        return data
        
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "scenario_type": scenario_type,
            "meta": {
                "scenario_id": scenario_type,
                "outcome_status": "Failure", 
                "overall_grade": "F",
                "summary": "Error generating report. Please try again."
            },
            "layer_1_pulse": [],
            "layer_2_narrative": {},
            "layer_3_blueprint": {}
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

    def header(self):
        if self.page_no() == 1:
            # Premium gradient header
            self.linear_gradient(0, 0, 210, 40, COLORS['header_grad_1'], COLORS['header_grad_2'], 'H')
            # Main title
            self.set_xy(10, 8)
            self.set_font('Arial', 'B', 24)
            self.set_text_color(255, 255, 255)
            super().cell(0, 10, 'COACT.AI', 0, 0, 'L')
            # Subtitle
            self.set_xy(10, 22)
            self.set_font('Arial', '', 11)
            self.set_text_color(147, 197, 253)
            super().cell(0, 5, 'Coaching & Performance Development Report', 0, 0, 'L')
            # Date on right
            self.set_xy(150, 10)
            self.set_font('Arial', '', 9)
            self.set_text_color(200, 220, 255)
            super().cell(50, 5, dt.datetime.now().strftime('%B %d, %Y'), 0, 0, 'R')
            self.ln(35)
        else:
            # Slim header for subsequent pages
            self.set_fill_color(*COLORS['header_grad_1'])
            self.rect(0, 0, 210, 14, 'F')
            self.set_xy(10, 4)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(255, 255, 255)
            super().cell(100, 6, 'CoAct.AI Report', 0, 0, 'L')
            # Page indicator
            self.set_font('Arial', '', 9)
            self.set_text_color(180, 200, 255)
            super().cell(0, 6, f'Page {self.page_no()}', 0, 0, 'R')
            self.ln(18)

    def check_space(self, h):
        if self.get_y() + h > 270:
            self.add_page()

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
        scenario_labels = {
            "coaching": "COACHING & PERFORMANCE",
            "negotiation": "SALES & NEGOTIATION",
            "reflection": "LEARNING REFLECTION",
            "custom": "CORPORATE SCENARIO",
            "leadership": "LEADERSHIP & STRATEGY",
            "customer_service": "CUSTOMER SERVICE"
        }
        
        accent_color = scenario_colors.get(scenario_type, scenario_colors["custom"])
        scenario_label = scenario_labels.get(scenario_type, scenario_labels["custom"])
        
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
        self.cell(100, 5, f"{icon} {scenario_label}", 0, 1)
        
        # Summary text
        self.set_xy(18, self.get_y() + 3)
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 65, 85)
        self.multi_cell(175, 5, sanitize_text(summary))
        
        # Metrics row with visual indicators
        current_y = self.get_y() + 4
        
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








        score = readiness.get('score', 0)
        next_level = sanitize_text(readiness.get('next_level_requirements', ''))
        timeline = sanitize_text(readiness.get('estimated_timeline', ''))
        
        # Main readiness display
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 10, f"OVERALL READINESS: {label} ({score}/10)", 0, 1)
        
        # Next level requirements (NEW)
        if next_level:
            self.set_fill_color(248, 250, 252) # Slate 50
            self.rect(10, self.get_y(), 190, 25, 'F')
            
            self.set_xy(15, self.get_y() + 5)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['accent'])
            self.cell(0, 5, "NEXT LEVEL REQUIREMENTS:", 0, 1)
            
            self.set_x(15)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(180, 5, next_level)
            
            if timeline:
                self.set_x(15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(*COLORS['text_light'])
                self.cell(0, 5, f"Estimated Timeline: {timeline}", 0, 1)
            
            self.set_y(self.get_y() + 5)
        
        self.ln(5)




    def draw_layer_1_pulse(self, pulse):
        """Draw Layer 1: The Pulse (Metrics)"""
        if not pulse: return
        self.draw_section_header("LAYER 1: THE PULSE", COLORS['section_comm'])
        
        self.ln(2)
        
        # Grid layout simulation using cells
        for metric in pulse:
            name = sanitize_text(metric.get('metric', 'Metric'))
            score = str(metric.get('score', 'N/A'))
            insight = sanitize_text(metric.get('insight', ''))
            
            # Metric Box
            self.set_fill_color(248, 250, 252)
            self.rect(self.get_x(), self.get_y(), 190, 25, 'F')
            
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['secondary'])
            self.cell(190, 6, name.upper(), 0, 1)
            
            # Score
            self.set_font('Arial', 'B', 12)
            if "Expert" in score or (score.replace('.','',1).isdigit() and float(score) >= 8):
                self.set_text_color(*COLORS['success'])
            elif "Beginner" in score or (score.replace('.','',1).isdigit() and float(score) <= 4):
                self.set_text_color(*COLORS['danger'])
            else:
                self.set_text_color(*COLORS['warning'])
            self.cell(190, 6, f"Score: {score}", 0, 1)
            
            # Insight
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(190, 5, insight)
            self.ln(4)

    def draw_layer_2_narrative(self, narrative):
        """Draw Layer 2: The Narrative"""
        if not narrative: return
        self.draw_section_header("LAYER 2: THE NARRATIVE", COLORS['section_skills'])
        
        # Sentiment Curve
        if 'sentiment_curve' in narrative:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['primary'])
            self.cell(0, 8, "AI Sentiment Curve:", 0, 1)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 5, sanitize_text(narrative['sentiment_curve']))
            self.ln(4)
            
        # Critical Pivots
        pivots = narrative.get('critical_pivots', {})
        if pivots.get('green_light'):
            gl = pivots['green_light']
            self.set_fill_color(*COLORS['rewrite_good'])
            self.rect(self.get_x(), self.get_y(), 190, 20, 'F')
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['success'])
            self.cell(190, 6, "GREEN LIGHT MOMENT", 0, 1)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(190, 5, sanitize_text(gl.get('event', '')))
            self.ln(4)
            
        if pivots.get('red_light'):
            rl = pivots['red_light']
            self.set_fill_color(*COLORS['bad_bg'])
            self.rect(self.get_x(), self.get_y(), 190, 20, 'F')
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['danger'])
            self.cell(190, 6, "RED LIGHT MOMENT", 0, 1)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(190, 5, sanitize_text(rl.get('event', '')))
            self.ln(4)

        # Think Aloud
        if 'think_aloud' in narrative:
            ta = narrative['think_aloud']
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['section_skills'])
            self.cell(0, 8, "The 'Think-Aloud' Reveal:", 0, 1)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(0, 5, f"When you said: \"{sanitize_text(ta.get('context',''))}\"")
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['primary'])
            self.multi_cell(0, 5, f"I thought: \"{sanitize_text(ta.get('thought',''))}\"")
            self.ln(4)

    def draw_layer_3_blueprint(self, blueprint):
        """Draw Layer 3: The Blueprint"""
        if not blueprint: return
        self.draw_section_header("LAYER 3: THE BLUEPRINT", COLORS['section_coach'])
        
        # Micro Correction
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['primary'])
        self.cell(90, 8, "Micro-Correction:", 0, 0)
        self.cell(90, 8, "Shadow Impact:", 0, 1)
        
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        
        y = self.get_y()
        self.multi_cell(90, 5, sanitize_text(blueprint.get('micro_correction', 'None')))
        self.set_xy(105, y)
        self.multi_cell(90, 5, sanitize_text(blueprint.get('shadow_impact', 'None')))
        self.ln(6)
        
        # Homework
        if 'homework_exercises' in blueprint:
            self.set_font('Arial', 'B', 10)
            self.cell(0, 8, "Actionable Homework:", 0, 1)
            self.set_font('Arial', '', 9)
            for ex in blueprint.get('homework_exercises', []):
                self.cell(5, 5, "-", 0, 0)
                self.multi_cell(0, 5, sanitize_text(ex))


def generate_report(transcript, role, ai_role, scenario, framework=None, filename="coaching_report.pdf", mode="coaching", precomputed_data=None, scenario_type=None):
    """
    Generate a UNIFIED PDF report for all scenario types.
    """
    # Auto-detect scenario type if not provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    
    print(f"Generating Unified PDF Report (scenario_type: {scenario_type})...")
    
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
    pdf.add_page()
    
    # Get scenario_type from data if available
    scenario_type = data.get('scenario_type', scenario_type)
    
    # 1. Banner with summary
    meta = data.get('meta', {})
    pdf.draw_banner(meta, scenario_type=scenario_type)
    
    # 2. Layer 1: The Pulse
    pulse = data.get('layer_1_pulse', [])
    if pulse:
        pdf.draw_layer_1_pulse(pulse)
        
    # 3. Layer 2: The Narrative
    narrative = data.get('layer_2_narrative', {})
    if narrative:
        pdf.draw_layer_2_narrative(narrative)
        
    # 4. Layer 3: The Blueprint
    blueprint = data.get('layer_3_blueprint', {})
    if blueprint:
        pdf.draw_layer_3_blueprint(blueprint)

    
    pdf.output(filename)
    print(f"✅ Unified report saved: {filename} (scenario: {scenario_type})")

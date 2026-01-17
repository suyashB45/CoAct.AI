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

SCENARIO_TITLES = {
    "coaching": {
        "exec_summary": "PERFORMANCE IN BRIEF",
        "skills": "COACHING COMPETENCIES",
        "tactical": "COACHING MOMENTS",
        "strengths": "EFFECTIVE BEHAVIORS",
         "growth": "DEVELOPMENT OPPORTUNITIES",
        "recs": "DEVELOPMENT PLAN",
        "analytics": "CONVERSATION METRICS"
    },
    "negotiation": {
        "exec_summary": "DEAL OVERVIEW",
        "skills": "NEGOTIATION SKILLS",
        "tactical": "TACTICAL MOVES & COUNTERS",
        "strengths": "WINNING TACTICS",
        "growth": "MISSED OPPORTUNITIES",
        "recs": "STRATEGIC ADJUSTMENTS",
        "analytics": "NEGOTIATION DYNAMICS"
    },
    "reflection": {
        "exec_summary": "REFLECTION SUMMARY",
        "skills": "LEARNING ANALYSIS",
        "tactical": "KEY INSIGHTS",
        "strengths": "SELF-AWARENESS HIGHLIGHTS",
        "growth": "AREAS FOR DEEPER REFLECTION",
        "recs": "JOURNALING & PRACTICE",
        "analytics": "INTERACTION FLOW"
    },
    "custom": {
        "exec_summary": "EXECUTIVE BRIEF",
        "skills": "COMPETENCY MATRIX",
        "tactical": "KEY STAKEHOLDER INTERACTIONS",
        "strengths": "STRATEGIC ASSETS",
        "growth": "PERFORMANCE GAPS",
        "recs": "EXECUTIVE ACTION PLAN",
        "analytics": "ENGAGEMENT METRICS"
    },
    "leadership": {
        "exec_summary": "LEADERSHIP IMPACT BRIEF",
        "skills": "LEADERSHIP COMPETENCIES",
        "tactical": "STRATEGIC MOMENTS",
        "strengths": "VISIONARY TRAITS",
        "growth": "INFLUENCE GAPS",
        "recs": "LEADERSHIP DEVELOPMENT PLAN",
        "analytics": "PRESENCE METRICS"
    },
    "customer_service": {
        "exec_summary": "SERVICE RESOLUTION REPORT",
        "skills": "CLIENT RELATIONS SKILLS",
        "tactical": "SERVICE RECOVERY MOMENTS",
        "strengths": "EMPATHY & PATIENCE",
        "growth": "RESOLUTION GAPS",
        "recs": "SERVICE EXCELLENCE PLAN",
        "analytics": "CUSTOMER SENTIMENT"
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
    
    # NEW THEMES - Sales & Corporate Only
    leadership_keywords = ["strategy", "board", "vision", "roadmap", "stakeholders", "executive", "company direction"]
    customer_service_keywords = ["customer", "complaint", "refund", "service", "angry", "escalation", "support", "ticket"]
    
    combined_text = f"{scenario_lower} {ai_role_lower} {role_lower}"
    
    # Check for reflection first
    if "coach" in ai_role_lower or any(kw in combined_text for kw in reflection_keywords[:3]):
        return "reflection"
    
    # Check specific corporate themes
    if any(kw in combined_text for kw in leadership_keywords):
        return "leadership"
    if any(kw in combined_text for kw in customer_service_keywords):
        return "customer_service"
    
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
    Generate report data with UNIFIED structure for all scenario types.
    
    scenario_type: "coaching" | "negotiation" | "reflection" | "custom"
    - coaching: Staff performance, team management (includes scores)
    - negotiation: Sales, pricing, customer handling (includes scores)  
    - reflection: Learning reflection with coach (no scores, qualitative only)
    - custom: User-defined scenarios (AI decides if scores are appropriate)
    """
    # Auto-detect scenario type if not provided
    if not scenario_type:
        scenario_type = detect_scenario_type(scenario, ai_role, role)
    
    # Determine if this scenario should include numerical scores
    include_scores = scenario_type in ["coaching", "negotiation", "custom", "leadership", "customer_service"]
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    
    if not user_msgs:
        return {
            "meta": {
                "fit_score": 0.0,
                "fit_label": "Starting Out",
                "summary": "Every journey begins with a single step! We're excited to see you start your practice session.",
                "scenario_type": scenario_type
            },
            "executive_summary": {
                "performance_overview": "The session has just begun. Complete your conversation to receive detailed feedback.",
                "key_strengths": [],
                "areas_for_growth": [],
                "recommended_next_steps": "Engage in the conversation and apply your skills."
            },
            "scenario_type": scenario_type
        }

    # Framework Specific Instructions
    framework_context = ""
    if framework:
        framework_context = f"### FOCUS FRAMEWORK: {framework}\\nEvaluate the user's adherence to the principles of {framework}.\\n"
    
    # UNIFIED REPORT STRUCTURE - Same for all scenarios
    score_instruction = ""
    if include_scores:
        score_instruction = """
- **SCORING**: Include numerical scores (0-10) in skill_analysis.
- Each skill should have: dimension, score (0-10), level ("Strong"/"Developing"/"Needs Focus"), interpretation, evidence, improvement_tip
"""
    else:
        score_instruction = """
- **NO SCORES**: Do NOT include numerical scores. Use qualitative levels only.
- Each skill should have: dimension, level ("Strong"/"Developing"/"Needs Focus"), interpretation, evidence, improvement_tip
- STRICTLY FORBIDDEN: Words like "Score", "Grade", "Rating", numbers for evaluation
"""

    unified_instruction = f"""
### UNIFIED REPORT GENERATION
👉 **Purpose**: Generate a comprehensive skill development report.
- **TONE**: Professional, constructive, actionable.
- **SCENARIO TYPE**: {scenario_type.upper()}
{score_instruction}

### OUTPUT JSON STRUCTURE:
{{
  "meta": {{
    "summary": "2-3 sentence overview of the session and key observations.",
    "scenario_type": "{scenario_type}",
    "emotional_trajectory": "e.g., 'Skeptical -> Collaborative' or 'Curious -> Reflective'",
    "session_quality": "Brief quality assessment of the interaction",
    "key_themes": ["Theme 1", "Theme 2", "Theme 3"]
  }},
  "executive_summary": {{
    "performance_overview": "A comprehensive paragraph summarizing overall performance, approach, and impact.",
    "key_strengths": ["Strength 1 with brief explanation", "Strength 2 with brief explanation"],
    "areas_for_growth": ["Area 1 with brief explanation", "Area 2 with brief explanation"],
    "recommended_next_steps": "Specific, actionable guidance for immediate improvement."
  }},
  "skill_analysis": [
    {{ 
      "dimension": "Listening & Empathy", 
      {"\"score\": 7," if include_scores else ""}
      "level": "Strong|Developing|Needs Focus",
      "interpretation": "What was observed...", 
      "evidence": "Direct quote from conversation", 
      "improvement_tip": "Specific actionable advice" 
    }},
    {{ 
      "dimension": "Questioning Quality", 
      {"\"score\": 6," if include_scores else ""}
      "level": "Strong|Developing|Needs Focus",
      "interpretation": "What was observed...", 
      "evidence": "Direct quote", 
      "improvement_tip": "Advice" 
    }},
    {{ 
      "dimension": "Psychological Safety", 
      {"\"score\": 8," if include_scores else ""}
      "level": "Strong|Developing|Needs Focus",
      "interpretation": "What was observed...", 
      "evidence": "Quote", 
      "improvement_tip": "Advice" 
    }},
    {{ 
      "dimension": "Coaching vs Telling", 
      {"\"score\": 5," if include_scores else ""}
      "level": "Strong|Developing|Needs Focus",
      "interpretation": "What was observed...", 
      "evidence": "Quote", 
      "improvement_tip": "Advice" 
    }},
    {{ 
      "dimension": "Overall Effectiveness", 
      {"\"score\": 7," if include_scores else ""}
      "level": "Strong|Developing|Needs Focus",
      "interpretation": "What was observed...", 
      "evidence": "Quote", 
      "improvement_tip": "Advice" 
    }}
  ],
  "tactical_observations": {{
    "success": {{ 
      "moment": "Quote of effective moment...", 
      "analysis": "Why it worked...", 
      "impact": "Effect on conversation", 
      "replication": "How to repeat this" 
    }},
    "risk": {{ 
      "moment": "Quote of risky moment...", 
      "analysis": "Why it was problematic...", 
      "alternative": "Better approach", 
      "prevention": "How to avoid" 
    }}
  }},
  "observed_strengths": [
    {{ 
      "title": "Strength Name", 
      "observation": "Detailed observation of the strength in action...",
      "business_impact": "How this strength benefits outcomes"
    }}
  ],
  "growth_opportunities": [
    {{ 
      "title": "Opportunity Name", 
      "observation": "What was noticed...", 
      "suggestion": "How to improve...",
      "practice_method": "Specific exercise or approach"
    }}
  ],
  "personalized_recommendations": {{
    "immediate_actions": ["Action 1", "Action 2"],
    "focus_areas": ["Focus 1 with context", "Focus 2 with context"],
    "reflection_prompts": [
      "What was the other person really trying to achieve?",
      "How might the conversation change if you paused longer?",
      "What assumptions did you make that you could question?"
    ],
    "practice_suggestions": [
      {{ "action": "Practice action", "frequency": "How often", "success_indicator": "How to know it's working" }}
    ]
  }},
  "learning_outcome": "A brief, inspiring statement about what the user achieved or learned (optional, primarily for Reflection scenarios).",
  "conversation_analytics": {{
    "total_exchanges": <number>,
    "user_talk_time_percentage": <0-100>,
    "question_to_statement_ratio": "<ratio string>",
    "emotional_tone_progression": "Description of emotional arc"
  }}
}}
"""

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
            "meta": {"summary": "Error generating report. Please try again.", "scenario_type": scenario_type},
            "executive_summary": {
                "performance_overview": "Report generation encountered an error.",
                "key_strengths": [],
                "areas_for_growth": [],
                "recommended_next_steps": "Please try generating the report again."
            }
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

    def draw_tactical_observations(self, obs):
        if not obs: return
        self.check_space(80)
        
        self.draw_section_header(self.get_title("tactical"), COLORS['section_skills'])
        
        success = obs.get('success', {})
        risk = obs.get('risk', {})
        
        # Success Card
        self.set_fill_color(240, 253, 244) # Green 50
        self.rect(10, self.get_y(), 190, 35, 'F')
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['success'])
        self.set_xy(15, self.get_y() + 5)
        self.cell(80, 5, "SUCCESS MOMENT", 0, 1)
        
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(85, 4, f'"{sanitize_text(success.get("moment", ""))}"')
        
        # Impact and replication
        impact = success.get('impact', '')
        replication = success.get('replication', '')
        if impact:
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_light'])
            self.set_x(15)
            self.multi_cell(85, 3, f"Impact: {sanitize_text(impact)}")
        if replication:
            self.set_x(15)
            self.multi_cell(85, 3, f"Replicate by: {sanitize_text(replication)}")
        
        # Risk Card (Right side)
        risk_y = self.get_y() - 35
        self.set_fill_color(254, 242, 242) # Red 50
        self.rect(105, risk_y, 95, 35, 'F')
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['danger'])
        self.set_xy(110, risk_y + 5)
        self.cell(85, 5, "IMPROVEMENT AREA", 0, 1)
        
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(110)
        self.multi_cell(85, 4, f'"{sanitize_text(risk.get("moment", ""))}"')
        
        # Alternative and prevention
        alternative = risk.get('alternative', '')
        prevention = risk.get('prevention', '')
        if alternative:
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_light'])
            self.set_x(110)
            self.multi_cell(85, 3, f"Try instead: {sanitize_text(alternative)}")
        if prevention:
            self.set_x(110)
            self.multi_cell(85, 3, f"Prevent by: {sanitize_text(prevention)}")
        
        self.ln(10)

    def draw_manager_recommendations(self, recs):
        if not recs: return
        self.check_space(60)
        
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(10, self.get_y(), 190, 55, 'F')
        
        self.set_xy(15, self.get_y() + 5)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "ACTIONABLE RECOMMENDATIONS", 0, 1)
        
        # Immediate Action
        self.set_font('Arial', 'B', 9)
        self.set_text_color(147, 197, 253) # Blue 300
        self.cell(45, 6, "IMMEDIATE ACTION:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, sanitize_text(recs.get('immediate_action', '')), 0, 1)
        
        # Next Practice
        self.set_font('Arial', 'B', 9)
        self.set_text_color(147, 197, 253)
        self.cell(45, 6, "NEXT PRACTICE:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, sanitize_text(recs.get('next_simulation', '')), 0, 1)
        
        # Development Focus (NEW)
        focus = recs.get('development_focus', '')
        if focus:
            self.set_font('Arial', 'B', 9)
            self.set_text_color(147, 197, 253)
            self.cell(45, 6, "FOCUS AREA:", 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, sanitize_text(focus), 0, 1)
        
        # Timeline and Success Metrics (NEW)
        timeline = recs.get('timeline', '')
        metrics = recs.get('success_metrics', '')
        if timeline or metrics:
            self.ln(2)
            if timeline:
                self.set_font('Arial', 'I', 8)
                self.set_text_color(203, 213, 225) # Slate 300
                self.cell(0, 5, f"Timeline: {sanitize_text(timeline)}", 0, 1)
            if metrics:
                self.set_font('Arial', 'I', 8)
                self.set_text_color(203, 213, 225)
                self.cell(0, 5, f"Success Metrics: {sanitize_text(metrics)}", 0, 1)
        
        self.ln(10)

    def draw_readiness_indicator(self, readiness):
        if not readiness: return
        self.check_space(40)
        self.ln(5)
        
        label = sanitize_text(readiness.get('label', 'N/A'))
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


    def draw_score_chart(self, scores):
        if not scores: return
        self.check_space(80)
        self.ln(5)
        
        self.draw_section_header("SKILL ASSESSMENT VISUALIZATION", COLORS['primary'])
        
        # Chart Settings
        chart_x = 20
        chart_y = self.get_y()
        chart_w = 170
        bar_h = 8
        gap = 4
        max_score = 10
        
        # Draw Axis Line
        self.set_draw_color(200, 200, 200)
        self.line(chart_x + 40, chart_y, chart_x + 40, chart_y + (len(scores) * (bar_h + gap)))
        
        for i, item in enumerate(scores):
            dim = sanitize_text(item.get('dimension', ''))
            score = item.get('score', 0)
            
            y_pos = chart_y + (i * (bar_h + gap))
            
            # Label
            self.set_xy(chart_x, y_pos + 1)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['text_main'])
            self.cell(38, 6, dim, 0, 0, 'R')
            
            # Bar Background
            self.set_fill_color(241, 245, 249)
            self.rect(chart_x + 41, y_pos, chart_w - 41, bar_h, 'F')
            
            # Bar Foreground with gradient effect
            bar_len = ((chart_w - 41) * score) / max_score
            if score >= 8: 
                bar_color = COLORS['success']
            elif score >= 5: 
                bar_color = COLORS['warning']
            else: 
                bar_color = COLORS['danger']
            
            self.set_fill_color(*bar_color)
            self.rect(chart_x + 41, y_pos, bar_len, bar_h, 'F')
            
            # Add subtle highlight on bar
            self.set_fill_color(255, 255, 255)
            self.set_draw_color(255, 255, 255)
            self.rect(chart_x + 41, y_pos, bar_len, 2, 'F')
            self.set_fill_color(*bar_color)
            self.rect(chart_x + 41, y_pos + 1, bar_len, 1, 'F')
            
            # Score Label with circle
            score_x = chart_x + 41 + bar_len + 3
            self.set_fill_color(*bar_color)
            self.ellipse(score_x, y_pos + 1, 6, 6, 'F')
            self.set_xy(score_x, y_pos + 1)
            self.set_font('Arial', 'B', 7)
            self.set_text_color(255, 255, 255)
            self.cell(6, 6, f"{int(score)}", 0, 0, 'C')

        # Add target line at score 7
        target_x = chart_x + 41 + ((chart_w - 41) * 7) / max_score
        self.set_draw_color(100, 116, 139)
        self.set_line_width(0.3)
        self.dashed_line(target_x, chart_y - 2, target_x, chart_y + (len(scores) * (bar_h + gap)), 2, 1)
        self.set_xy(target_x - 8, chart_y - 6)
        self.set_font('Arial', '', 6)
        self.set_text_color(100, 116, 139)
        self.cell(16, 4, 'Target: 7', 0, 0, 'C')
        self.set_line_width(0.2)

        self.set_y(chart_y + (len(scores) * (bar_h + gap)) + 8)


    # --- LEARNING DETAILS ---
    
    def draw_learning_outcome(self, outcome):
        if not outcome: return
        self.check_space(30)
        self.ln(5)
        
        self.set_fill_color(236, 253, 245) # Emerald 50
        self.rect(10, self.get_y(), 190, 25, 'F')
        
        self.set_xy(15, self.get_y() + 5)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['success'])
        self.cell(0, 6, "LEARNING OUTCOME", 0, 1)
        
        self.set_x(15)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(6, 78, 59) # Emerald 900
        self.multi_cell(180, 5, sanitize_text(outcome))
        self.ln(10)

    # --- SHARED DRAWING METHODS ---
    def draw_observed_strengths(self, strengths):
        if not strengths: return
        self.check_space(60)
        self.draw_section_header(self.get_title("strengths"), COLORS['success'])
        
        for strength in strengths:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['success'])
            title = sanitize_text(strength.get('title', ''))
            self.cell(0, 6, f"> {title}", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.set_x(15)
            observation = sanitize_text(strength.get('observation', ''))
            self.multi_cell(0, 5, observation)
            self.ln(3)
        self.ln(5)

    def draw_coaching_opportunities(self, opportunities):
        if not opportunities: return
        self.check_space(60)
        self.draw_section_header(self.get_title("growth"), COLORS['warning'])
        
        for opp in opportunities:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['warning'])
            title = sanitize_text(opp.get('title', ''))
            self.cell(0, 6, f"-> {title}", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.set_x(15)
            observation = sanitize_text(opp.get('observation', ''))
            self.multi_cell(0, 5, observation)
            self.ln(3)

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
    
    # 2. Executive Summary
    exec_summary = data.get('executive_summary', {})
    if exec_summary:
        pdf.draw_executive_summary(exec_summary)
    
    # 3. Conversation Analytics
    analytics = data.get('conversation_analytics', {})
    if analytics:
        pdf.draw_conversation_analytics(analytics)
    
    # 4. Skill Analysis (Unified Table + Chart)
    scores = data.get('skill_analysis', []) or data.get('skill_dimension_scores', [])
    if scores:
        has_scores = any('score' in s for s in scores)
        # Always use draw_assessment_table, toggling score column
        pdf.draw_assessment_table(scores, show_scores=has_scores)
        
        if has_scores:
            pdf.draw_score_chart(scores)
    
    # 5. Tactical Observations
    tactical = data.get('tactical_observations', {})
    if tactical:
        pdf.draw_tactical_observations(tactical)
    
    # 6. Strengths
    strengths = data.get('observed_strengths', [])
    if strengths:
        pdf.draw_observed_strengths(strengths)
    
    # 7. Growth Opportunities
    opportunities = data.get('growth_opportunities', [])
    if opportunities:
        pdf.draw_coaching_opportunities(opportunities)
    
    # 8. Personalized Recommendations
    recs = data.get('personalized_recommendations', {})
    if recs:
        pdf.draw_personalized_recommendations(recs)
        
    # 9. Learning Outcome (Legacy/Reflection)
    outcome = data.get('learning_outcome', '')
    if outcome:
        pdf.draw_learning_outcome(outcome)
    
    pdf.output(filename)
    print(f"✅ Unified report saved: {filename} (scenario: {scenario_type})")

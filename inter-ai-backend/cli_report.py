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

def sanitize_text(text):
    if text is None: return ""
    text = str(text)
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2022': '-', '\u2026': '...'
    }
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    try:
        return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    except:
        return text.encode('latin-1', 'replace').decode('latin-1')

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

def analyze_full_report_data(transcript, role, ai_role, scenario, framework=None, mode="coaching"):
    # Prepare conversation for analysis
    conversation_text = "\n".join([f"{t['role'].upper()}: {t['content']}" for t in transcript])
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    user_messages_text = "\n".join([f"USER: {t['content']}" for t in user_msgs])
    
    msg_count = len(transcript)
    user_turn_count = len(user_msgs)
    session_status = "COMPLETE" if msg_count >= 10 else "INCOMPLETE" # Lowered threshold for testing
    
    if not user_msgs:
        return {
            "meta": {
                "fit_score": 0.0,
                "fit_label": "Starting Out",
                "summary": "Every journey begins with a single step! We're excited to see you start your coaching practice."
            },
            "sidebar_data": {"top_traits": ["Courage to begin"], "improvements": ["Session engagement"]},
            "mode": mode
        }

    # Directional signal mapping helper
    directional_labels = {
        "0-3": "Starting Out",
        "4-5": "Developing", 
        "6-7": "Consistent",
        "8-10": "Fluent"
    }

    # Framework Specific Instructions
    framework_context = ""
    if framework:
         framework_context = f"### FOCUS FRAMEWORK: {framework}\nEvaluate the user's adherence to the principles of {framework}.\n"
    
    if mode == "evaluation":
        system_prompt = (
            f"### SYSTEM ROLE\n"
            f"You are a STRICT PERFORMANCE EVALUATOR assessing a high-stakes roleplay simulation.\n"
            f"Context: {scenario}\n"
            f"User Role: {role} | AI Role: {ai_role}\n"
            f"Mode: EVALUATION (Graded Assessment)\n"
            f"{framework_context}\n"
            f"### INSTRUCTIONS\n"
            "Analyze the conversation to provide a formal Performance Evaluation.\n"
            "Focus on Competency, Skill Benchmarking, and ROI.\n"
            "BE STRICT. Do not sugarcoat grades.\n"
            "Identify the exact turn where your behavior shifted (e.g., 'At Turn 4, I became more open because...').\n\n"
            f"### REPORT SECTIONS\n"
            "1. **Scoring Table**: Grade the user (0-10) on Rapport, Needs Discovery, Objection Mastery, and Outcome Effectiveness. Cite specific evidence.\n"
            "2. **Overall Grade**: Calculate a weighted percentage.\n"
            "3. **Tactical Observations**: Identify one specific SUCCESS turn and one RISK turn.\n"
            "4. **Manager Recommendations**: Assign immediate actions and next simulation levels.\n"
            "5. **Business Impact**: Estimate ROI and Risk Level (Low/Medium/High).\n"
            "6. **Competency Gap**: Compare User Score vs Top Performer Benchmark (0-10) for 3 critical skills.\n"
            "7. **Risk Flags**: Identify specific behavioral risks (e.g., 'Interrupting', 'Passive').\n\n"
            "### OUTPUT FORMAT (Strict JSON)\n"
            "{\n"
            "  \"meta\": {\n"
            "    \"summary\": <string Executive Summary>,\n"
            "    \"overall_grade\": <int 0-100>,\n"
            "    \"status\": <string 'Ready'/'Developing'/'Action Required'>\n"
            "  },\n"
            "  \"scoring_table\": [\n"
            "      { \"dimension\": \"Rapport & Connection\", \"score\": <int 0-10>, \"evidence\": <string specific observation> },\n"
            "      { \"dimension\": \"Needs Discovery\", \"score\": <int 0-10>, \"evidence\": <string specific observation> },\n"
            "      { \"dimension\": \"Objection Mastery\", \"score\": <int 0-10>, \"evidence\": <string specific observation> },\n"
            "      { \"dimension\": \"Outcome Effectiveness\", \"score\": <int 0-10>, \"evidence\": <string specific observation> }\n"
            "  ],\n"
            "  \"competency_gap\": [\n"
            "      { \"skill\": \"...\", \"user_score\": <int>, \"benchmark_score\": <int> }\n"
            "  ],\n"
            "  \"risk_flags\": [\"...\", \"...\"],\n"
            "  \"tactical_observations\": {\n"
            "      \"success\": { \"moment\": <string quote/desc>, \"analysis\": <string why it worked> },\n"
            "      \"risk\": { \"moment\": <string quote/desc>, \"analysis\": <string why it failed> }\n"
            "  },\n"
            "  \"turning_point_analysis\": {\n"
            "      \"turn_number\": <int>,\n"
            "      \"description\": <string e.g. 'At Turn 4, I shifted because...'>\n"
            "  },\n"
            "  \"business_impact\": {\n"
            "      \"projected_roi\": <string e.g. 'High'>,\n"
            "      \"risk_level\": <string e.g. 'Low'>,\n"
            "      \"comment\": <string impact analysis>\n"
            "  },\n"
            "  \"manager_recommendations\": {\n"
            "      \"immediate_action\": <string specific resource/step>,\n"
            "      \"next_simulation\": <string recommendation for next practice>\n"
            "  }\n"
            "}"
        )
    else:
        # COACHING MODE
        system_prompt = (
            f"### SYSTEM ROLE\n"
            f"You are clear, identifying behavioral patterns and asking Socratic questions.\n"
            f"Context: {scenario}\n"
            f"User Role: {role} | AI Role: {ai_role}\n"
            f"Mode: COACHING (Developmental)\n"
            f"{framework_context}\n"
            f"### INSTRUCTIONS\n"
            "Focus on Personal Development & Mastery.\n"
            "Do NOT use assessment language (Score, Grade, Pass/Fail).\n"
            "Use Socratic methods to encourage self-reflection.\n"
            "Identify the exact turn where your behavior shifted (e.g., 'At Turn 4, I became more open because...').\n"
            "Rewrite specific user lines to be more effective (Micro-Coaching).\n"
            "**TERMINOLOGY GUIDE:**\n"
            "- Use 'Professional Environment' or 'Workplace Dynamics' (avoid 'Corporate').\n"
            "- Use 'Conversational Fluency' (avoid 'Benchmark').\n"
            "- Use 'Contextual Best Practices' (avoid 'Requirements').\n\n"
            "### REPORT SECTIONS\n"
            "1. **Executive Summary**: High-level overview.\n"
            "2. **Observed Strengths**: Evidence-based wins.\n"
            "3. **Coaching Opportunities**: Areas for improvement.\n"
            "4. **Conversation Reframes**: 'You said X — here is how it could be reframed'.\n"
            "5. **Practice Prompts**: Specific drills (e.g., 'Try this...').\n"
            "6. **Behavioral Patterns**: Recurring habits.\n"
            "7. **Impact Reflection**: How the user's approach affected stakeholders.\n\n"
            "### OUTPUT FORMAT (Strict JSON)\n"
            "{\n"
            "  \"meta\": {\n"
            "    \"summary\": <string High-level summary of the session theme>\n"
            "  },\n"
            "  \"overall_alignment\": { \"score\": <int 0-10>, \"label\": <string e.g. 'Consistent'> },\n"
            "  \"skill_snapshot\": [\n"
            "      { \"skill\": \"...\", \"score\": <int>, \"label\": <string 'Fluent'/'Consistent'/'Developing'>, \"evidence\": \"...\" }\n"
            "  ],\n"
            "  \"eq_matrix\": [\n"
            "      { \"trait\": \"Empathy Display\", \"score\": <int>, \"observation\": \"...\" },\n"
            "      { \"trait\": \"Emotional Regulation\", \"score\": <int>, \"observation\": \"...\" },\n"
            "      { \"trait\": \"De-escalation\", \"score\": <int>, \"observation\": \"...\" }\n"
            "  ],\n"
            "  \"observed_strengths\": [\"...\", \"...\"],\n"
            "  \"coaching_opportunities\": [\n"
            "      { \"observation\": \"...\", \"suggestion\": \"...\" }\n"
            "  ],\n"
            "  \"conversation_reframes\": [\n"
            "      { \"original\": \"...\", \"suggested_reframe\": \"...\", \"why\": \"...\" }\n"
            "  ],\n"
            "  \"practice_prompts\": [\"...\", \"...\"],\n"
            "  \"behavioral_patterns\": [\n"
            "      { \"observation\": <string>, \"insight\": <string> }\n"
            "  ],\n"
            "  \"socratic_lens\": [\n"
            "      { \"question\": <string>, \"purpose\": <string e.g. 'Aimed at intent'> }\n"
            "  ],\n"
            "  \"skill_focus\": [\n"
            "      { \"skill\": <string>, \"description\": <string> }\n"
            "  ],\n"
            "  \"practice_drills\": [\n"
            "      { \"drill\": <string name>, \"instruction\": <string> }\n"
            "  ],\n"
            "  \"micro_coaching\": [\n"
            "      { \"quote\": <string original>, \"better\": <string improved>, \"why\": <string> }\n"
            "  ],\n"
            "  \"impact_reflection\": <string>,\n"
            "  \"sidebar_data\": { \"top_traits\": [\"Trait 1\", \"Trait 2\"] },\n"
            "  \"turning_point_analysis\": {\n"
            "      \"turn_number\": <int>,\n"
            "      \"description\": <string e.g. 'At Turn 4, I shifted because...'>\n"
            "  }\n"
            "}"
        )

    try:
        # Create clearly separated sections for the LLM
        # Full conversation for context
        full_conversation = "\n".join([f"{'USER' if t['role'] == 'user' else 'ASSISTANT'}: {t['content']}" for t in transcript])
        
        # Extract ONLY user messages for focused analysis
        user_only_messages = "\n".join([f"USER: {t['content']}" for t in transcript if t['role'] == 'user'])
        
        # Build the analysis input with clear separation
        analysis_input = f"""### FULL CONVERSATION (For Context Only)
{full_conversation}

### USER'S MESSAGES ONLY (Analyze ONLY These)
{user_only_messages}
"""
        
        response = llm_reply([
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": analysis_input}
        ])
        clean_text = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Add common meta
        data['mode'] = mode
        if 'meta' not in data: data['meta'] = {}
        data['meta']['fit_score'] = data['meta'].get('overall_grade', 0) / 10 if mode == 'evaluation' else 0
        
        return data
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        # Fallback empty structure
        return {"mode": mode, "meta": {"summary": "Error generating report."}}

class DashboardPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Generated by CoAct AI Coaching Engine', 0, 0, 'C')

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
            self.linear_gradient(0, 0, 210, 35, COLORS['header_grad_1'], COLORS['header_grad_2'], 'H')
            self.set_xy(10, 10)
            self.set_font('Arial', 'B', 20)
            self.set_text_color(255, 255, 255)
            self.cell(0, 10, 'COACT.AI', 0, 0, 'L')
            self.set_xy(10, 22)
            self.set_font('Arial', '', 10)
            self.set_text_color(147, 197, 253)
            self.cell(0, 5, 'Skill Development Reflection', 0, 0, 'L')
            self.ln(30)
        else:
            self.set_fill_color(*COLORS['header_grad_1'])
            self.rect(0, 0, 210, 12, 'F')
            self.set_xy(10, 3)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, 'Skill Development Reflection', 0, 0, 'L')
            self.ln(15)

    def draw_banner(self, meta):
        summary = meta.get('summary', '')
        
        self.set_y(self.get_y() + 5)
        start_y = self.get_y()
        
        # 1. Main Card Background
        self.set_fill_color(252, 253, 255) # Almost white
        self.set_draw_color(241, 245, 249) # Slate 100
        self.rect(10, start_y, 190, 40, 'DF')
        
        # 2. Accent Bar (Left)
        # self.set_fill_color(*COLORS['primary'])
        # self.rect(10, start_y, 4, 40, 'F')
        
        # 3. Executive Summary
        self.set_xy(15, start_y + 8)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(148, 163, 184) # Slate 400
        self.cell(100, 5, "EXECUTIVE SUMMARY", 0, 1)
        
        self.set_xy(15, self.get_y() + 2)
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 65, 85) # Slate 700
        self.multi_cell(180, 5, sanitize_text(summary))
        
        self.set_y(start_y + 50)

    def draw_coaching_with_sidebar(self, strengths, opportunities, prompts, sidebar_data):
        start_y = self.get_y()
        left_w, right_x, side_w = 135, 145, 55
        
        self.set_xy(10, start_y)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(left_w, 8, "OBSERVED STRENGTHS", 0, 1)
        self.set_font('Arial', '', 10)
        for s in strengths[:3]:
            self.set_x(15)
            self.multi_cell(left_w - 10, 5, "- " + sanitize_text(s))
        
        self.ln(5)
        self.set_x(10)
        self.set_font('Arial', 'B', 12)
        self.cell(left_w, 8, "GROWTH OPPORTUNITIES", 0, 1)
        for opp in opportunities[:2]:
            self.set_x(15)
            self.set_font('Arial', 'B', 9)
            self.multi_cell(left_w - 10, 5, sanitize_text(opp.get('observation')))
            self.set_x(15)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(left_w - 10, 5, "Try: " + sanitize_text(opp.get('suggestion')))
            self.ln(2)

        # Sidebar
        final_y = self.get_y()
        self.set_fill_color(*COLORS['sidebar_bg'])
        self.rect(right_x, start_y, side_w, max(final_y - start_y, 100), 'F')
        self.set_xy(right_x + 3, start_y + 5)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(side_w - 6, 6, "BEHAVIORAL REFLECTION", 0, 1)
        self.set_font('Arial', '', 8)
        for t in sidebar_data.get('top_traits', [])[:3]:
            self.set_x(right_x + 3)
            self.cell(0, 5, "> " + sanitize_text(t), 0, 1)
        self.set_y(final_y + 10)

    def draw_skill_snapshot(self, skill_snapshot):
        """Draw skill reflection with directional signals instead of numerical scores."""
        if not skill_snapshot: return
        self.check_space(80)
        self.ln(8)
        
        self.set_fill_color(*COLORS['accent'])
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "SKILL REFLECTION", 0, 1)
        self.ln(3)
        
        # Signal to color mapping
        signal_colors = {
            'Starting Out': COLORS['danger'],
            'Developing': COLORS['warning'],
            'Consistent': COLORS['success'],
            'Fluent': (16, 185, 129)  # Emerald for mastery
        }
        
        for skill in skill_snapshot[:4]:
            name = sanitize_text(skill.get('name', ''))
            signal = skill.get('signal', 'Developing')
            text = sanitize_text(skill.get('text', ''))
            
            color = signal_colors.get(signal, COLORS['warning'])
            
            # Skill row with directional signal
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(80, 5, name, 0, 0)
            self.set_text_color(*color)
            self.set_font('Arial', 'B', 9)
            self.cell(40, 5, signal.upper(), 0, 1)
            
            # Feedback
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*COLORS['text_light'])
            if len(text) > 120: text = text[:117] + "..."
            self.set_x(15)
            self.multi_cell(0, 4, text)
            self.ln(4)


    def draw_behavioral_analysis(self, behavioral_cards):
        if not behavioral_cards: return
        self.check_space(60)
        self.ln(5)
        
        self.set_fill_color(139, 92, 246)  # Purple
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "BEHAVIORAL ANALYSIS", 0, 1)
        self.ln(3)
        
        for card in behavioral_cards[:3]:
            name = sanitize_text(card.get('name', ''))
            score = float(card.get('score', 0))
            text = sanitize_text(card.get('text', ''))
            
            if score >= 7: color = COLORS['success']
            elif score >= 5: color = COLORS['warning']
            else: color = COLORS['danger']
            
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(80, 5, name, 0, 0)
            self.set_text_color(*color)
            self.cell(20, 5, f"{score:.1f}/10", 0, 1)
            
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*COLORS['text_light'])
            if len(text) > 80: text = text[:77] + "..."
            self.set_x(15)
            self.cell(0, 5, text, 0, 1)
            self.ln(2)

    def draw_practice_prompts(self, prompts):
        if not prompts: return
        self.check_space(40)
        self.ln(5)
        self.set_fill_color(*COLORS['accent'])
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "SKILL DEVELOPMENT REFLECTION: NEXT STEPS", 0, 1)
        self.ln(2)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        for p in prompts[:5]:
            self.set_x(15)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['text_main'])
            self.cell(16, 5, "Try this: ", 0, 0)
            
            self.set_font('Arial', '', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(160, 5, sanitize_text(p))
            self.ln(2)

    def draw_impact_reflection(self, text):
        if not text: return
        self.check_space(30)
        self.ln(5)
        self.set_fill_color(*COLORS['section_eq']) # Pink for impact/empathy
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "IMPACT REFLECTION", 0, 1)
        self.ln(2)
        
        self.set_x(15)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*COLORS['text_main'])
        self.multi_cell(180, 5, sanitize_text(text))
        self.ln(5)

    def draw_reframes(self, reframes):
        if not reframes: return
        self.check_space(60)
        self.ln(8)
        
        self.set_fill_color(245, 158, 11)  # Amber
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "CONVERSATION COACHING INSIGHTS", 0, 1)
        self.ln(3)

        for item in reframes[:3]:
            # Support both old and new keys for resilience
            orig = sanitize_text(item.get('original') or item.get('you_said', ''))
            reframe = sanitize_text(item.get('suggested_reframe') or item.get('coach_reframe', ''))
            why = sanitize_text(item.get('why') or item.get('logic', ''))

            # You Said
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(15, 5, "You said: ", 0, 0)
            self.set_text_color(*COLORS['text_main']) # Same color
            self.multi_cell(0, 5, f'"{orig}"')
            
            # Reframe
            self.set_x(10)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['success'])
            self.cell(27, 5, "Coach Reframe: ", 0, 0)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(0, 5, f'"{reframe}"')

            # Logic
            self.set_x(10)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(0, 4, f"Why this works: {why}")
            self.ln(4)

    def draw_eq_matrix(self, eq_data):
        if not eq_data: return
        self.check_space(70)
        self.ln(5)
        
        # Header
        self.set_fill_color(236, 72, 153) # Pink 500
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "EMOTIONAL INTELLIGENCE DEEP DIVE", 0, 1)
        self.ln(4)
        
        # Grid Layout
        y_start = self.get_y()
        # We have 5 items. Let's do 2 columns.
        
        col_width = 90
        row_height = 25
        
        for i, item in enumerate(eq_data):
            row = i // 2
            col = i % 2
            
            x = 10 + (col * (col_width + 10))
            y = y_start + (row * (row_height + 5))
            
            # Use check_space if we run out (unlikely with just 5 items but good practice)
            if y + row_height > 275:
                self.add_page()
                y = self.get_y()
                # reset
            
            # Card Background
            self.set_fill_color(255, 255, 255)
            self.set_draw_color(226, 232, 240)
            self.rect(x, y, col_width, row_height, 'DF')
            
            # Title
            trait = sanitize_text(item.get('trait', 'EQ Trait'))
            score = int(item.get('score', 0))
            text = sanitize_text(item.get('text', ''))
            
            # Color code based on score
            if score >= 8: 
                bar_color = COLORS['success']
                level = "Strong"
            elif score >= 5: 
                bar_color = COLORS['warning']
                level = "Developing"
            else: 
                bar_color = COLORS['danger']
                level = "Focus Area"
                
            self.set_xy(x + 3, y + 3)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['primary'])
            self.cell(45, 5, trait, 0, 0)
            
            # Score Label
            self.set_text_color(*bar_color)
            self.set_font('Arial', 'B', 8)
            self.cell(40, 5, f"{level} ({score}/10)", 0, 1, 'R')
            
            # Text
            self.set_xy(x + 3, y + 9)
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_light'])
            # Truncate text to fit
            if len(text) > 90: text = text[:87] + "..."
            self.multi_cell(col_width - 6, 4, text)
            
            # Mini Bar at bottom
            self.set_fill_color(*bar_color)
            self.rect(x, y + row_height - 1.5, col_width * (score/10), 1.5, 'F')
            
        self.set_y(y_start + (3 * (row_height + 5)))

    def draw_turning_point(self, turning_point):
        if not turning_point: return
        self.check_space(60)
        self.ln(8)
        
        # Header
        occurred = turning_point.get('occurred', False)
        color = COLORS['success'] if occurred else COLORS['warning']
        self.set_fill_color(*color)
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "THE TURNING POINT", 0, 1)
        
        status = "A beautiful breakthrough moment!" if occurred else "Your next breakthrough is waiting - keep practicing!"
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_light'])
        self.cell(0, 5, status, 0, 1)
        self.ln(3)
        
        # Quote the moment if it happened
        if occurred and turning_point.get('moment'):
            y = self.get_y()
            self.set_fill_color(236, 253, 245)  # Emerald 50
            self.rect(10, y, 190, 15, 'F')
            self.set_xy(15, y + 3)
            self.set_font('Arial', 'I', 10)
            self.set_text_color(*COLORS['success'])
            moment = sanitize_text(turning_point.get('moment', ''))
            if len(moment) > 150: moment = moment[:147] + "..."
            self.multi_cell(180, 5, f'"{moment}"')
            self.ln(3)
        
        # Before/After states
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['danger'])
        self.cell(30, 5, "BEFORE:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(0, 5, sanitize_text(turning_point.get('before_state', '')), 0, 1)
        
        # Fixed "AFTER:" logic or text
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['success'])
        self.cell(30, 5, "AFTER:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(0, 5, sanitize_text(turning_point.get('after_state', '')), 0, 1)
        
        self.ln(2)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_light'])
        self.multi_cell(0, 5, sanitize_text(turning_point.get('analysis', '')))
        self.ln(5)

    def draw_vocabulary_coaching(self, vocab):
        if not vocab: return
        self.check_space(60)
        self.ln(5)
        
        # Header
        self.set_fill_color(139, 92, 246)  # Violet 500
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "VOCABULARY COACHING", 0, 1)
        self.ln(5)
        
        y_start = self.get_y()
        col_w = 90
        col_h = 35 # Fixed height for cards
        
        # Backgrounds
        # Green Column
        self.set_fill_color(240, 253, 244) # Green 50
        self.rect(10, y_start, col_w, col_h, 'F')
        # Red Column
        self.set_fill_color(254, 242, 242) # Red 50
        self.rect(10 + col_w + 5, y_start, col_w, col_h, 'F')
        
        # Lean In (Left)
        self.set_xy(15, y_start + 4)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['success'])
        self.cell(80, 5, "LEAN IN (Use More)", 0, 1)
        
        lean_in = vocab.get('lean_in_phrases', [])
        self.set_font('Arial', '', 9)
        self.set_text_color(22, 101, 52) # Green 800
        for p in lean_in[:3]:
            self.set_x(15)
            self.cell(5, 5, "+", 0, 0)
            self.cell(80, 5, sanitize_text(p), 0, 1)
            
        # Lean Away (Right)
        self.set_xy(10 + col_w + 10, y_start + 4)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['danger'])
        self.cell(80, 5, "LEAN AWAY (Avoid)", 0, 1)
        
        lean_away = vocab.get('lean_away_phrases', [])
        self.set_font('Arial', '', 9)
        self.set_text_color(153, 27, 27) # Red 800
        for p in lean_away[:3]:
            self.set_x(10 + col_w + 10)
            self.cell(5, 5, "-", 0, 0)
            self.cell(80, 5, sanitize_text(p), 0, 1)
            
        # Tip
        self.set_xy(10, y_start + col_h + 5)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_light'])
        tip = vocab.get('coaching_tip', '')
        if tip:
            self.multi_cell(0, 5, f"TIP: {sanitize_text(tip)}")
            
        self.ln(5)


    def draw_reflection_guide(self, questions):
        if not questions: return
        self.check_space(50)
        self.ln(5)
        
        self.set_xy(16, self.get_y())

    # --- NEW METHODS FOR SEPARATE REPORTS ---

    # 1. EVALUATION REPORT METHODS
    def draw_evaluation_table(self, scoring_table):
        if not scoring_table: return
        self.check_space(80)
        self.ln(5)
        
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 10, "PERFORMANCE SCORING", 0, 1)
        self.ln(2)

        # Header
        self.set_fill_color(241, 245, 249)
        self.set_font('Arial', 'B', 9)
        self.cell(60, 8, "DIMENSION", 1, 0, 'L', True)
        self.cell(20, 8, "SCORE", 1, 0, 'C', True)
        self.cell(110, 8, "EVIDENCE & LOGIC", 1, 1, 'L', True)

        for row in scoring_table:
            dim = row.get('dimension', '')
            score = row.get('score', 0)
            evidence = row.get('evidence', '')

            self.set_font('Arial', 'B', 9)
            self.cell(60, 20, dim, 1, 0, 'L')
            
            # Score Color
            if score >= 8: self.set_text_color(*COLORS['success'])
            elif score >= 5: self.set_text_color(*COLORS['warning'])
            else: self.set_text_color(*COLORS['danger'])
            
            self.cell(20, 20, f"{score}/10", 1, 0, 'C')
            
            self.set_text_color(*COLORS['text_main'])
            self.set_font('Arial', '', 8)
            
            # Multi-cell inside cell hack
            current_x = self.get_x()
            current_y = self.get_y()
            self.multi_cell(110, 5, sanitize_text(evidence), border=0)
            # Draw border around it
            self.set_xy(current_x + 110, current_y)
            self.rect(current_x, current_y, 110, 20) 
            self.ln(20) # Move down row height

        self.ln(5)

    def draw_tactical_observations(self, obs):
        if not obs: return
        self.check_space(60)
        
        success = obs.get('success', {})
        risk = obs.get('risk', {})
        
        # Success Card
        self.set_fill_color(240, 253, 244) # Green 50
        self.rect(10, self.get_y(), 90, 50, 'F')
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['success'])
        self.set_xy(15, self.get_y() + 5)
        self.cell(80, 5, "SUCCESS MOMENT", 0, 1)
        
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(80, 4, f"\"{sanitize_text(success.get('moment'))}\"")
        self.ln(2)
        self.set_font('Arial', '', 9)
        self.set_x(15)
        self.multi_cell(80, 4, sanitize_text(success.get('analysis')))
        
        # Risk Card (Right side)
        y_start = self.get_y() - 50 if self.get_y() > 50 else self.get_y()
        # Be careful with Y coord here, relative to previous rect
        # Let's just fix Y for both to be safe
        current_y = self.get_y()
        
        # We need to backtrack Y to draw side-by-side
        # Simplified: Just draw them stacked if complex, or side by side carefully
        # Let's stack them for safety in FPDF
        
        self.ln(5)
        
        # Risk Card
        self.set_fill_color(254, 242, 242) # Red 50
        self.rect(10, self.get_y(), 190, 30, 'F') # Full width stack
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['danger'])
        self.set_xy(15, self.get_y() + 5)
        self.cell(180, 5, "RISK MOMENT", 0, 1)
        
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(180, 4, f"\"{sanitize_text(risk.get('moment'))}\"")
        self.ln(2)
        self.set_font('Arial', '', 9)
        self.set_x(15)
        self.multi_cell(180, 4, sanitize_text(risk.get('analysis')))
        self.ln(10)

    def draw_manager_recommendations(self, recs):
        if not recs: return
        self.check_space(50)
        
        self.set_fill_color(30, 41, 59) # Slate 800
        self.rect(10, self.get_y(), 190, 40, 'F')
        
        self.set_xy(15, self.get_y() + 5)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, "MANAGER RECOMMENDATIONS", 0, 1)
        
        self.set_font('Arial', 'B', 9)
        self.set_text_color(147, 197, 253) # Blue 300
        self.cell(40, 6, "IMMEDIATE ACTION:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, sanitize_text(recs.get('immediate_action')), 0, 1)
        
        self.ln(2)
        
        self.set_font('Arial', 'B', 9)
        self.set_text_color(147, 197, 253)
        self.cell(40, 6, "NEXT SIMULATION:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, sanitize_text(recs.get('next_simulation')), 0, 1)
        
        self.ln(10)

    # 2. COACHING REPORT METHODS
    def draw_behavioral_patterns(self, patterns):
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 10, "BEHAVIORAL PATTERNS", 0, 1)
        
        for p in patterns:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['accent'])
            self.cell(5, 5, ">", 0, 0)
            self.cell(0, 5, sanitize_text(p.get('observation')), 0, 1)
            
            self.set_x(15)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(0, 5, sanitize_text(p.get('insight')))
            self.ln(3)
    
    def draw_socratic_lens(self, questions):
        self.ln(5)
        self.set_fill_color(240, 249, 255) # Sky 50
        self.rect(10, self.get_y(), 190, len(questions)*20 + 10, 'F')
        
        self.set_xy(15, self.get_y()+5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "THE SOCRATIC LENS (Reflection)", 0, 1)
        
        for q in questions:
            self.set_x(15)
            self.set_font('Arial', 'I', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(180, 5, "? " + sanitize_text(q.get('question')))
            
            self.set_x(15)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['accent'])
            self.cell(0, 5, f"AIMED AT: {sanitize_text(q.get('purpose'))}", 0, 1)
            self.ln(3)
        self.ln(5)
    
    def draw_skill_focus(self, skills):
        self.check_space(50)
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "SKILL FOCUS AREAS", 0, 1)
        
        y = self.get_y()
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(226, 232, 240)
        
        col_w = 90
        for i, skill in enumerate(skills[:2]):
            x = 10 if i == 0 else 110
            self.rect(x, y, col_w, 30)
            
            self.set_xy(x+5, y+5)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['primary'])
            self.cell(col_w-10, 5, sanitize_text(skill.get('skill')), 0, 1)
            
            self.set_xy(x+5, y+12)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(col_w-10, 4, sanitize_text(skill.get('description')))
        
        self.set_y(y + 35)

    def draw_practice_drills(self, drills):
        self.check_space(40)
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(245, 158, 11) # Amber
        self.cell(0, 8, "PRACTICE DRILLS (Micro-Habits)", 0, 1)
        
        for drill in drills:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['text_main'])
            self.cell(40, 6, sanitize_text(drill.get('drill')) + ":", 0, 0)
            
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 6, sanitize_text(drill.get('instruction')))
            self.ln(2)

        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "REFLECTION GUIDE", 0, 1)
        self.ln(3)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        for i, q in enumerate(questions[:3]):
            self.set_x(15)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['accent'])
            self.cell(8, 6, f"{i+1}.", 0, 0)
            self.set_font('Arial', '', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(170, 6, sanitize_text(q))
            self.ln(2)
        self.ln(5)

    def draw_skill_bars(self, skills):
        """Draws Linear Progress Bars for skills (0-10 score)."""
        if not skills: return
        self.check_space(80)
        self.ln(5)
        
        # Title
        self.set_fill_color(248, 250, 252)
        self.set_draw_color(226, 232, 240)
        
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "SKILL SNAPSHOT", 0, 1)
        self.ln(3)
        
        for skill in skills:
            name = sanitize_text(skill.get('name', ''))
            score = int(skill.get('score', 0))
            text = sanitize_text(skill.get('text', ''))
            
            # Color Logic
            if score >= 8:
                bar_color = COLORS['success']
                label_color = COLORS['success']
            elif score >= 5:
                bar_color = COLORS['warning']
                label_color = COLORS['warning'] 
            else:
                bar_color = COLORS['danger']
                label_color = COLORS['danger']

            # Percentage for bar width (0-10 -> 0-100%)
            percentage = min(max(score * 10, 5), 100)
            
            # Card Box (Background)
            self.check_space(35)
            y_start = self.get_y()
            self.set_fill_color(248, 250, 252) # Very light slate
            self.set_draw_color(226, 232, 240)
            self.rect(10, y_start, 190, 30, 'FD')
            
            # Text Content
            self.set_xy(15, y_start + 4)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['primary'])
            self.cell(100, 5, name, 0, 0)
            
            # Score Label
            self.set_x(160)
            self.set_text_color(*label_color)
            self.set_font('Arial', 'B', 9)
            self.cell(30, 5, f"{score}/10", 0, 1, 'R')
            
            # Bar Background
            self.set_xy(15, y_start + 11)
            self.set_fill_color(226, 232, 240)
            self.rect(15, self.get_y(), 180, 4, 'F')
            
            # Bar Fill
            self.set_fill_color(*bar_color)
            self.rect(15, self.get_y(), 180 * (percentage/100), 4, 'F')
            
            # Description
            self.set_xy(15, y_start + 18)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(180, 4, text)
            
            self.set_y(y_start + 35)

    def draw_radar_chart(self, skills):
        # ... kept for legacy or alternative ...
        pass

    def draw_line_chart(self, title, data, color, y_label="Score"):
        """Generic simple line chart"""
        if not data or len(data) < 2: return
        self.check_space(60)
        self.ln(5)
        
        # Header
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, title, 0, 1)
        
        # Chart Specs
        h = 40
        w = 160
        x_start = 25
        y_start = self.get_y() + h
        
        # Draw Axes
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(x_start, self.get_y(), x_start, y_start) # Y
        self.line(x_start, y_start, x_start + w, y_start) # X
        
        # Max/Min for scaling
        max_val = max(data)
        if max_val == 0: max_val = 1
        
        step_x = w / (len(data) - 1)
        
        self.set_draw_color(*color)
        self.set_line_width(0.8)
        
        prev_x, prev_y = -1, -1
        
        for i, val in enumerate(data):
            # Scale Y (assuming 0 to max_val)
            normalized_h = (val / max_val) * h if max_val > 0 else 0
            x = x_start + (i * step_x)
            y = y_start - normalized_h
            
            if i > 0:
                self.line(prev_x, prev_y, x, y)
            
            # Point
            self.set_fill_color(*color)
            self.rect(x-0.8, y-0.8, 1.6, 1.6, 'F')
            
            prev_x, prev_y = x, y
            
        self.ln(h + 10)

    def dashed_line(self, x1, y1, x2, y2, dash_length=1, space_length=1):
        """Draw a dashed line"""
        self.set_line_width(0.1)
        self.set_draw_color(200, 200, 200)
        total_len = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        if total_len == 0: return
        
        dx = (x2 - x1) / total_len
        dy = (y2 - y1) / total_len
        
        cur_len = 0
        while cur_len < total_len:
            curr_x = x1 + dx * cur_len
            curr_y = y1 + dy * cur_len
            
            next_len = min(cur_len + dash_length, total_len)
            next_x = x1 + dx * next_len
            next_y = y1 + dy * next_len
            
            self.line(curr_x, curr_y, next_x, next_y)
            cur_len += dash_length + space_length

    def draw_business_impact(self, impact_data):
        if not impact_data: return
        self.draw_section_header("BUSINESS IMPACT ANALYSIS", COLORS['text_dark'])
        
        # Grid Layout
        start_y = self.get_y()
        self.set_line_width(0.3)
        self.set_draw_color(200, 200, 200)
        
        # Projected ROI
        self.set_xy(10, start_y)
        self.set_fill_color(*COLORS['accent_light'])
        self.cell(95, 12, " PROJECTED ROI", border=0, fill=True, ln=0)
        self.set_xy(10, start_y + 12)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*COLORS['success'])
        self.cell(95, 12, f" {impact_data.get('projected_roi', 'N/A')}", border='LBR', ln=0)
        
        # Risk Level
        self.set_xy(105, start_y)
        self.set_fill_color(*COLORS['risk_light'])
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLORS['text_light']) # Reset text color for header
        self.cell(95, 12, " RISK LEVEL", border=0, fill=True, ln=0)
        self.set_xy(105, start_y + 12)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*COLORS['risk'])
        self.cell(95, 12, f" {impact_data.get('risk_level', 'N/A')}", border='LBR', ln=1)
        
        # Comment
        self.ln(5)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*COLORS['text_gray'])
        self.multi_cell(0, 6, f"Coach's Note: {impact_data.get('comment', '')}")
        self.ln(8)

    def draw_micro_coaching(self, coaching_list):
        if not coaching_list: return
        self.draw_section_header("MICRO-COACHING: LINE-BY-LINE", COLORS['accent'])
        
        for item in coaching_list:
            # Container
            self.set_fill_color(250, 250, 250)
            self.rect(10, self.get_y(), 190, 35, 'F')
            
            # Original Quote
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(180, 50, 50) # Red
            self.cell(20, 8, "YOU SAID:", 0, 0)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*COLORS['text_gray'])
            self.multi_cell(0, 8, f'"{item.get("quote", "")}"')
            
            # Better Version
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*COLORS['success']) 
            self.cell(20, 8, "TRY THIS:", 0, 0)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*COLORS['text_dark'])
            self.multi_cell(0, 8, item.get("better", ""))
            
            # Why
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*COLORS['text_gray'])
            self.multi_cell(0, 6, f"Thinking: {item.get('why', '')}")
            
            self.ln(4)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def draw_competency_gap(self, gaps):
        if not gaps: return
        self.draw_section_header("COMPETENCY GAP ANALYSIS (User vs Top Performer)", COLORS['primary'])
        
        self.set_font('Helvetica', '', 9)
        y = self.get_y()
        
        for item in gaps:
            skill = item.get('skill', 'Skill')
            user_score = item.get('user_score', 0)
            bench_score = item.get('benchmark_score', 9)
            
            # Label
            self.set_text_color(*COLORS['text_main'])
            self.cell(40, 6, sanitize_text(skill), 0, 0)
            
            # Bar Chart
            bar_start_x = 55
            max_w = 100
            
            # User Bar
            self.set_fill_color(*COLORS['primary'])
            self.rect(bar_start_x, y+1, user_score * 10, 4, 'F')
            
            # Benchmark Bar (Ghosted)
            self.set_fill_color(200, 200, 200)
            self.rect(bar_start_x, y+6, bench_score * 10, 2, 'F')
            
            # Scores
            self.set_x(bar_start_x + max_w + 5)
            self.cell(20, 10, f"{user_score} / {bench_score}", 0, 1)
            
            y += 12
            self.set_y(y)
        self.ln(5)

    def draw_risk_flags(self, flags):
        self.draw_section_header("BEHAVIORAL RISK FLAGS", COLORS['risk'])
        
        if not flags:
            self.set_font('Helvetica', 'I', 10)
            self.set_text_color(*COLORS['success'])
            self.cell(0, 10, "No critical behavioral risks detected.", 0, 1)
        else:
            for flag in flags:
                self.set_fill_color(*COLORS['risk_light'])
                self.set_text_color(*COLORS['risk'])
                self.set_font('Helvetica', 'B', 10)
                
                # Warning Icon equivalent
                self.cell(10, 8, "!", 0, 0, 'C', fill=True)
                self.cell(0, 8, f"  {sanitize_text(flag)}", 0, 1, fill=True)
                self.ln(2)
        self.ln(8)


def generate_report(transcript, role, ai_role, scenario, framework=None, filename="coaching_report.pdf", mode="coaching", precomputed_data=None):
    print(f"Generating PDF Report ({mode})...")
    
    # Analyze data or use precomputed
    if precomputed_data:
        data = precomputed_data
        # Ensure mode is set in data if missing
        if 'mode' not in data: data['mode'] = mode
    else:
        print("Generating new report data...")
        data = analyze_full_report_data(transcript, role, ai_role, scenario, framework, mode)
    
    # Sanitize all string data recursively to avoid Unicode errors
    def sanitize_data(obj):
        if isinstance(obj, str):
            return sanitize_text(obj)
        elif isinstance(obj, dict):
            return {k: sanitize_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize_data(item) for item in obj]
        return obj
    
    data = sanitize_data(data)
    
    pdf = DashboardPDF()
    pdf.add_page()
    
    # Common Header
    pdf.draw_banner(data.get('meta', {}))
    
    # Conditional Reporting based on Mode
    if mode == "evaluation":
        # 1. Scoring Table
        pdf.draw_evaluation_table(data.get('scoring_table', []))
        
        # 2. Competency Gap (New)
        pdf.draw_competency_gap(data.get('competency_gap', []))

        # 3. Business Impact
        pdf.draw_business_impact(data.get('business_impact', {}))
        
        # 4. Risk Flags (New)
        pdf.draw_risk_flags(data.get('risk_flags', []))
        
        # 5. Tactical Observations (Success/Risk)
        pdf.draw_tactical_observations(data.get('tactical_observations', {}))
        
        # 6. Manager Recommendations
        pdf.draw_manager_recommendations(data.get('manager_recommendations', {}))
        
        # 7. Turning Point
        pdf.draw_turning_point(data.get('turning_point_analysis', {})) # Updated key
        
        # 8. EQ Deep Dive (Still relevant for evaluation)
        pdf.draw_eq_matrix(data.get('eq_matrix', []))
        
    else:
        # COACHING MODE (Default)
        
        # 1. Observed Strengths (New)
        pdf.draw_observed_strengths(data.get('observed_strengths', []))
        
        # 2. Coaching Opportunities (New)
        pdf.draw_coaching_opportunities(data.get('coaching_opportunities', []))
        
        # 3. Conversation Reframes (Micro-Coaching)
        # Check both keys for backward compatibility
        reframes = data.get('conversation_reframes', []) or data.get('micro_coaching', [])
        pdf.draw_reframes(reframes) 
        
        # 4. Practice Prompts/Drills
        prompts = data.get('practice_prompts', []) or data.get('practice_drills', [])
        pdf.draw_practice_prompts(prompts)
        
        # 5. Impact Reflection
        pdf.draw_impact_reflection(data.get('impact_reflection', ''))

        # 6. Behavioral Patterns (Supplemental)
        pdf.draw_behavioral_patterns(data.get('behavioral_patterns', []))
        
        # 7. Socratic Lens (Supplemental)
        pdf.draw_socratic_lens(data.get('socratic_lens', []))
        
        # 8. EQ Matrix & Turning Point (Universal value)
        pdf.draw_eq_matrix(data.get('eq_matrix', []))
        pdf.draw_turning_point(data.get('turning_point_analysis', {}))

    # New Data Charts (These can be common to both modes if desired, or moved inside conditional blocks)
    if data.get('pace_data'):
        pdf.draw_line_chart("COMMUNICATION VOLUME (Words per Turn)", data.get('pace_data'), COLORS['accent'], "Words")
        
    if data.get('sentiment_arc'):
         pdf.draw_line_chart("SENTIMENT ANALYSIS (Emotional Flow)", data.get('sentiment_arc'), COLORS['success'], "Sentiment")

    pdf.draw_turning_point(data.get('turning_point'))
    pdf.draw_vocabulary_coaching(data.get('vocabulary_coaching'))
    pdf.draw_reflection_guide(data.get('reflection_guide', []))
    # pdf.draw_transcript(transcript) # REMOVED per user request for privacy
    pdf.output(filename)
    print(f"Saved: {filename}")
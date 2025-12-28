import json
import os
import math
import unicodedata
import datetime as dt
from fpdf import FPDF
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

USE_AZURE = True 
def setup_client():
    try:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if USE_AZURE and api_key and endpoint:
            return AzureOpenAI(
                api_key=api_key,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
                azure_endpoint=endpoint
            )
        elif os.getenv("OPENAI_API_KEY"):
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        print(f"Warning: Failed to initialize AI client: {e}")
    return None

# client = setup_client()  <-- REMOVED top-level call to prevent import crashes
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# --- Premium Blue Palette ---
COLORS = {
    'text_main': (33, 37, 41),
    'text_light': (108, 117, 125),
    'white': (255, 255, 255),
    
    # Brand Colors
    'primary': (30, 58, 138),    # Navy Blue
    'secondary': (100, 116, 139), # Slate
    'accent': (37, 99, 235),     # Royal Blue
    
    # Gradients & UI
    'header_grad_1': (30, 58, 138),
    'header_grad_2': (59, 130, 246),
    'score_grad_1': (220, 252, 231), 
    'score_grad_2': (187, 247, 208),
    'score_text': (21, 128, 61),
    
    'divider': (226, 232, 240),
    'bg_light': (248, 250, 252),
    'bg_gray': (241, 245, 249),
    'bar_track': (226, 232, 240),
    'bar_empty': (229, 231, 235),
    'card_border': (203, 213, 225),
    'sidebar_bg': (240, 249, 255),
    
    # Status
    'success': (22, 163, 74),
    'warning': (245, 158, 11),
    'danger': (220, 38, 38),
    'rewrite_bad': (254, 242, 242), 
    'rewrite_good': (240, 253, 244),
    'bad_bg': (254, 226, 226), 
    'bad_text': (153, 27, 27),
    'grey_bg': (229, 231, 235), 'grey_text': (107, 114, 128)
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
    client = setup_client()
    if not client:
        print("LLM Error: No API credentials found. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in backend/.env")
        return "{}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME, messages=messages, max_tokens=max_tokens, temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return "{}"

def analyze_full_report_data(transcript, role, ai_role, scenario):
    conversation_text = "\n".join([f"{t['role'].upper()}: {t['content']}" for t in transcript])
    msg_count = len(transcript)
    session_status = "COMPLETE" if msg_count >= 30 else "INCOMPLETE"
    
    last_question = "None"
    if transcript and transcript[-1]['role'] == 'assistant':
        last_question = transcript[-1]['content']
    
    user_msgs = [t for t in transcript if t['role'] == 'user']
    if not user_msgs:
        # Hard-fail if no user input
        return {
            "meta": {
                "fit_score": 0.0,
                "fit_label": "No Participation",
                "potential_score": 0.0,
                "summary": "The user did not participate in the session."
            },
            "sidebar_data": {"top_traits": [], "improvements": ["Participation"], "motivators": [], "derailers": ["Non-participation"]},
            "functional_cards": [], "behavioral_cards": [], "chatberry_analysis": {}, "coach_rewrite_card": {}, "learning_plan": {}, "qa_analysis": [], "strategic_advice": {}
        }

    incomplete_instruction = ""
    if session_status == "INCOMPLETE":
        incomplete_instruction = (
            f"IMPORTANT: Session INCOMPLETE (stopped at: '{last_question}').\n"
            "1. **Strict Penalty**: If < 3 user turns, Max Score = 2.0. If < 5 turns, Max Score = 4.0.\n"
            "2. In 'qa_analysis', include this last question. Set score: 0, feedback: 'Not Answered'.\n"
        )

    system_prompt = (
        f"### SYSTEM ROLE\n"
        f"You are CoAct, a STRICT and UNCOMPROMISING Evaluation Engine. Analyze the roleplay for role: '{role}'.\n"
        f"Context: {scenario} | Status: {session_status}\n"
        f"{incomplete_instruction}\n\n"
        f"### SCORING RULES (0.0 - 10.0 Scale)\n"
        "1. **Fit Score**: BE HARSH. Average performance = 4.0-5.0. Good = 6.0-7.0. Excellent (>8.0) requires PERFECTION.\n"
        "2. **Q&A Evaluation**: Penalize dodging, vagueness, or fluff heavily. If they don't answer the core conflict, score < 3.0.\n"
        "3. **Feedback Tone**: Be direct, critical, and professional. Do not sugarcoat. Point out every missing nuance.\n"
        "4. **Linguistic**: Analyze 7 specific metrics: Vocabulary, Grammar, Coherence, Discourse Markers, Accuracy, Register, Content.\n"
        "   (Do NOT generate a CEFR score).\n\n"
        "### OUTPUT FORMAT (Strict JSON)\n"
        "{\n"
        "  \"meta\": {\n"
        "    \"fit_score\": 7.5,\n"
        "    \"fit_label\": \"Proficient\",\n"
        "    \"potential_score\": 8.2,\n"
        "    \"summary\": \"Executive summary...\"\n"
        "  },\n"
        "  \"sidebar_data\": {\n"
        "    \"top_traits\": [\"Trait 1\", \"Trait 2\", \"Trait 3\"],\n"
        "    \"improvements\": [\"Area 1\", \"Area 2\"],\n"
        "    \"motivators\": [\"M1\", \"M2\"],\n"
        "    \"derailers\": [\"D1\", \"D2\"]\n"
        "  },\n"
        "  \"functional_cards\": [\n"
        "    { \"name\": \"Skill Name\", \"score\": 7.0, \"text\": \"Feedback...\" }\n"
        "  ],\n"
        "  \"behavioral_cards\": [\n"
        "    { \"name\": \"Trait Name\", \"score\": 7.8, \"text\": \"Definition...\" }\n"
        "  ],\n"
        "  \"chatberry_analysis\": {\n"
        "    \"analysis_text\": \"Paragraph describing communication style...\",\n"
        "    \"metrics\": [\n"
        "      { \"label\": \"Vocabulary\", \"score\": 7.0 },\n"
        "      { \"label\": \"Grammar\", \"score\": 6.0 },\n"
        "      { \"label\": \"Coherence\", \"score\": 6.5 },\n"
        "      { \"label\": \"Discourse Markers\", \"score\": 6.0 },\n"
        "      { \"label\": \"Accuracy\", \"score\": 7.0 },\n"
        "      { \"label\": \"Register\", \"score\": 7.0 },\n"
        "      { \"label\": \"Content\", \"score\": 6.0 }\n"
        "    ]\n"
        "  },\n"
        "  \"coach_rewrite_card\": {\n"
        "    \"title\": \"Instant Fix\",\n"
        "    \"context\": \"Context...\",\n"
        "    \"original_user_response\": \"Original...\",\n"
        "    \"pro_rewrite\": \"Rewrite...\",\n"
        "    \"why_it_works\": \"Why...\"\n"
        "  },\n"
        "  \"learning_plan\": {\n"
        "    \"priority_focus\": \"Focus...\",\n"
        "    \"recommended_drill\": \"Drill...\",\n"
        "    \"suggested_reading\": \"Reading...\"\n"
        "  },\n"
        "  \"qa_analysis\": [\n"
        "    { \"question\": \"Q1 Text...\", \"answer\": \"User answer...\", \"feedback\": \"Critique...\", \"score\": 6.5 }\n"
        "  ],\n"
        "  \"strategic_advice\": {\n"
        "    \"conflict_diagnosis\": \"Why this persona is difficult (e.g., 'High resistance to change due to fear of incompetence').\",\n"
        "    \"step_by_step\": [\"Step 1: Validate...\", \"Step 2: Reframe...\", \"Step 3: Close...\"],\n"
        "    \"power_phrase\": \"One sentence that would instantly disarm this specific character.\"\n"
        "  }\n"
        "}"
    )

    try:
        response = llm_reply([
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": conversation_text}
        ])
        clean_text = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return {}

class DashboardPDF(FPDF):
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

    def get_multicell_height(self, width, text, font_size=9, line_height=5):
        if not text: return 0
        self.set_font('Arial', '', font_size)
        lines = len(self.multi_cell(width, line_height, sanitize_text(text), split_only=True))
        return lines * line_height

    def header(self):
        # Header is called automatically by add_page
        if self.page_no() == 1:
            self.linear_gradient(0, 0, 210, 25, COLORS['header_grad_1'], COLORS['header_grad_2'], 'H')
            self.set_xy(10, 8)
            self.set_font('Arial', 'B', 16)
            self.set_text_color(255, 255, 255)
            self.cell(0, 10, 'COACT.AI DASHBOARD', 0, 0, 'L')
            self.set_xy(-60, 8)
            self.set_font('Arial', '', 9)
            self.cell(50, 10, dt.datetime.now().strftime('%Y-%m-%d | %H:%M'), 0, 0, 'R')
            self.ln(25)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 8)
        self.set_text_color(*COLORS['text_light'])
        self.cell(0, 10, f'Page {self.page_no()} - Generated by CoAct.ai', 0, 0, 'C')

    def check_space(self, height):
        if self.get_y() + height > 275:
            self.add_page()
            return True
        return False

    def draw_section_title(self, title):
        self.check_space(15)
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['text_main'])
        self.cell(0, 8, sanitize_text(title).upper(), 0, 1, 'L')
        self.set_fill_color(*COLORS['primary'])
        self.rect(10, self.get_y(), 10, 1, 'F')
        self.ln(5)

    def draw_banner(self, meta):
        fit = float(meta.get('fit_score', 0))
        pot = float(meta.get('potential_score', 0))
        label = meta.get('fit_label', 'Developing')
        summary = meta.get('summary', '')
        
        bg, txt = get_score_theme(fit)
        
        summary_h = self.get_multicell_height(130, summary, 10)
        box_h = max(55, summary_h + 30)
        
        self.check_space(box_h)
        y = self.get_y()
        
        self.linear_gradient(10, y, 190, box_h, COLORS['score_grad_1'], COLORS['score_grad_2'], 'V')
        
        self.set_xy(15, y+8)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['score_text'])
        self.cell(40, 5, "FIT SCORE", 0, 1, 'C')
        
        self.set_xy(15, y+18)
        self.set_font('Arial', 'B', 32)
        self.cell(40, 10, f"{fit:.1f}", 0, 1, 'C')
        
        self.set_xy(15, y+30)
        self.set_font('Arial', 'B', 9)
        self.cell(40, 5, label.upper(), 0, 0, 'C')
        
        self.set_xy(15, y+40)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*COLORS['primary'])
        self.cell(40, 5, f"Potential: {pot:.1f}", 0, 0, 'C')
        
        self.set_draw_color(255, 255, 255)
        self.set_line_width(1)
        self.line(60, y+5, 60, y+box_h-5)
        
        self.set_xy(65, y+8)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['score_text'])
        self.cell(100, 5, "EXECUTIVE SUMMARY", 0, 1)
        
        self.set_xy(65, y+16)
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        self.multi_cell(130, 6, sanitize_text(summary))
        
        self.set_y(y + box_h + 10)

    def draw_skill_cards_with_sidebar(self, func_cards, beh_cards, sidebar_data):
        # Calculate roughly how much height we need for the entire section.
        # This prevents the sidebar from being cut in half across pages.
        est_height = 20 + ((len(func_cards) + len(beh_cards)) * 30)
        self.check_space(est_height)
        
        start_y = self.get_y()
        left_width = 130
        right_start = 150
        
        # --- LEFT: Skills ---
        self.set_xy(10, start_y)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['text_main'])
        self.cell(left_width, 8, "FUNCTIONAL & BEHAVIORAL SKILLS", 0, 1)
        self.ln(2)
        
        current_y = self.get_y()
        all_cards = func_cards + beh_cards
        
        for card in all_cards:
            # Note: We rely on the initial check_space to ensure this fits.
            # If list is huge (unlikely), FPDF might overflow, but for standard 4-6 skills this is safe.
            
            name = sanitize_text(card.get('name', 'Skill'))
            desc = sanitize_text(card.get('text', ''))
            score = float(card.get('score', 0))
            
            self.set_xy(10, current_y)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['primary'])
            self.cell(50, 5, name, 0, 0)
            
            # Bar Track
            self.set_fill_color(*COLORS['bar_track'])
            self.rect(60, current_y+1, 60, 3, 'F')
            
            # Progress
            self.set_fill_color(*get_bar_color(score))
            self.rect(60, current_y+1, (score/10)*60, 3, 'F')
            
            # Score
            self.set_xy(125, current_y)
            self.set_font('Arial', 'B', 9)
            self.cell(10, 5, f"{score:.1f}", 0, 1)
            
            # Desc
            self.set_xy(10, current_y + 6)
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(left_width - 5, 4, desc)
            
            current_y = self.get_y() + 4
            self.set_y(current_y)

        final_y = self.get_y()
        
        # --- RIGHT: Sidebar ---
        # Ensures sidebar matches content height or min 130mm
        sidebar_height = max(final_y - start_y, 130)
        
        self.set_xy(right_start, start_y)
        self.set_fill_color(*COLORS['sidebar_bg'])
        self.rect(right_start, start_y, 50, sidebar_height, 'F')
        
        self.set_xy(right_start + 2, start_y + 5)
        
        def draw_side_sec(title, items, icon):
            self.set_x(right_start + 2)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['primary'])
            self.cell(45, 6, title, 0, 1)
            self.set_font('Arial', '', 8)
            self.set_text_color(*COLORS['text_main'])
            for it in items[:3]:
                clean_it = sanitize_text(it)
                if len(clean_it) > 23: clean_it = clean_it[:21] + ".."
                self.set_x(right_start + 2)
                self.cell(3, 5, icon, 0, 0)
                self.cell(42, 5, clean_it, 0, 1)
            self.ln(2)

        draw_side_sec("TOP TRAITS", sidebar_data.get('top_traits', []), ">")
        draw_side_sec("AREAS OF IMPV.", sidebar_data.get('improvements', []), "!")
        draw_side_sec("MOTIVATORS", sidebar_data.get('motivators', []), "*")
        draw_side_sec("DERAILERS", sidebar_data.get('derailers', []), "-")
        
        self.set_y(max(final_y, start_y + sidebar_height) + 10)

    def draw_chatberry_analysis(self, cb_data):
        if not cb_data: return
        self.check_space(100)
        self.draw_section_title("COMMUNICATION & LINGUISTICS")
        y = self.get_y()
        
        analysis = sanitize_text(cb_data.get('analysis_text', ''))
        h_text = self.get_multicell_height(190, analysis) + 15
        
        self.set_fill_color(*COLORS['bg_light'])
        self.rect(10, y, 190, h_text, 'F')
        
        self.set_xy(15, y+5)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['primary'])
        self.cell(180, 5, "COMMUNICATION STYLE SUMMARY", 0, 1)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(180, 5, analysis)
        
        y += h_text + 10
        self.set_y(y)
        
        metrics = cb_data.get('metrics', [])
        col_w = 46 
        row_h = 25
        
        for i, m in enumerate(metrics):
            r = i // 4
            c = i % 4
            curr_x = 10 + (c * (col_w + 2))
            curr_y = y + (r * (row_h + 2))
            
            label = sanitize_text(m.get('label', ''))
            score = float(m.get('score', 0))
            
            self.set_fill_color(255, 255, 255)
            self.set_draw_color(*COLORS['card_border'])
            self.rect(curr_x, curr_y, w=col_w, h=row_h, style='DF')
            
            self.set_xy(curr_x + 2, curr_y + 2)
            self.set_font('Arial', 'B', 14)
            self.set_text_color(*COLORS['text_main'])
            self.cell(col_w-4, 8, f"{int(score)}/10", 0, 1)
            
            self.set_xy(curr_x + 2, curr_y + 10)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(col_w-4, 4, label)
            
        self.set_y(y + (2 * row_h) + 15)

    def draw_rewrite_card(self, card):
        if not card: return
        self.check_space(60)
        self.draw_section_title("COACH'S INSTANT FIX")
        
        orig = sanitize_text(card.get('original_user_response', ''))
        pro = sanitize_text(card.get('pro_rewrite', ''))
        why = sanitize_text(card.get('why_it_works', ''))
        
        h_orig = self.get_multicell_height(85, orig, 9)
        h_pro = self.get_multicell_height(85, pro, 9)
        h_box = max(h_orig, h_pro) + 25
        
        y = self.get_y()
        
        # Left
        self.set_fill_color(*COLORS['rewrite_bad'])
        self.rect(10, y, 90, h_box, 'F')
        self.set_xy(15, y+5)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['danger'])
        self.cell(80, 5, "YOU SAID:", 0, 1)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(80, 5, orig)
        
        # Right
        self.set_fill_color(*COLORS['rewrite_good'])
        self.rect(110, y, 90, h_box, 'F')
        self.set_xy(115, y+5)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['success'])
        self.cell(80, 5, "PRO REWRITE:", 0, 1)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(115)
        self.multi_cell(80, 5, pro)
        
        # Footer
        y_why = y + h_box + 5
        self.set_xy(10, y_why)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(10, 5, "Why:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_light'])
        self.multi_cell(170, 5, why)
        
        self.set_y(y_why + 15)

    def draw_learning_plan(self, plan):
        if not plan: return
        self.check_space(40)
        self.draw_section_title("LEARNING PLAN")
        y = self.get_y()
        
        self.set_fill_color(*COLORS['bg_light'])
        self.rect(10, y, 190, 30, 'F')
        
        focus = sanitize_text(plan.get('priority_focus', ''))
        drill = sanitize_text(plan.get('recommended_drill', ''))
        read = sanitize_text(plan.get('suggested_reading', ''))
        
        self.set_xy(15, y+5)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(30, 6, "Focus:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(100, 6, focus, 0, 1)
        
        self.set_x(15)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(30, 6, "Drill:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(100, 6, drill, 0, 1)
        
        self.set_x(15)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(30, 6, "Reading:", 0, 0)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(100, 6, read, 0, 1)
        
        self.set_y(y + 40)

    def draw_qa_card(self, qa_item):
        self.check_space(50)
        self.draw_section_title("Q&A ANALYSIS")
        
        q = sanitize_text(qa_item.get('question', ''))
        summ = sanitize_text(qa_item.get('answer', ''))
        feed = sanitize_text(qa_item.get('feedback', ''))
        score = float(qa_item.get('score', 0))
        
        if score == 0.0:
            score_txt = "NOT ANSWERED"
            bg, txt = COLORS['bad_bg'], COLORS['bad_text']
        else:
            score_txt = f"{score:.1f}/10"
            bg, txt = COLORS['bg_gray'], COLORS['text_light']

        h_q = self.get_multicell_height(180, q)
        h_sum = self.get_multicell_height(180, summ)
        h_feed = self.get_multicell_height(180, feed)
        
        box_h = h_q + h_sum + h_feed + 45
        y = self.get_y()
        
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*COLORS['card_border'])
        self.rect(10, y, 190, box_h, 'DF')
        
        self.set_xy(15, y+5)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['primary'])
        self.multi_cell(180, 5, f"Q: {q}")
        
        curr_y = self.get_y() + 2
        self.set_draw_color(240, 240, 240)
        self.line(15, curr_y, 195, curr_y)
        
        self.set_xy(15, curr_y + 5)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(*COLORS['accent'])
        self.cell(20, 5, "ANSWER:", 0, 1)
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(180, 5, summ)
        
        # Feedback Container
        curr_y = self.get_y() + 5
        self.set_fill_color(*bg)
        # Extra padding for feedback box
        self.rect(12, curr_y, 186, h_feed + 15, 'F')
        
        self.set_xy(15, curr_y + 3)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(*txt)
        self.cell(30, 5, f"FEEDBACK ({score_txt}):", 0, 1)
        
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*COLORS['text_main'])
        self.set_x(15)
        self.multi_cell(180, 5, feed)
        
        self.set_y(self.get_y() + 10)

    def draw_transcript(self, transcript):
        if not transcript: return
        self.add_page()
        self.draw_section_title("SESSION OVERVIEW")
        
        for t in transcript:
            role = t['role'].upper()
            content = sanitize_text(t['content'])
            
            # Role Label
            self.set_font('Arial', 'B', 8)
            if role == 'USER':
                self.set_text_color(*COLORS['accent'])
            else:
                self.set_text_color(*COLORS['primary'])
            
            # Check space for at least header + 1 line
            self.check_space(15)
            self.cell(0, 5, role, 0, 1)
            
            # Content
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            
            # Calculate height needed
            h = self.get_multicell_height(190, content)
            self.check_space(h + 5)
            
            self.multi_cell(190, 5, content)
            self.ln(4)

    def draw_context(self, scenario):
        if not scenario: return
        self.check_space(40)
        self.draw_section_title("SESSION CONTEXT")
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*COLORS['text_main'])
        
        self.set_fill_color(*COLORS['bg_light'])
        h = self.get_multicell_height(190, scenario) + 10
        self.rect(10, self.get_y(), 190, h, 'F')
        
        self.set_xy(15, self.get_y() + 5)
        self.multi_cell(180, 5, sanitize_text(scenario))
        
        self.set_y(self.get_y() + 10)

    def draw_strategic_advice(self, advice):
        if not advice: return
        self.check_space(60)
        self.draw_section_title("STRATEGIC GAMEPLAN")
        
        diag = sanitize_text(advice.get('conflict_diagnosis', ''))
        steps = advice.get('step_by_step', [])
        phrase = sanitize_text(advice.get('power_phrase', ''))
        
        y = self.get_y()
        
        # Diagnosis Box
        self.set_fill_color(240, 249, 255) # Light Blue
        self.rect(10, y, 190, 20, 'F')
        
        self.set_xy(15, y+5)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['primary'])
        self.cell(40, 5, "DIAGNOSIS:", 0, 0)
        
        self.set_font('Arial', '', 9)
        self.set_text_color(*COLORS['text_main'])
        self.multi_cell(140, 5, diag)
        
        y += 25
        self.set_y(y)
        
        # Steps
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(190, 6, "WINNING STRATEGY:", 0, 1)
        self.set_font('Arial', '', 9)
        
        for step in steps:
            clean_step = sanitize_text(step)
            self.set_x(15)
            self.cell(5, 5, "->", 0, 0)
            self.multi_cell(170, 5, clean_step)
            self.ln(2)
            
        self.ln(3)
        
        # Power Phrase
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*COLORS['accent'])
        self.cell(40, 6, "POWER PHRASE:", 0, 0)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*COLORS['text_main'])
        self.multi_cell(140, 6, f'"{phrase}"')
        
        self.ln(10)

def generate_report(session_id, timestamp, name, transcript, role, ai_role, scenario, framework, filename):
    print(f"Generating Report: {filename}")
    data = analyze_full_report_data(transcript, role, ai_role, scenario)
    
    pdf = DashboardPDF()
    pdf.add_page()
    # Note: pdf.header() is called automatically
    pdf.draw_banner(data.get('meta', {}))
    
    # Draw Context after banner
    pdf.draw_context(scenario)
    
    pdf.draw_skill_cards_with_sidebar(
        data.get('functional_cards', []),
        data.get('behavioral_cards', []),
        data.get('sidebar_data', {})
    )
    pdf.draw_chatberry_analysis(data.get('chatberry_analysis', {}))
    pdf.draw_rewrite_card(data.get('coach_rewrite_card', {}))

    pdf.draw_learning_plan(data.get('learning_plan', {}))
    pdf.draw_strategic_advice(data.get('strategic_advice', {}))
    
    qa_list = data.get('qa_analysis', [])
    if qa_list:
        pdf.draw_qa_card(qa_list[0])
        
    pdf.draw_transcript(transcript)
    
    pdf.output(filename)
    print(f"Saved: {filename}")

def check_page_break(self, h):
    if self.get_y() + h > 275: self.add_page()
DashboardPDF.check_page_break = check_page_break
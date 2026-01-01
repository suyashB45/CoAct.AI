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
    'grey_text': (100, 116, 139)     # Slate 500
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

def analyze_full_report_data(transcript, role, ai_role, scenario, framework=None):
    # Prepare conversation for analysis
    conversation_text = "\n".join([f"{t['role'].upper()}: {t['content']}" for t in transcript])
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    user_messages_text = "\n".join([f"USER: {t['content']}" for t in user_msgs])
    
    msg_count = len(transcript)
    user_turn_count = len(user_msgs)
    session_status = "COMPLETE" if msg_count >= 30 else "INCOMPLETE"
    
    if not user_msgs:
        return {
            "meta": {
                "fit_score": 0.0,
                "fit_label": "Starting Out",
                "summary": "Every journey begins with a single step! We're excited to see you start your coaching practice. Your next session will give us wonderful insights to celebrate."
            },
            "sidebar_data": {"top_traits": ["Courage to begin"], "improvements": ["Session engagement"]},
            "functional_cards": [], "behavioral_cards": [], "observed_strengths": ["You took the first step by starting a practice session - that shows initiative!"], "coaching_opportunities": [],
            "practice_prompts": ["Try engaging more in your next session", "Share your thoughts freely - there are no wrong answers", "Take your time and express yourself naturally"]
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
    if framework == "CIRCLE OF INFLUENCE":
        framework_context = (
            "### FOCUS FRAMEWORK: CIRCLE OF INFLUENCE (7 Habits)\n"
            "This framework distinguishes between what we can control (Circle of Influence) and what we cannot (Circle of Concern).\n"
            "- **Coaching Goal**: Help the user move from complaining/worrying about external factors to TAKING ACTION on what they can control.\n"
            "- **Evaluate**: Did they focus on their own behavior/responses, or blame others/circumstances?\n"
            "- **Feedback**: Celebrate proactive language ('I will', 'I can'). Gently reframe reactive language ('They made me', 'I had to').\n"
        )
    elif framework == "SCARF":
        framework_context = (
            "### FOCUS FRAMEWORK: SCARF (Neuroscience of Leadership)\n"
            "Analyze the conversation through 5 social domains that drive behavior:\n"
            "1. **Status**: Did they respect/enhance the other's relative importance?\n"
            "2. **Certainty**: Did they provide clarity and reduce ambiguity?\n"
            "3. **Autonomy**: Did they offer choices or control?\n"
            "4. **Relatedness**: Did they build safety and connection?\n"
            "5. **Fairness**: Did the exchange feel just and unbiased?\n"
            "- **Coaching Goal**: Highlight where they supported these needs (Safety) or threatened them (Threat Response).\n"
        )
    elif framework == "FUEL":
        framework_context = (
            "### FOCUS FRAMEWORK: FUEL (Coaching Conversation)\n"
            "Guide the user through these steps:\n"
            "1. **Frame the Conversation**: Set context and agree on purpose.\n"
            "2. **Understand the State**: Explore the current situation and perspective.\n"
            "3. **Explore the Desired State**: Imagine success and options.\n"
            "4. **Lay Out a Success Plan**: Agree on specific actions and timeline.\n"
            "- **Evaluate**: Did the user follow this structure to guide the conversation effectively?\n"
        )
    
    system_prompt = (
        f"### SYSTEM ROLE\n"
        f"You are CoAct, a WARM, NURTURING coaching mentor. Your purpose is to celebrate growth and gently guide improvement.\n"
        f"Context: {scenario}\n"
        f"User Role: {role} | AI Partner Role: {ai_role}\n"
        f"Session: {user_turn_count} user turns | Status: {session_status}\n"
        f"{framework_context}\n"
        f"### CRITICAL INSTRUCTION - READ CAREFULLY\n"
        "ANALYZE ONLY THE USER'S MESSAGES. DO NOT analyze or evaluate the AI/ASSISTANT's responses.\n"
        "**IMPORTANT**: When filling 'you_said' fields in coaching_opportunities, ONLY quote from USER messages.\n"
        "**NEVER** quote ASSISTANT messages as if the user said them - this is a critical error.\n"
        "The ASSISTANT (AI coach) messages are labeled as 'ASSISTANT:' - these are NOT the user's words.\n\n"
        "Focus on:\n"
        "- What the USER said (messages labeled 'USER:'), how they said it\n"
        "- The USER's tone, word choice, structure\n"
        "- How the USER handled the conversation\n"
        "- The USER's communication skills and strategies\n\n"
        f"### TONE & VOCABULARY GUIDELINES (EXTREMELY IMPORTANT)\n"
        "Your feedback must feel like a SUPPORTIVE MENTOR, not a critic. Use rich, expressive vocabulary:\n\n"
        "**FOR AREAS NEEDING GROWTH (Be Gentle & Encouraging):**\n"
        "- Never say 'failed', 'poor', 'weak', 'bad', 'wrong', 'mistake'\n"
        "- Use: 'emerging opportunity', 'growth edge', 'room to blossom', 'untapped potential'\n"
        "- Use: 'foundation being built', 'skills in development', 'journey beginning'\n"
        "- Use: 'with practice, this will strengthen', 'this is where growth awaits'\n"
        "- Frame challenges as: 'Your next breakthrough area', 'An exciting space for development'\n"
        "- Acknowledge effort: 'You showed courage in trying...', 'It takes bravery to...'n\n"
        "**FOR AREAS OF SUCCESS (Be Celebratory & Expressive):**\n"
        "- Use: 'brilliant', 'remarkable', 'outstanding', 'exceptional', 'masterful'\n"
        "- Use: 'beautifully executed', 'wonderfully crafted', 'elegantly handled'\n"
        "- Use: 'natural gift', 'innate strength', 'impressive instinct', 'powerful presence'\n"
        "- Use: 'truly impressive', 'genuinely admirable', 'exceptionally strong'\n"
        "- Celebrate: 'This moment showcased your natural talent!', 'A shining example of...'\n\n"
        f"### DIRECTIONAL SIGNALS (Encouraging Labels)\n"
        "Use these warmly-framed developmental stages:\n"
        "- **Starting Out**: 'Beginning a promising journey' - Focus on potential, not gaps.\n"
        "- **Developing**: 'Growing beautifully' - Highlight progress and momentum.\n"
        "- **Consistent**: 'Reliably strong' - Celebrate their dependable skills.\n"
        "- **Fluent**: 'Masterful and inspiring' - Express genuine admiration.\n\n"
        f"### EVALUATION DIMENSIONS (4 CORE SKILLS)\n"
        "Analyze the USER across these 4 communication skills with ENCOURAGING language:\n"
        "1. **Communication Clarity**: How clearly did they express themselves? Celebrate clarity, gently note opportunities.\n"
        "2. **Questioning & Listening**: Did they ask thoughtful questions? Honor their curiosity.\n"
        "3. **Empathy**: Did they show understanding? Celebrate connection attempts.\n"
        "4. **Handling Objections**: Did they navigate challenges? Acknowledge their resilience.\n\n"
        f"### COACHING PHILOSOPHY\n"
        "1. **Celebrate First**: Always lead with what they did well. Find genuine positives.\n"
        "2. **Growth Mindset**: Frame feedback as opportunities, but BE CLEAR about gaps/lagging areas.\n"
        "3. **Warm Vocabulary**: Use expressive, rich language that feels supportive.\n"
        "4. **Evidence-Based**: Cite specific quotes, but frame them positively.\n"
        "5. **Balanced Summary**: The user should feel encouraged but aware of what to fix.\n\n"
        "### SPECIAL COACHING SECTIONS\n"
        "1. **Turning Point Analysis (The Coaching Moment)**: If breakthrough occurred, CELEBRATE IT enthusiastically! If not, gently explain what's possible next time with encouragement.\n"
        "2. **Vocabulary Coaching**: 'Lean In' phrases = celebratory language for their good choices. 'Lean Away' = gently suggest alternatives without criticism.\n"
        "3. **Conversation Reframes**: Frame as 'A lovely alternative could be...' not 'You should have said...'\n"
        "4. **Reflection Guide**: Create 2-3 thought-provoking questions that inspire growth.\n\n"
        "### OUTPUT FORMAT (Strict JSON)\n"
        "{\n"
        "  \"meta\": {\n"
        "    \"fit_label\": <string: Starting Out/Developing/Consistent/Fluent>, \"summary\": <string 2-3 sentences. 1. Celebrate main strength. 2. Clearly state the PRIMARY GAP or LAGGING AREA. 3. End with encouragement.>\n"
        "  },\n"
        "  \"skill_snapshot\": [\n"
        "    { \"name\": \"Communication Clarity\", \"signal\": <string>, \"text\": <string: Explain WHY this score was given. Cite specific evidence/quotes.> },\n"
        "    { \"name\": \"Questioning & Listening\", \"signal\": <string>, \"text\": <string: Explain WHY this score was given. Cite specific evidence/quotes.> },\n"
        "    { \"name\": \"Empathy\", \"signal\": <string>, \"text\": <string: Explain WHY this score was given. Cite specific evidence/quotes.> },\n"
        "    { \"name\": \"Handling Objections\", \"signal\": <string>, \"text\": <string: Explain WHY this score was given. Cite specific evidence/quotes.> }\n"
        "  ],\n"
        "  \"observed_strengths\": [<string 2-3 CELEBRATORY strengths with enthusiastic language and specific quotes>],\n"
        "  \"coaching_opportunities\": [{ \"you_said\": <exact quote>, \"try_this\": <warm, gentle reframe>, \"why\": <encouraging explanation of growth potential> }],\n"
        "  \"practice_prompts\": [<string 3 actionable, POSITIVELY-FRAMED micro-tasks>],\n"
        "  \"sidebar_data\": { \"top_traits\": [<string celebratory traits>], \"improvements\": [<string gently-framed growth areas>] },\n"
        "  \"turning_point\": {\n"
        "    \"occurred\": <boolean>,\n"
        "    \"moment\": <string - exact quote or null>,\n"
        "    \"before_state\": <string emotional state before>,\n"
        "    \"after_state\": <string emotional state after>,\n"
        "    \"analysis\": <string - if occurred: CELEBRATE enthusiastically; if not: gently encourage with 'Next time, try...'>\n"
        "  },\n"
        "  \"vocabulary_coaching\": {\n"
        "    \"lean_in_phrases\": [<string CELEBRATE their good language choices>],\n"
        "    \"lean_away_phrases\": [<string gently note alternatives without criticism>],\n"
        "    \"coaching_tip\": <string warm, encouraging advice for vocabulary growth>\n"
        "  },\n"
        "  \"sentiment_arc\": [<list of integers 1-10 representing user sentiment per turn (1=Frustrated, 10=Flow/Joy)>],\n"
        "  \"reflection_guide\": [<string 2-3 inspiring, growth-oriented questions>],\n"
        "  \"behavioral_cards\": [\n"
        "    { \"trait\": \"Empathy\", \"score\": <int 1-10>, \"text\": <string brief encouraging analysis> },\n"
        "    { \"trait\": \"Adaptability\", \"score\": <int 1-10>, \"text\": <string brief encouraging analysis> },\n"
        "    { \"trait\": \"Influence\", \"score\": <int 1-10>, \"text\": <string brief encouraging analysis> }\n"
        "  ]\n"
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

### USER'S MESSAGES ONLY (Analyze ONLY These - Never Quote from ASSISTANT Messages)
{user_only_messages}

### CRITICAL REMINDER
- The 'you_said' field MUST ONLY contain quotes from USER messages above, NEVER from ASSISTANT messages.
- When identifying coaching opportunities, ONLY quote what the USER said.
- The ASSISTANT's messages are for context only - do NOT analyze or quote them as user content.
"""
        
        response = llm_reply([
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": analysis_input}
        ])
        clean_text = response.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Calculate Pace (Word Count per Turn) locally
        user_msgs = [t for t in transcript if t['role'] == 'user']
        pace_data = [len(t.get('content', '').split()) for t in user_msgs]
        data['pace_data'] = pace_data
        
        # Calculate Fit Score locally (based on skills)
        skill_map = {'Starting Out': 1, 'Developing': 2, 'Consistent': 3, 'Fluent': 4}
        total_score = 0
        skill_count = 0
        for s in data.get('skill_snapshot', []):
            sig = s.get('signal', 'Starting Out')
            total_score += skill_map.get(sig, 1)
            skill_count += 1
            
        avg_score = total_score / skill_count if skill_count > 0 else 1
        # Map 1-4 scale to 0-10 scale
        # 1=2.5, 2=5.0, 3=7.5, 4=10.0
        fit_score = (avg_score / 4) * 10
        if 'meta' not in data: data['meta'] = {}
        data['meta']['fit_score'] = round(fit_score, 1)
        
        return data
    except Exception as e:
        print(f"JSON Parse Error: {e}")
        return {
            "meta": {"fit_label": "Developing", "summary": "Your coaching journey is beautifully in progress! We're preparing your personalized insights."},
            "skill_snapshot": [
                {"name": "Communication Clarity", "signal": "Developing", "text": "Your clarity skills are growing - keep practicing!"},
                {"name": "Questioning & Listening", "signal": "Developing", "text": "Your curiosity and listening are developing wonderfully."},
                {"name": "Empathy", "signal": "Developing", "text": "Your ability to connect is blossoming beautifully."},
                {"name": "Handling Objections", "signal": "Developing", "text": "Your resilience in challenging moments is emerging."}
            ],
            "observed_strengths": ["You showed up and practiced - that takes courage!"], 
            "coaching_opportunities": [], 
            "practice_prompts": ["Continue practicing with confidence", "Every session builds your skills", "Trust your natural communication instincts"],
            "sidebar_data": {"top_traits": ["Growth mindset"], "improvements": ["Continued practice"]}
        }

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
            self.cell(0, 5, 'Coaching Practice Reflection', 0, 0, 'L')
            self.ln(30)
        else:
            self.set_fill_color(*COLORS['header_grad_1'])
            self.rect(0, 0, 210, 12, 'F')
            self.set_xy(10, 3)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, 'CoAct.AI Coaching Summary', 0, 0, 'L')
            self.ln(15)

    def draw_banner(self, meta):
        label = meta.get('fit_label', 'Developing')
        summary = meta.get('summary', '')
        fit_score = float(meta.get('fit_score', 0))
        bg, txt_color = get_score_theme(fit_score)
        
        self.set_fill_color(*bg)
        self.rect(10, self.get_y(), 190, 45, 'F')
        self.set_xy(15, self.get_y() + 8)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*txt_color)
        self.cell(40, 5, "COACHING ALIGNMENT", 0, 1, 'C')
        self.set_xy(15, self.get_y() + 2)
        self.set_font('Arial', 'B', 18)
        self.cell(40, 10, label.upper(), 0, 0, 'C')
        
        self.set_draw_color(255, 255, 255)
        self.line(60, self.get_y() - 10, 60, self.get_y() + 25)
        
        self.set_xy(65, self.get_y() - 10)
        self.set_font('Arial', 'B', 10)
        self.cell(100, 5, "PRACTICE REFLECTION", 0, 1)
        self.set_xy(65, self.get_y())
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        self.multi_cell(130, 5, sanitize_text(summary))
        self.set_y(self.get_y() + 20)

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
        self.cell(side_w - 6, 6, "SKILL DYNAMICS", 0, 1)
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
        self.cell(0, 8, "PRACTICE PROMPTS", 0, 1)
        self.ln(2)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(*COLORS['text_main'])
        for i, p in enumerate(prompts[:5]):
            self.set_x(15)
            self.cell(8, 5, f"{i+1}.", 0, 0)
            self.multi_cell(170, 5, sanitize_text(p))
            self.ln(2)

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
        
        self.set_fill_color(6, 182, 212)  # Cyan 500
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
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
        """Draws Linear Progress Bars for skills (matching frontend visuals)."""
        if not skills: return
        self.check_space(80)
        self.ln(5)
        
        # Title
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "SKILL SNAPSHOT", 0, 1)
        self.ln(3)
        
        # Signal Map
        score_map = {'Starting Out': 25, 'Developing': 50, 'Consistent': 75, 'Fluent': 100}
        color_map = {
            'Starting Out': COLORS['danger'],
            'Developing': COLORS['warning'],
            'Consistent': COLORS['success'],
            'Fluent': (59, 130, 246) # Blue for Fluent
        }
        
        # Draw Bars Two-Column if possible, or just list
        # Let's do a clean list with bars like the screenshot
        
        for skill in skills:
            name = sanitize_text(skill.get('name', ''))
            signal = skill.get('signal', 'Starting Out')
            text = sanitize_text(skill.get('text', ''))
            
            percentage = score_map.get(signal, 25)
            bar_color = color_map.get(signal, COLORS['warning'])
            
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
            
            # Score / Signal
            self.set_x(160)
            self.set_text_color(*bar_color)
            self.set_font('Arial', 'B', 9)
            self.cell(30, 5, signal.upper(), 0, 1, 'R')
            
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

    def draw_transcript(self, transcript):
        if not transcript: return
        self.add_page()
        
        self.set_fill_color(*COLORS['primary'])
        self.rect(10, self.get_y(), 3, 8, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLORS['primary'])
        self.cell(0, 8, "CONVERSATION TRANSCRIPT", 0, 1)
        self.ln(5)
        
        for t in transcript:
            role = t.get('role', '').upper()
            content = sanitize_text(t.get('content', ''))
            if len(content) > 300: content = content[:297] + "..."
            
            self.check_space(20)
            
            if role == 'USER':
                self.set_font('Arial', 'B', 9)
                self.set_text_color(*COLORS['accent'])
                self.cell(0, 5, "YOU:", 0, 1)
            else:
                self.set_font('Arial', 'B', 9)
                self.set_text_color(*COLORS['text_light'])
                self.cell(0, 5, "AI COACH:", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.set_x(15)
            self.multi_cell(180, 5, content)
            self.ln(3)

    def check_space(self, h):
        if self.get_y() + h > 275: self.add_page()

def generate_report(session_id, timestamp, name, transcript, role, ai_role, scenario, framework, filename, precomputed_data=None):
    print(f"Generating Report: {filename}")
    
    if precomputed_data:
        print("Using precomputed report data for consistency.")
        data = precomputed_data
    else:
        print("Generating new report data...")
        data = analyze_full_report_data(transcript, role, ai_role, scenario)
    
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
    pdf.draw_banner(data.get('meta', {}))
    pdf.draw_coaching_with_sidebar(
        data.get('observed_strengths', []),
        data.get('coaching_opportunities', []),
        data.get('practice_prompts', []),
        data.get('sidebar_data', {})
    )
    # Replaced Radar Chart with Skill Bars (reference consistency)
    pdf.draw_skill_bars(data.get('skill_snapshot', []))
    
    # Behavioral Analysis (Adding explicitly as requested improvement)
    pdf.draw_behavioral_analysis(data.get('behavioral_cards', []))
    
    # New Data Charts
    if data.get('pace_data'):
        pdf.draw_line_chart("COMMUNICATION VOLUME (Words per Turn)", data.get('pace_data'), COLORS['accent'], "Words")
        
    if data.get('sentiment_arc'):
         pdf.draw_line_chart("SENTIMENT ANALYSIS (Emotional Flow)", data.get('sentiment_arc'), COLORS['success'], "Sentiment")

    pdf.draw_turning_point(data.get('turning_point'))
    pdf.draw_vocabulary_coaching(data.get('vocabulary_coaching'))
    pdf.draw_reflection_guide(data.get('reflection_guide', []))
    pdf.draw_transcript(transcript)
    pdf.output(filename)
    print(f"Saved: {filename}")
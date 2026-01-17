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
    conversation_text = "\\n".join([f"{t['role'].upper()}: {t['content']}" for t in transcript])
    
    # Extract only user messages for focused analysis
    user_msgs = [t for t in transcript if t['role'] == 'user']
    user_messages_text = "\\n".join([f"USER: {t['content']}" for t in user_msgs])
    
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

    # Framework Specific Instructions
    framework_context = ""
    if framework:
         framework_context = f"### FOCUS FRAMEWORK: {framework}\\nEvaluate the user's adherence to the principles of {framework}.\\n"
    
    # Determine Mode-Specific Instructions & Output Format
    if mode == "evaluation":
        mode_instruction = """
### 1️⃣ ASSESSMENT MODE - INSTRUCTIONS
👉 **Purpose**: Evaluate performance, generate scores, insights, and improvement actions.
- **TONE**: Professional, objective, evaluative.
- **SCORING**: You MUST provide scores (0-10) for all dimensions.
- **FOCUS**: Performance gaps, competency levels, and specific actionable fixes.

### OUTPUT JSON STRUCTURE (ASSESSMENT):
{
  "meta": {
    "summary": "Concise overview of performance (e.g., 'The participant demonstrated moderate effectiveness...').",
    "emotional_trajectory": "Skeptical -> Collaborative",
    "session_quality": "High engagement with clear learning moments",
    "key_themes": ["Active listening", "Question framing", "Empathy building"]
  },
  "skill_dimension_scores": [
    { "dimension": "Listening & Empathy", "score": <0-10>, "interpretation": "Demonstrated understanding but...", "evidence": "Quote showing this skill in action", "improvement_tip": "Specific actionable advice" },
    { "dimension": "Questioning Quality", "score": <0-10>, "interpretation": "Relied on leading questions...", "evidence": "Quote showing this skill", "improvement_tip": "Try open-ended questions like 'What if...?'" },
    { "dimension": "Psychological Safety", "score": <0-10>, "interpretation": "Maintained non-threatening tone...", "evidence": "Quote demonstrating safety creation", "improvement_tip": "Continue validating emotions before exploring solutions" },
    { "dimension": "Coaching vs Telling", "score": <0-10>, "interpretation": "Shifted to advice too quickly...", "evidence": "Quote showing coaching approach", "improvement_tip": "Ask 'What options do you see?' before suggesting" },
    { "dimension": "Overall Effectiveness", "score": <0-10>, "interpretation": "Consistent foundation with room for refinement...", "evidence": "Quote showing overall approach", "improvement_tip": "Focus on one skill at a time for deeper impact" }
  ],
  "tactical_observations": {
    "success": { "moment": "Quote...", "analysis": "Why it worked...", "impact": "How it affected the conversation", "replication": "How to do this again" },
    "risk": { "moment": "Quote...", "analysis": "Why it was risky...", "alternative": "What could have been done instead", "prevention": "How to avoid this pattern" }
  },
  "observed_strengths": [
    { "title": "Safety Creator", "observation": "Created a psychologically safe environment...", "frequency": "Consistent throughout", "business_impact": "Builds trust for difficult conversations" }
  ],
  "growth_opportunities": [
    { "title": "Leading Questions", "observation": "Overused leading questions...", "suggestion": "Ask 'What' instead of 'Don't you think'...", "practice_method": "Role-play with open-ended question stems", "timeline": "Practice in next 2-3 conversations" }
  ],
  "effectiveness_insights": [
    { "moment": "You said...", "reframe": "Try saying...", "why": "Explanation...", "skill_area": "Active Listening", "difficulty": "Intermediate" }
  ],
  "manager_recommendations": {
    "immediate_action": "Use more 'What' and 'How' questions.",
    "next_simulation": "Practice 'Active Listening' drills.",
    "development_focus": "Questioning techniques and pause management",
    "timeline": "2-week focused practice period",
    "success_metrics": "Increase open-ended questions by 50%, reduce advice-giving by 30%"
  },
  "readiness_indicator": {
    "label": "Developing",
    "score": <0-10>,
    "next_level_requirements": "Demonstrate consistent questioning skills in 3 consecutive sessions",
    "estimated_timeline": "4-6 weeks with focused practice"
  },
  "conversation_analytics": {
    "total_exchanges": <number>,
    "user_talk_time_percentage": <0-100>,
    "question_to_statement_ratio": <ratio>,
    "emotional_tone_progression": "Started cautious, became more open",
    "framework_adherence": "Strong GROW model application"
  },
  "personalized_learning_path": [
    { "skill": "Open-ended questioning", "priority": "High", "resources": ["Practice guide", "Video examples"], "timeline": "Week 1-2" },
    { "skill": "Pause management", "priority": "Medium", "resources": ["Timing exercises"], "timeline": "Week 3-4" }
  ]
}
"""
    else:
        mode_instruction = """
### 2️⃣ LEARNING MODE - INSTRUCTIONS
👉 **Purpose**: Develop skills without judgment, scores, or evaluation.
- **TONE**: Supportive, reflective, coaching-oriented.
- **STRICTLY FORBIDDEN**: Do NOT use words like "Score", "Grade", "Rating", "Fail", "Poor". NO NUMBERS.
- **FOCUS**: Self-awareness, reflection, practice, and "how to think".

### OUTPUT JSON STRUCTURE (LEARNING):
{
  "meta": {
    "summary": "Neutral reflection of patterns (e.g., 'You focused on explaining solutions quickly...').",
    "emotional_trajectory": "Curious -> Reflective",
    "session_energy": "Engaged and thoughtful throughout",
    "learning_moments": ["Discovered power of silence", "Recognized advice-giving pattern", "Felt impact of open questions"]
  },
  "key_insights": [
    { "pattern": "Pacing", "description": "You tend to respond faster than you probe.", "self_awareness_question": "What drives your urgency to respond quickly?", "exploration_area": "Comfort with silence and pause" },
    { "pattern": "Curiosity", "description": "You prioritize clarity over curiosity.", "self_awareness_question": "What would happen if you stayed curious longer?", "exploration_area": "Question sequencing and depth" }
  ],
  "reflective_questions": [
    { "question": "What was the other person really trying to achieve?", "purpose": "Deepen empathy and understanding", "timing": "Use during conversations" },
    { "question": "How might the conversation change if you paused longer?", "purpose": "Explore pacing and presence", "timing": "Practice in low-stakes situations" }
  ],
  "skill_focus_areas": [
    { "skill": "Active Listening", "description": "Focus on hearing the unsaid.", "why_important": "Creates deeper connection and trust", "practice_opportunities": "Daily conversations, team meetings", "success_indicators": "Others feel truly heard" },
    { "skill": "Open-Ended Questioning", "description": "Using 'What' and 'How' to explore.", "why_important": "Unlocks creative thinking and ownership", "practice_opportunities": "One-on-ones, problem-solving sessions", "success_indicators": "People generate their own solutions" }
  ],
  "suggested_approaches": [
    { "moment": "You explained...", "alternative": "Try exploring...", "benefit": "This allows the user to...", "skill_practiced": "Coaching vs. Telling", "confidence_level": "Start with low-risk situations" }
  ],
  "practice_plan": [
    { "action": "Ask at least 3 open questions before responding.", "frequency": "Every conversation this week", "reflection_prompt": "What did you discover by waiting?", "difficulty": "Beginner" },
    { "action": "Pause 2-3 seconds after each reply.", "frequency": "Daily practice", "reflection_prompt": "How did the silence feel? What emerged?", "difficulty": "Intermediate" }
  ],
  "learning_outcome": "With continued focus on curiosity, your interactions will feel more collaborative...",
  "mindset_shifts": [
    { "from": "I need to have the answer", "to": "I can help them find their answer", "practice_area": "Coaching conversations" },
    { "from": "Silence means I'm not helping", "to": "Silence creates space for thinking", "practice_area": "Pause management" }
  ],
  "strengths_to_leverage": [
    { "strength": "Natural empathy", "how_to_use": "Trust your instincts about emotional undertones", "amplification": "Verbalize what you're sensing to check understanding" }
  ],
  "curiosity_builders": [
    { "technique": "The 5 Whys", "description": "Keep asking 'why' to go deeper", "when_to_use": "When someone states a conclusion" },
    { "technique": "Assumption checking", "description": "Notice and question your assumptions", "when_to_use": "When you think you know the answer" }
  ],
  "reflection_journal_prompts": [
    "What surprised me most about this conversation?",
    "When did I feel most connected to the other person?",
    "What would I do differently if I could replay one moment?"
  ]
}
"""

    # Unified System Prompt
    system_prompt = (
        f"### SYSTEM ROLE\\n"
        f"You are an expert Soft Skills Development Coach acting as the logic engine for 'COACT.AI Reports'.\\n"
        f"Context: {scenario}\\n"
        f"User Role: {role} | AI Role: {ai_role}\\n"
        f"{framework_context}\\n"
        f"{mode_instruction}\\n"
        f"### GENERAL RULES\\n"
        "1. Be specific and citation-based (quote the user).\\n"
        "2. Be constructive.\\n"
        "3. OUTPUT MUST BE VALID JSON ONLY.\\n"
    )

    try:
        # Create clearly separated sections for the LLM
        full_conversation = "\\n".join([f"{'USER' if t['role'] == 'user' else 'ASSISTANT'}: {t['content']}" for t in transcript])
        user_only_messages = "\\n".join([f"USER: {t['content']}" for t in transcript if t['role'] == 'user'])
        
        analysis_input = f"""### FULL CONVERSATION
{full_conversation}
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
        
        # Normalize data for frontend compatibility if needed
        if mode == 'evaluation':
            data['meta']['fit_score'] = data.get('readiness_indicator', {}).get('score', 0) / 10
        else:
            data['meta']['fit_score'] = 0
            
        return data
    except Exception as e:
        print(f"JSON Parse Error: {e}")
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
            self.cell(0, 5, 'Performance & Skill Development Report', 0, 0, 'L')
            self.ln(30)
        else:
            self.set_fill_color(*COLORS['header_grad_1'])
            self.rect(0, 0, 210, 12, 'F')
            self.set_xy(10, 3)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(255, 255, 255)
            self.cell(0, 6, 'CoAct.AI Report', 0, 0, 'L')
            self.ln(15)

    def check_space(self, h):
        if self.get_y() + h > 270:
            self.add_page()

    def draw_section_header(self, title, color):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 10, title, 0, 1)
        self.ln(2)

    def draw_banner(self, meta, mode="coaching"):
        summary = meta.get('summary', '')
        emotional_trajectory = meta.get('emotional_trajectory', '')
        session_quality = meta.get('session_quality', '')
        key_themes = meta.get('key_themes', [])
        learning_moments = meta.get('learning_moments', [])
        
        self.set_y(self.get_y() + 5)
        start_y = self.get_y()
        
        # Calculate banner height based on content
        banner_height = 55 if (emotional_trajectory or session_quality or key_themes or learning_moments) else 40
        
        # 1. Main Card Background
        self.set_fill_color(252, 253, 255) # Almost white
        self.set_draw_color(241, 245, 249) # Slate 100
        self.rect(10, start_y, 190, banner_height, 'DF')
        
        # 2. Mode-specific title
        self.set_xy(15, start_y + 8)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(148, 163, 184) # Slate 400
        title = "PERFORMANCE ASSESSMENT SUMMARY" if mode == "evaluation" else "LEARNING REFLECTION SUMMARY"
        self.cell(100, 5, title, 0, 1)
        
        # 3. Executive Summary
        self.set_xy(15, self.get_y() + 2)
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 65, 85) # Slate 700
        self.multi_cell(180, 5, sanitize_text(summary))
        
        # 4. Additional context for enhanced reports
        current_y = self.get_y() + 3
        
        if emotional_trajectory:
            self.set_xy(15, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(100, 116, 139) # Slate 500
            self.cell(40, 4, "EMOTIONAL JOURNEY:", 0, 0)
            self.set_font('Arial', '', 8)
            self.set_text_color(51, 65, 85)
            self.cell(0, 4, sanitize_text(emotional_trajectory), 0, 1)
            current_y += 5
        
        if session_quality:
            self.set_xy(15, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(100, 116, 139)
            self.cell(40, 4, "SESSION QUALITY:", 0, 0)
            self.set_font('Arial', '', 8)
            self.set_text_color(51, 65, 85)
            self.cell(0, 4, sanitize_text(session_quality), 0, 1)
            current_y += 5
        
        # Key themes or learning moments
        themes_to_show = key_themes if mode == "evaluation" else learning_moments
        if themes_to_show:
            self.set_xy(15, current_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(100, 116, 139)
            label = "KEY THEMES:" if mode == "evaluation" else "LEARNING MOMENTS:"
            self.cell(40, 4, label, 0, 0)
            self.set_font('Arial', '', 8)
            self.set_text_color(51, 65, 85)
            themes_text = ", ".join([sanitize_text(str(theme)) for theme in themes_to_show[:3]])
            self.cell(0, 4, themes_text, 0, 1)
        
        self.set_y(start_y + banner_height + 5)

    # --- ASSESSMENT MODE DRAWING METHODS ---

    def draw_assessment_table(self, scores):
        if not scores: return
        self.check_space(80)
        self.ln(5)
        
        self.draw_section_header("SKILL DIMENSION ANALYSIS", COLORS['primary'])

        # Header
        self.set_fill_color(241, 245, 249)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*COLORS['text_main'])
        self.cell(45, 8, "DIMENSION", 1, 0, 'L', True)
        self.cell(15, 8, "SCORE", 1, 0, 'C', True)
        self.cell(65, 8, "INTERPRETATION", 1, 0, 'L', True)
        self.cell(65, 8, "IMPROVEMENT TIP", 1, 1, 'L', True)

        for item in scores:
            dim = sanitize_text(item.get('dimension', ''))
            score = item.get('score', 0)
            interp = sanitize_text(item.get('interpretation', ''))
            tip = sanitize_text(item.get('improvement_tip', ''))

            # Calculate row height based on content
            row_height = max(15, len(interp) // 40 * 5 + 10, len(tip) // 40 * 5 + 10)

            self.set_font('Arial', 'B', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(45, row_height, dim, 1, 0, 'L')
            
            # Score Color
            if score >= 8: self.set_text_color(*COLORS['success'])
            elif score >= 6: self.set_text_color(*COLORS['warning'])
            else: self.set_text_color(*COLORS['danger'])
            
            self.cell(15, row_height, f"{score}/10", 1, 0, 'C')
            
            # Interpretation
            self.set_text_color(*COLORS['text_main'])
            self.set_font('Arial', '', 8)
            current_x = self.get_x()
            current_y = self.get_y()
            self.multi_cell(65, 7.5, interp, border=1, align='L')
            
            # Improvement tip
            self.set_xy(current_x + 65, current_y)
            self.set_text_color(*COLORS['accent'])
            self.multi_cell(65, 7.5, tip, border=1, align='L')
            
            # Move to next row
            self.set_xy(10, current_y + row_height)

        self.ln(5)

    def draw_conversation_analytics(self, analytics):
        if not analytics: return
        self.check_space(40)
        
        self.draw_section_header("CONVERSATION ANALYTICS", COLORS['secondary'])
        
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
            
            # Bar Foreground
            bar_len = ((chart_w - 41) * score) / max_score
            if score >= 8: self.set_fill_color(*COLORS['success'])
            elif score >= 5: self.set_fill_color(*COLORS['warning'])
            else: self.set_fill_color(*COLORS['danger'])
            
            self.rect(chart_x + 41, y_pos, bar_len, bar_h, 'F')
            
            # Score Label
            self.set_xy(chart_x + 41 + bar_len + 2, y_pos + 1)
            self.set_text_color(100, 100, 100)
            self.cell(10, 6, f"{score}", 0, 0)

        self.set_y(chart_y + (len(scores) * (bar_h + gap)) + 5)


    # --- LEARNING MODE DRAWING METHODS ---

    def draw_behavioral_sidebar(self, insights):
        if not insights: return
        self.check_space(80)
        self.ln(5)
        
        self.draw_section_header("KEY INSIGHTS & SELF-AWARENESS", COLORS['primary'])
        
        for p in insights:
            pattern = sanitize_text(p.get('pattern', ''))
            description = sanitize_text(p.get('description', ''))
            question = sanitize_text(p.get('self_awareness_question', ''))
            
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['accent'])
            self.cell(0, 6, f"• {pattern}", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(0, 5, description)
            
            if question:
                self.set_font('Arial', 'I', 9)
                self.set_text_color(*COLORS['text_light'])
                self.multi_cell(0, 5, f"Reflect: {question}")
            
            self.ln(3)

    def draw_mindset_shifts(self, shifts):
        if not shifts: return
        self.check_space(60)
        
        self.draw_section_header("MINDSET TRANSFORMATIONS", COLORS['section_coach'])
        
        for shift in shifts:
            from_mindset = sanitize_text(shift.get('from', ''))
            to_mindset = sanitize_text(shift.get('to', ''))
            practice_area = sanitize_text(shift.get('practice_area', ''))
            
            # From mindset (old)
            self.set_fill_color(254, 226, 226) # Red 100
            self.rect(10, self.get_y(), 90, 20, 'F')
            self.set_xy(15, self.get_y() + 3)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['danger'])
            self.cell(80, 4, "FROM:", 0, 1)
            self.set_x(15)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(80, 4, from_mindset)
            
            # Arrow
            arrow_y = self.get_y() - 10
            self.set_xy(100, arrow_y)
            self.set_font('Arial', 'B', 12)
            self.set_text_color(*COLORS['text_light'])
            self.cell(10, 10, "→", 0, 0, 'C')
            
            # To mindset (new)
            self.set_fill_color(240, 253, 244) # Green 50
            self.rect(110, arrow_y - 10, 90, 20, 'F')
            self.set_xy(115, arrow_y - 7)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(*COLORS['success'])
            self.cell(80, 4, "TO:", 0, 1)
            self.set_x(115)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(80, 4, to_mindset)
            
            # Practice area
            if practice_area:
                self.set_font('Arial', 'I', 8)
                self.set_text_color(*COLORS['text_light'])
                self.cell(0, 5, f"Practice in: {practice_area}", 0, 1)
            
            self.ln(5)

    def draw_curiosity_builders(self, builders):
        if not builders: return
        self.check_space(50)
        
        self.draw_section_header("CURIOSITY BUILDING TECHNIQUES", COLORS['section_comm'])
        
        for builder in builders:
            technique = sanitize_text(builder.get('technique', ''))
            description = sanitize_text(builder.get('description', ''))
            when_to_use = sanitize_text(builder.get('when_to_use', ''))
            
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['section_comm'])
            self.cell(0, 6, f"🔍 {technique}", 0, 1)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(0, 5, description)
            
            if when_to_use:
                self.set_font('Arial', 'I', 8)
                self.set_text_color(*COLORS['text_light'])
                self.multi_cell(0, 4, f"Use when: {when_to_use}")
            
            self.ln(3)

    def draw_reflection_prompts(self, prompts):
        if not prompts: return
        self.check_space(40)
        
        self.draw_section_header("REFLECTION JOURNAL PROMPTS", COLORS['section_eq'])
        
        self.set_fill_color(248, 250, 252)
        self.rect(10, self.get_y(), 190, len(prompts) * 8 + 10, 'F')
        
        start_y = self.get_y()
        for i, prompt in enumerate(prompts):
            self.set_xy(15, start_y + 5 + i * 8)
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_main'])
            self.cell(0, 6, f"• {sanitize_text(prompt)}", 0, 1)
        
        self.set_y(start_y + len(prompts) * 8 + 15)
            self.multi_cell(0, 6, sanitize_text(p.get('description')))
            self.ln(2)
        self.ln(5)

    def draw_reflection_guide(self, questions):
        if not questions: return
        self.check_space(50)
        self.draw_section_header("REFLECTIVE COACHING QUESTIONS", COLORS['section_comm'])
        
        self.set_fill_color(248, 250, 252)
        self.rect(10, self.get_y(), 190, len(questions)*15 + 10, 'F')
        self.set_y(self.get_y() + 5)
        
        for q in questions:
            self.set_x(15)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['accent'])
            self.cell(10, 6, "?", 0, 0)
            self.set_font('Arial', 'I', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(170, 6, sanitize_text(q))
            self.ln(4)
        self.ln(5)

    def draw_skill_focus(self, skills):
        if not skills: return
        self.check_space(50)
        self.draw_section_header("SKILL FOCUS AREAS", COLORS['section_skills'])
        
        for skill in skills:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['primary'])
            self.cell(50, 6, sanitize_text(skill.get('skill')), 0, 0)
            
            self.set_font('Arial', '', 9)
            self.set_text_color(*COLORS['text_light'])
            self.multi_cell(0, 6, sanitize_text(skill.get('description')))
            self.ln(2)
        self.ln(5)

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

    def draw_practice_prompts(self, prompts):
        if not prompts: return
        self.check_space(40)
        self.draw_section_header("PRACTICE PLAN", COLORS['section_coach'])
        
        for p in prompts[:5]:
            self.set_x(15)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*COLORS['text_main'])
            self.cell(5, 5, "-", 0, 0)
            
            self.set_font('Arial', '', 10)
            self.set_text_color(*COLORS['text_main'])
            self.multi_cell(170, 5, sanitize_text(p))
            self.ln(2)

    # --- SHARED DRAWING METHODS ---
    def draw_observed_strengths(self, strengths):
        if not strengths: return
        self.check_space(60)
        self.draw_section_header("STRENGTHS IDENTIFIED", COLORS['success'])
        
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
        self.draw_section_header("IMPROVEMENT AREAS", COLORS['warning'])
        
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

def generate_report(transcript, role, ai_role, scenario, framework=None, filename="coaching_report.pdf", mode="coaching", precomputed_data=None):
    print(f"Generating Enhanced PDF Report ({mode})...")
    
    # Analyze data or use precomputed
    if precomputed_data:
        data = precomputed_data
        if 'mode' not in data: data['mode'] = mode
    else:
        print("Generating new report data...")
        data = analyze_full_report_data(transcript, role, ai_role, scenario, framework, mode)
    
    # Sanitize data
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
    
    # Enhanced banner with more context
    meta = data.get('meta', {})
    pdf.draw_banner(meta, mode=mode)
    
    if mode == "evaluation":
        # 1️⃣ ASSESSMENT MODE - Enhanced Content
        
        # Conversation Analytics (NEW)
        analytics = data.get('conversation_analytics', {})
        if analytics:
            pdf.draw_conversation_analytics(analytics)
        
        # Enhanced skill assessment
        scores = data.get('skill_dimension_scores', [])
        if scores:
            pdf.draw_assessment_table(scores)
            pdf.draw_score_chart(scores)
        
        # Enhanced tactical observations
        tactical = data.get('tactical_observations', {})
        if tactical:
            pdf.draw_tactical_observations(tactical)
        
        # Strengths and opportunities
        strengths = data.get('observed_strengths', [])
        if strengths:
            pdf.draw_observed_strengths(strengths)
        
        opportunities = data.get('growth_opportunities', [])
        if opportunities:
            pdf.draw_coaching_opportunities(opportunities)
        
        # Personalized Learning Path (NEW)
        learning_path = data.get('personalized_learning_path', [])
        if learning_path:
            pdf.draw_learning_path(learning_path)
        
        # Enhanced manager recommendations
        recs = data.get('manager_recommendations', {})
        if recs:
            pdf.draw_manager_recommendations(recs)
        
        # Enhanced readiness indicator
        readiness = data.get('readiness_indicator', {})
        if readiness:
            pdf.draw_readiness_indicator(readiness)
        
    else:
        # 2️⃣ LEARNING MODE - Enhanced Content
        
        # Enhanced key insights with self-awareness
        insights = data.get('key_insights', [])
        if insights:
            pdf.draw_behavioral_sidebar(insights)
        
        # Mindset Shifts (NEW)
        shifts = data.get('mindset_shifts', [])
        if shifts:
            pdf.draw_mindset_shifts(shifts)
        
        # Enhanced reflective questions
        questions = data.get('reflective_questions', [])
        if questions:
            pdf.draw_reflection_guide(questions)
        
        # Enhanced skill focus areas
        skills = data.get('skill_focus_areas', [])
        if skills:
            pdf.draw_skill_focus(skills)
        
        # Curiosity Builders (NEW)
        builders = data.get('curiosity_builders', [])
        if builders:
            pdf.draw_curiosity_builders(builders)
        
        # Enhanced practice plan
        practice = data.get('practice_plan', [])
        if practice:
            pdf.draw_practice_prompts(practice)
        
        # Reflection Journal Prompts (NEW)
        prompts = data.get('reflection_journal_prompts', [])
        if prompts:
            pdf.draw_reflection_prompts(prompts)
        
        # Learning outcome
        outcome = data.get('learning_outcome', '')
        if outcome:
            pdf.draw_learning_outcome(outcome)

    pdf.output(filename)
    print(f"✅ Enhanced {mode} report saved: {filename}")
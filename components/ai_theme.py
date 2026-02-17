import os

def generate_ai_theme(api_key: str, context: dict) -> dict:
    """
    توليد ثيم CSS مخصص باستخدام Gemini بناءً على سياق المستخدم
    """
    try:
        try:
            import google.generativeai as genai
        except ImportError:
            return {"status": "error", "message": "يرجى تثبيت المكتبة أولاً: pip install google-generativeai"}
        
        genai.configure(api_key=api_key)
        
        # اختيار النموذج (يفضل Flash للسرعة)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # صياغة الطلب بناءً على السياق
        score = context.get('score', 0)
        time_of_day = context.get('time_of_day', 'day')
        mood = "productive" if score >= 3 else "relaxed" if score > 0 else "neutral"
        
        prompt = f"""
        You are a CSS expert. Generate a modern, sophisticated CSS `background` property value for a productivity app in dark mode.
        
        Context:
        - User Mood: {mood} (Score: {score}/4)
        - Time: {time_of_day}
        - Style: Glassmorphism, Deep, Subtle, Abstract
        
        Requirements:
        - Return ONLY the raw CSS value for the background. No markdown, no selectors, no explanations.
        - Example output: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)
        - Use modern color palettes (deep blues, purples for night; energetic greens/oranges for high productivity).
        - Can use radial-gradient or complex multiple backgrounds.
        """
        
        response = model.generate_content(prompt)
        css_background = response.text.strip().replace("`", "").replace("background:", "").replace(";", "").strip()
        
        return {
            "status": "success",
            "background": css_background,
            "theme_name": f"AI {mood.capitalize()} Theme"
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

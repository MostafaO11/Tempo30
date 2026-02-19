"""
متتبع الإنتاجية - التطبيق الرئيسي
Productivity Tracker - Main Application
"""

import streamlit as st
import os
# Set the HOME environment variable to a writable directory
os.environ['HOME'] = '/tmp'
# إعداد الصفحة (يجب أن يكون في البداية)
st.set_page_config(
    page_title="Tempo 30",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database import get_user_theme
from auth import get_current_user

def setup_pwa():
    """إعداد تطبيق الويب التقدمي (PWA)"""
    
    # قراءة ملف Manifest
    manifest_path = os.path.join(os.path.dirname(__file__), "static", "manifest.json")
    if os.path.exists(manifest_path):
        import json
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_content = json.load(f)
            # تحديث المسارات لتكون مطلقة أو نسبية صحيحة
            # هنا نستخدم data URI لتجنب مشاكل المسارات في Streamlit
            import base64
            manifest_json = json.dumps(manifest_content)
            b64_manifest = base64.b64encode(manifest_json.encode()).decode()
            
            st.markdown(f"""
            <link rel="manifest" href="data:application/manifest+json;base64,{b64_manifest}">
            <meta name="theme-color" content="#28a745">
            <meta name="apple-mobile-web-app-capable" content="yes">
            <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
            <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
            """, unsafe_allow_html=True)

# تفعيل PWA
setup_pwa()

# تحميل التنسيقات المخصصة
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # تنسيقات إضافية
    # تنسيقات إضافية (تم نقلها إلى custom.css)
    pass

# تحميل التنسيقات
load_css()

# استيراد الوحدات
from auth import init_auth_state, is_authenticated, render_auth_page
from components.sidebar import render_sidebar, get_current_page
from components.dashboard import render_dashboard
from components.log_activity import render_log_activity
from components.analytics_page import render_analytics
from components.settings import render_settings
from components.tasks import render_tasks

def main():
    """الدالة الرئيسية"""
    
    # تهيئة حالة المصادقة
    init_auth_state()
    
    # تهيئة حالة الاحتفال
    if "show_celebration" not in st.session_state:
        st.session_state.show_celebration = None
    if "selected_slot" not in st.session_state:
        st.session_state.selected_slot = None
    
    # التحقق من المصادقة
    if not is_authenticated():
        render_auth_page()
        render_footer()
        return
    
    # عرض الشريط الجانبي
    render_sidebar()
    
    # الحصول على الصفحة الحالية
    current_page = get_current_page()
    
    # عرض الصفحة المناسبة
    if current_page == "dashboard":
        render_dashboard()
    elif current_page == "log_activity":
        render_log_activity()
    elif current_page == "tasks":
        render_tasks()
    elif current_page == "analytics":
        render_analytics()
    elif current_page == "leaderboard":
        from components.leaderboard_page import render_leaderboard
        render_leaderboard()
    elif current_page == "settings":
        render_settings()
    else:
        render_dashboard()
        
    # حقن المؤقت العالمي للإشعارات (يعمل في الخلفية)
    from components.global_timer import render_global_timer
    render_global_timer()
    
    # عرض الفوتر
    render_footer()

def render_footer():
    """عرض الفوتر في أسفل الصفحة"""
    import base64
    
    # تحميل الشعار
    logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
    mime_type = "image/png"
    
    if not os.path.exists(logo_path):
        logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.jpg")
        mime_type = "image/jpeg"
    
    img_tag = ""
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            # تعديل الحجم والمحاذاة ليكون بجوار الاسم
            img_tag = f'<img src="data:{mime_type};base64,{encoded}" style="height: 35px; vertical-align: middle; margin-left: 10px; border-radius: 5px;">'
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid #333;
        color: #888;
    ">
        <p style="margin: 0; font-size: 1rem; display: flex; align-items: center; justify-content: center;">
            Made by <span style="color: #4CAF50; font-weight: bold; font-size: 1.2rem; margin: 0 5px;">MOOSTAFA</span>
            {img_tag}
        </p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.8rem; color: #666;">
            Tempo 30 v1.0 | 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()


"""
الشريط الجانبي
Sidebar Component
"""

import streamlit as st
from auth import sign_out, get_user_display_name, get_current_user
from database import get_user_profile, get_logs_by_range
from analytics import calculate_streak, get_logs_summary_by_date
from datetime import date, timedelta

def render_sidebar():
    """عرض الشريط الجانبي"""
    
    with st.sidebar:
        # معلومات المستخدم
        user = get_current_user()
        display_name = get_user_display_name()
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="margin: 0; color: #4CAF50;">مرحباً 👋</h2>
            <p style="margin: 0.5rem 0 0 0; color: #fafafa; font-size: 1.2rem;">{display_name}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # سلسلة الإنتاجية
        if user:
            try:
                profile = get_user_profile(user.id)
                daily_goal = profile.get("daily_goal", 100) if profile else 100
                
                # جلب سجلات آخر 30 يوم لحساب السلسلة
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                logs = get_logs_by_range(user.id, start_date, end_date)
                
                logs_by_date = get_logs_summary_by_date(logs)
                streak = calculate_streak(logs_by_date, daily_goal)
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); border-radius: 10px; margin-bottom: 1rem;">
                    <p style="margin: 0; color: #aaa; font-size: 0.9rem;">🔥 سلسلة الإنتاجية</p>
                    <h1 style="margin: 0.5rem 0 0 0; color: #ff9800; font-size: 2.5rem;">{streak}</h1>
                    <p style="margin: 0; color: #888;">يوم متتالي</p>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass
        
        st.markdown("---")
        
        # قائمة التنقل
        st.markdown("### 📋 القائمة")
        
        # استخدام radio buttons للتنقل
        pages = {
            "لوحة التحكم": "dashboard",
            "تسجيل النشاط": "log_activity",
            "المهام": "tasks",
            "التحليلات": "analytics",
            "المتصدرين": "leaderboard",
            "الإعدادات": "settings"
        }
        
        icons = {
            "لوحة التحكم": "🏠",
            "تسجيل النشاط": "✏️",
            "المهام": "✅",
            "التحليلات": "📊",
            "المتصدرين": "🏆",
            "الإعدادات": "⚙️"
        }
        
        # تهيئة الصفحة الحالية
        if "current_page" not in st.session_state:
            st.session_state.current_page = "dashboard"
        
        for page_name, page_key in pages.items():
            is_active = st.session_state.current_page == page_key
            btn_style = "primary" if is_active else "secondary"
            
            if st.button(
                f"{icons[page_name]} {page_name}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type=btn_style
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # زر تسجيل الخروج
        if st.button("🚪 تسجيل الخروج", use_container_width=True, type="secondary"):
            sign_out()
            st.rerun()
        
        # معلومات التطبيق
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #666; font-size: 0.8rem;">
            <p>Tempo 30 v1.0</p>
        </div>
        """, unsafe_allow_html=True)

def get_current_page() -> str:
    """الحصول على الصفحة الحالية"""
    return st.session_state.get("current_page", "dashboard")

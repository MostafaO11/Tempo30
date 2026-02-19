"""
صفحة الإعدادات والملف الشخصي
Settings Component
"""

import streamlit as st
from auth import get_current_user, get_user_display_name
from database import (
    get_user_profile, 
    update_user_profile,
    update_user_goals,
    get_categories,
    add_category,
    add_category,
    delete_category,
    _get_categories_file,
    _save_json,
    _load_json
)
import os

def render_settings():
    """عرض صفحة الإعدادات"""
    
    user = get_current_user()
    if not user:
        st.error("يرجى تسجيل الدخول أولاً")
        return
    
    st.markdown("""
    <h1 style="text-align: center; color: #FF9800;">
        ⚙️ الإعدادات
    </h1>
    """, unsafe_allow_html=True)
    
    # تبويبات (تم حذف المظهر الذكي)
    tab1, tab2, tab3 = st.tabs(["👤 الملف الشخصي", "🎯 الأهداف", "📁 الفئات"])
    
    with tab1:
        render_profile_settings(user)
    
    with tab2:
        render_goals_settings(user)
    
    with tab3:
        render_categories_settings(user)

def render_profile_settings(user):
    """إعدادات الملف الشخصي"""
    
    st.markdown("### 👤 الملف الشخصي")
    
    profile = get_user_profile(user.id)
    current_name = profile.get("display_name", "") if profile else ""
    
    # معلومات الحساب
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
        <p style="color: #888; margin: 0;">📧 البريد الإلكتروني</p>
        <p style="color: #fafafa; margin: 0.5rem 0 0 0; font-size: 1.2rem;">{user.email}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # تعديل الاسم
    with st.form("profile_form"):
        new_name = st.text_input(
            "👤 الاسم المعروض",
            value=current_name,
            key="profile_name"
        )
        
        submit = st.form_submit_button("💾 حفظ التغييرات", use_container_width=True)
        
        if submit:
            if new_name != current_name:
                result = update_user_profile(user.id, {"display_name": new_name})
                if result["status"] == "success":
                    st.success("✅ تم تحديث الملف الشخصي بنجاح!")
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.info("لم يتم إجراء أي تغييرات")

def render_goals_settings(user):
    """إعدادات الأهداف"""
    
    st.markdown("### 🎯 أهداف الإنتاجية")
    st.markdown("*حدد أهدافك لتتبع تقدمك نحوها*")
    
    profile = get_user_profile(user.id)
    
    current_daily = profile.get("daily_goal", 100) if profile else 100
    current_weekly = profile.get("weekly_goal", 500) if profile else 500
    current_monthly = profile.get("monthly_goal", 2000) if profile else 2000
    
    with st.form("goals_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">📅</span>
                <p style="color: #888; margin: 0;">الهدف اليومي</p>
            </div>
            """, unsafe_allow_html=True)
            
            daily_goal = st.number_input(
                "نقاط/يوم",
                min_value=10,
                max_value=192,  # 48 فترة × 4 نقاط
                value=current_daily,
                step=10,
                key="daily_goal"
            )
            
            # شرح
            st.caption(f"الحد الأقصى: 192 نقطة (48 فترة × 4)")
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">📆</span>
                <p style="color: #888; margin: 0;">الهدف الأسبوعي</p>
            </div>
            """, unsafe_allow_html=True)
            
            weekly_goal = st.number_input(
                "نقاط/أسبوع",
                min_value=50,
                max_value=1344,  # 192 × 7
                value=current_weekly,
                step=50,
                key="weekly_goal"
            )
        
        with col3:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <span style="font-size: 2rem;">🗓️</span>
                <p style="color: #888; margin: 0;">الهدف الشهري</p>
            </div>
            """, unsafe_allow_html=True)
            
            monthly_goal = st.number_input(
                "نقاط/شهر",
                min_value=200,
                max_value=5760,  # 192 × 30
                value=current_monthly,
                step=100,
                key="monthly_goal"
            )
        
        submit = st.form_submit_button("💾 حفظ الأهداف", use_container_width=True)
        
        if submit:
            result = update_user_goals(user.id, daily_goal, weekly_goal, monthly_goal)
            if result["status"] == "success":
                st.success("✅ تم تحديث الأهداف بنجاح!")
                st.rerun()
            else:
                st.error(result["message"])
    
    st.markdown("""
    - **ابدأ بهدف واقعي**: إذا كنت مبتدئاً، ابدأ بهدف يومي منخفض (50-80 نقطة)
    - **تدرج في الزيادة**: زد هدفك تدريجياً مع تحسن عاداتك
    - **كن مرناً**: لا تحبط إذا لم تحقق الهدف في بعض الأيام
    - **راقب اتجاهاتك**: استخدم صفحة التحليلات لفهم أنماط إنتاجيتك
    """)

def render_categories_settings(user):
    """إعدادات الفئات"""
    
    st.markdown("### 📁 إدارة الفئات")
    
    # الفئات الحالية
    categories = get_categories(user.id)
    
    # الفئات الافتراضية
    default_cats = [c for c in categories if c.get("is_default", False)]
    custom_cats = [c for c in categories if not c.get("is_default", False)]
    
    # عرض الفئات الافتراضية
    st.markdown("#### 📌 الفئات الافتراضية")
    
    cols = st.columns(4)
    for i, cat in enumerate(default_cats):
        with cols[i % 4]:
            col_card, col_del = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                <div style="background: {cat.get('color', '#4CAF50')}22; border: 2px solid {cat.get('color', '#4CAF50')}; border-radius: 10px; padding: 1rem; text-align: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.5rem;">{cat.get('icon', '📌')}</span>
                    <p style="color: #fafafa; margin: 0.5rem 0 0 0;">{cat.get('name_ar', cat.get('name', ''))}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("❌", key=f"hide_default_{cat.get('name', '')}_{i}"):
                    from database import hide_default_category
                    result = hide_default_category(user.id, cat.get("name", ""))
                    if result["status"] == "success":
                        st.success("تم الحذف")
                        st.rerun()
                    else:
                        st.error(result["message"])
    
    st.markdown("---")
    
    # الفئات المخصصة
    st.markdown("#### ✨ الفئات المخصصة")
    
    if custom_cats:
        for idx, cat in enumerate(custom_cats):
            with st.container():
                c1, c2, c3, c4 = st.columns([0.5, 3, 1, 0.5])
                
                cat_id = cat.get('id') or f"custom_{idx}"
                current_color = cat.get('color', '#4CAF50')
                current_icon = cat.get('icon', '📌')
                current_name = cat.get('name_ar', cat.get('name', ''))
                
                with c1:
                    st.markdown(f"<div style='font-size: 1.5rem; text-align: center; padding-top: 5px;'>{current_icon}</div>", unsafe_allow_html=True)
                
                with c2:
                    st.markdown(f"<div style='font-size: 1.1rem; padding-top: 10px; color: {current_color}; font-weight: bold;'>{current_name}</div>", unsafe_allow_html=True)
                
                with c3:
                    # تحرير اللون
                    new_color = st.color_picker(
                        "تعديل اللون",
                        value=current_color,
                        key=f"edit_color_{cat_id}",
                        label_visibility="collapsed"
                    )
                    
                    if new_color != current_color:
                        from database import update_category
                        result = update_category(user.id, cat_id, {"color": new_color})
                        if result["status"] == "success":
                            st.toast(f"تم تحديث لون {current_name}")
                            st.rerun()
                
                with c4:
                    if st.button("🗑️", key=f"del_cat_{cat_id}_{idx}"):
                        from database import delete_category
                        result = delete_category(cat_id, user_id=user.id)
                        if result["status"] == "success":
                            st.success("تم الحذف")
                            st.rerun()
                        else:
                            st.error(result["message"])
                
                st.markdown("<hr style='margin: 0.5rem 0; opacity: 0.1;'>", unsafe_allow_html=True)

    else:
        st.info("لا توجد فئات مخصصة حتى الآن")
    
    # إضافة فئة جديدة
    st.markdown("---")
    st.markdown("#### ➕ إضافة فئة جديدة")
    
    with st.form("new_category_form"):
        cat_name_ar = st.text_input("اسم الفئة *", key="new_cat_name_ar", placeholder="مثال: قراءة، رياضة، تأمل...")
        
        col1, col2 = st.columns(2)
        with col1:
            cat_icon = st.text_input("الأيقونة (اختياري)", value="📌", key="new_cat_icon")
        with col2:
            cat_color = st.color_picker("اللون (اختياري)", value="#4CAF50", key="new_cat_color")
        
        submit = st.form_submit_button("➕ إضافة الفئة", use_container_width=True)
        
        if submit:
            if cat_name_ar:
                cat_icon = cat_icon if cat_icon else "📌"
                result = add_category(user.id, cat_name_ar, cat_name_ar, cat_color, cat_icon)
                if result["status"] == "success":
                    st.success("✅ تم إضافة الفئة بنجاح!")
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.warning("يرجى كتابة اسم الفئة")

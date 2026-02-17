"""
صفحة تسجيل النشاط
Log Activity Component
"""

import streamlit as st
from datetime import date, datetime, timedelta
from auth import get_current_user
from database import (
    log_productivity, 
    get_logs_by_date, 
    get_categories,
    delete_log
)
from config import (
    PRODUCTIVITY_LEVELS, 
    get_time_slot_label,
    get_all_time_slots,
    DAYS_OF_WEEK_AR
)

def render_log_activity():
    """عرض صفحة تسجيل النشاط"""
    
    user = get_current_user()
    if not user:
        st.error("يرجى تسجيل الدخول أولاً")
        return
    
    st.markdown("""
    <h1 style="text-align: center; color: #9C27B0;">
        ✏️ تسجيل النشاط
    </h1>
    <p style="text-align: center; color: #888;">
        سجّل إنتاجيتك لأي فترة زمنية
    </p>
    """, unsafe_allow_html=True)
    
    # تبويبات
    tab1, tab2 = st.tabs(["📝 تسجيل جديد", "📋 سجلات اليوم"])
    
    with tab1:
        render_new_log_form(user)
    
    with tab2:
        render_today_logs(user)

def render_new_log_form(user):
    """نموذج تسجيل جديد"""
    
    st.markdown("### 📅 اختر التاريخ والوقت")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # اختيار التاريخ
        selected_date = st.date_input(
            "التاريخ",
            value=date.today(),
            max_value=date.today(),
            format="YYYY-MM-DD",
            key="log_date"
        )
        
        # عرض اسم اليوم
        day_name = DAYS_OF_WEEK_AR[selected_date.weekday()]
        st.markdown(f"**{day_name}**")
    
    with col2:
        # اختيار الفترة الزمنية
        time_slots = get_all_time_slots()
        slot_options = {f"{slot[1]} (الفترة {slot[0] + 1})": slot[0] for slot in time_slots}
        
        selected_slot_display = st.selectbox(
            "الفترة الزمنية",
            options=list(slot_options.keys()),
            key="log_time_slot"
        )
        selected_slot = slot_options.get(selected_slot_display, 0)
    
    st.markdown("---")
    
    # الحصول على الفئات
    categories = get_categories(user.id)
    category_options = {
        f"{cat.get('icon', '📌')} {cat.get('name_ar', cat.get('name', ''))}": cat.get('name', '') 
        for cat in categories
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_category_display = st.selectbox(
            "📁 الفئة",
            options=list(category_options.keys()),
            key="log_category"
        )
        selected_category = category_options.get(selected_category_display, "Work")
    
    with col2:
        notes = st.text_input("📝 ملاحظات (اختياري)", key="log_notes")
    
    st.markdown("---")
    st.markdown("### 🎯 اختر مستوى الإنتاجية")
    
    # التحقق من السجل الحالي
    existing_logs = get_logs_by_date(user.id, selected_date)
    existing_log = next((l for l in existing_logs if l.get("time_slot") == selected_slot), None)
    
    if existing_log:
        current_score = existing_log.get("score", 0)
        st.info(f"⚠️ هذه الفترة مسجلة بالفعل بـ {current_score} نقاط. التسجيل الجديد سيحدث السجل القديم.")
    
    # أزرار التقييم
    cols = st.columns(5)
    
    for i, (score, level) in enumerate(PRODUCTIVITY_LEVELS.items()):
        with cols[i]:
            # تنسيق الزر
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {level['color']}33 0%, {level['bg_color']} 100%);
                border: 2px solid {level['color']};
                border-radius: 15px;
                padding: 1rem;
                text-align: center;
                margin-bottom: 0.5rem;
            ">
                <div style="font-size: 2rem;">{level['emoji']}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: {level['color']};">{score}</div>
                <div style="color: #888; font-size: 0.9rem;">{level['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(
                f"اختيار",
                key=f"log_score_{score}",
                use_container_width=True
            ):
                result = log_productivity(
                    user_id=user.id,
                    log_date=selected_date,
                    time_slot=selected_slot,
                    score=score,
                    category=selected_category,
                    notes=notes if notes else None
                )
                if result["status"] == "success":
                    action = "تحديث" if existing_log else "تسجيل"
                    st.success(f"✅ تم {action} {level['name']} ({score} نقاط) بنجاح!")
                    st.balloons()
                else:
                    st.error(result["message"])

def render_today_logs(user):
    """عرض سجلات اليوم"""
    
    today = date.today()
    logs = get_logs_by_date(user.id, today)
    
    if not logs:
        st.info("لا توجد سجلات لهذا اليوم بعد. ابدأ بتسجيل إنتاجيتك! 🚀")
        return
    
    st.markdown(f"### 📊 سجلات اليوم ({len(logs)} سجل)")
    
    # ترتيب حسب الفترة الزمنية
    logs = sorted(logs, key=lambda x: x.get("time_slot", 0))
    
    for log in logs:
        slot = log.get("time_slot", 0)
        score = log.get("score", 0)
        category = log.get("category", "")
        notes = log.get("notes", "")
        level = PRODUCTIVITY_LEVELS[score]
        
        time_label = get_time_slot_label(slot)
        
        # الحصول على الفئة بالعربي
        categories = get_categories(user.id)
        cat_ar = next((c.get("name_ar", c.get("name", "")) for c in categories if c.get("name") == category), category)
        cat_icon = next((c.get("icon", "📌") for c in categories if c.get("name") == category), "📌")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {level['color']}22 0%, #1e1e1e 100%);
                border-right: 4px solid {level['color']};
                border-radius: 10px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #888;">⏰ {time_label}</span>
                        <span style="margin-right: 1rem; color: {level['color']};">{level['emoji']} {level['name']} ({score})</span>
                    </div>
                    <div>
                        <span style="color: #888;">{cat_icon} {cat_ar}</span>
                    </div>
                </div>
                {f'<p style="color: #666; margin: 0.5rem 0 0 0; font-size: 0.9rem;">📝 {notes}</p>' if notes else ''}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("")  # spacer
        
        with col3:
            if st.button("🗑️", key=f"delete_{log.get('id')}", help="حذف السجل"):
                result = delete_log(log.get("id"))
                if result["status"] == "success":
                    st.success("تم الحذف")
                    st.rerun()
                else:
                    st.error(result["message"])

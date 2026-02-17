"""
صفحة المهام (To-Do List)
Tasks Component
"""

import streamlit as st
from auth import get_current_user
from database import get_tasks, add_task, toggle_task, delete_task, update_task
from datetime import date

TASK_TYPES = {
    "daily": {"label": "⚡ يومية", "emoji": "⚡", "color": "#4CAF50", "description": "تتصفر كل يوم جديد"},
    "weekly": {"label": "📅 أسبوعية", "emoji": "📅", "color": "#2196F3", "description": "تتصفر كل أسبوع"},
    "monthly": {"label": "🎯 شهرية", "emoji": "🎯", "color": "#FF9800", "description": "تتصفر كل شهر"},
}

def render_tasks():
    """عرض صفحة المهام"""
    
    user = get_current_user()
    if not user:
        st.error("يرجى تسجيل الدخول أولاً")
        return
    
    st.markdown("""
    <h1 style="text-align: center; color: #4CAF50; margin-bottom: 0;">
        ✅ قائمة المهام
    </h1>
    <p style="text-align: center; color: #888; margin-top: 0.5rem;">
        نظّم مهامك اليومية والأسبوعية والشهرية
    </p>
    """, unsafe_allow_html=True)
    
    # ============ إضافة مهمة جديدة ============
    st.markdown("---")
    
    with st.expander("➕ إضافة مهمة جديدة", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_title = st.text_input("عنوان المهمة", placeholder="مثال: قراءة 20 صفحة...", key="new_task_title")
        with col2:
            task_type = st.selectbox(
                "النوع",
                options=list(TASK_TYPES.keys()),
                format_func=lambda x: TASK_TYPES[x]["label"],
                key="new_task_type"
            )
        
        # New fields for Phase 1
        col3, col4 = st.columns([1, 1])
        with col3:
            due_date = st.date_input("تاريخ الاستحقاق (اختياري)", value=None, key="new_task_due")
        with col4:
            # Placeholder for future list selection or other options
            pass
            
        new_notes = st.text_area("ملاحظات", placeholder="أضف تفاصيل إضافية...", height=68, key="new_task_notes")
        
        if st.button("✅ إضافة", type="primary", use_container_width=True):
            if new_title.strip():
                # Convert date to string if selected
                due_date_str = str(due_date) if due_date else None
                
                result = add_task(
                    user.id, 
                    new_title.strip(), 
                    task_type,
                    notes=new_notes,
                    due_date=due_date_str
                )
                
                if result["status"] == "success":
                    st.success("✅ تمت الإضافة!")
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.warning("يرجى كتابة عنوان المهمة")
    
    # ============ التبويبات ============
    tab_daily, tab_weekly, tab_monthly = st.tabs([
        "⚡ يومية",
        "📅 أسبوعية", 
        "🎯 شهرية"
    ])
    
    with tab_daily:
        _render_task_list(user.id, "daily")
    
    with tab_weekly:
        _render_task_list(user.id, "weekly")
    
    with tab_monthly:
        _render_task_list(user.id, "monthly")


def _render_task_list(user_id: str, task_type: str):
    """عرض قائمة المهام حسب النوع"""
    
    info = TASK_TYPES[task_type]
    tasks = get_tasks(user_id, task_type)
    
    # شريط التقدم
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("completed"))
    
    if total > 0:
        progress = completed / total
        bar_color = info["color"]
        
        st.markdown(f"""
        <div style="background: #1a1a2e; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="color: {bar_color}; font-weight: bold;">{info['emoji']} {completed}/{total} مكتملة</span>
                <span style="color: #888; font-size: 0.8rem;">{info['description']}</span>
            </div>
            <div style="background: #333; border-radius: 8px; height: 8px; overflow: hidden;">
                <div style="background: {bar_color}; height: 100%; width: {progress*100}%; border-radius: 8px; transition: width 0.5s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # عرض المهام
        for task in tasks:
            _render_task_item(user_id, task, info)
        
        # احتفال عند إنهاء الكل
        if completed == total:
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: {bar_color}22; border: 2px solid {bar_color}; border-radius: 12px; margin-top: 1rem;">
                <span style="font-size: 2rem;">🎉</span>
                <p style="color: {bar_color}; font-weight: bold; margin: 0.5rem 0 0 0;">
                    أحسنت! أكملت جميع المهام {info['label']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <span style="font-size: 3rem;">📋</span>
            <p style="margin-top: 0.5rem;">لا توجد مهام {info['label']} حالياً</p>
            <p style="font-size: 0.8rem; color: #555;">استخدم "➕ إضافة مهمة جديدة" بالأعلى</p>
        </div>
        """, unsafe_allow_html=True)


def _render_task_item(user_id: str, task: dict, type_info: dict):
    """عرض مهمة واحدة"""
    
    task_id = task.get("id", "")
    is_completed = task.get("completed", False)
    title = task.get("title", "")
    color = type_info["color"]
    
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col1:
        if st.button(
            "✅" if is_completed else "⬜",
            key=f"toggle_{task_id}",
            use_container_width=True
        ):
            toggle_task(user_id, task_id)
            st.rerun()
            
        # Star button
        is_starred = task.get("starred", False)
        if st.button("⭐" if is_starred else "☆", key=f"star_{task_id}", use_container_width=True):
            update_task(user_id, task_id, {"starred": not is_starred})
            st.rerun()
    
    with col2:
        text_style = f"text-decoration: line-through; color: #666;" if is_completed else f"color: #fafafa;"
        bg = f"{color}15" if not is_completed else "#1a1a1a"
        border = f"1px solid {color}44" if not is_completed else "1px solid #333"
        
        st.markdown(f"""
        <div style="background: {bg}; border: {border}; border-radius: 10px; padding: 0.7rem 1rem; display: flex; align-items: center; flex-direction: column; align-items: flex-start;">
            <div style="width: 100%; display: flex; justify-content: space-between;">
                <span style="{text_style} font-size: 1rem;">{title}</span>
                {f'<span style="font-size: 0.8rem; color: #ff9800;">📅 {task.get("due_date")}</span>' if task.get("due_date") else ''}
            </div>
            {f'<div style="margin-top: 0.5rem; font-size: 0.9rem; color: #aaa; width: 100%; padding-top: 0.5rem; border-top: 1px solid #ffffff11;">{task.get("notes")}</div>' if task.get("notes") else ''}
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🗑️", key=f"del_{task_id}", use_container_width=True):
            delete_task(user_id, task_id)
            st.rerun()

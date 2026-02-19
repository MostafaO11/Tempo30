"""
صفحة المتصدرين
Leaderboard Component
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from database import _get_logs_file, _load_json, get_user_profile
from auth import _load_users, get_current_user
from config import LOCAL_DATA_DIR

def get_leaderboard_data(period="weekly"):
    """
    تجميع بيانات المتصدرين
    period: 'weekly', 'monthly', 'all_time'
    """
    users_data = []
    all_users = _load_users()
    
    today = date.today()
    if period == "weekly":
        # بداية الأسبوع (السبت)
        days_since_sat = (today.weekday() + 2) % 7
        start_date = today - timedelta(days=days_since_sat)
        end_date = today
    elif period == "monthly":
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = date(2000, 1, 1) # All time
        end_date = today
    
    for email, user_info in all_users.items():
        user_id = user_info.get("id")
        # الاسم المعروض
        display_name = user_info.get("metadata", {}).get("display_name", email.split("@")[0])
        
        # تجاهل المستخدمين التجريبيين إذا لزم الأمر
        if "demo" in email and len(all_users) > 5:
            continue

        # قراءة السجلات
        logs_file = _get_logs_file(user_id)
        if not logs_file.exists():
            continue
            
        logs = _load_json(logs_file, [])
        
        # حساب النقاط للفترة
        score = 0
        logs_count = 0
        
        for log in logs:
            log_date_str = log.get("log_date")
            if not log_date_str: continue
            
            # تحويل التاريخ للتأكد
            try:
                l_date = date.fromisoformat(log_date_str)
                if start_date <= l_date <= end_date:
                    score += log.get("score", 0)
                    logs_count += 1
            except:
                continue
        
        if score > 0:
            users_data.append({
                "name": display_name,
                "score": score,
                "logs_count": logs_count,
                "id": user_id
            })
    
    # الترتيب
    users_data.sort(key=lambda x: x["score"], reverse=True)
    return users_data

def render_leaderboard():
    """عرض صفحة المتصدرين"""
    
    st.markdown("""
    <h1 style="text-align: center; color: #FFD700; margin-bottom: 2rem;">
        🏆 لوحة المتصدرين
    </h1>
    """, unsafe_allow_html=True)
    
    # اختيار الفترة
    col_per, col_empty = st.columns([2, 1])
    with col_per:
        period_map = {
            "الأسبوع الحالي (Sprint)": "weekly",
            "الشهر الحالي (Marathon)": "monthly",
            "كل الأوقات (Legends)": "all_time"
        }
        selected_period_label = st.radio(
            "الفترة",
            options=list(period_map.keys()),
            horizontal=True,
            label_visibility="collapsed"
        )
        period = period_map[selected_period_label]
    
    # جلب البيانات
    with st.spinner("جاري تحديث الترتيب..."):
        # لا نستخدم الـ cache هنا حالياً لتحديث فوري، يمكن إضافته لاحقاً
        data = get_leaderboard_data(period)
    
    if not data:
        st.info("لا توجد بيانات كافية لعرض المتصدرين حتى الآن. كن الأول! 🚀")
        return
        
    # عرض التوب 3 بشكل مميز
    top_3 = data[:3]
    others = data[3:]
    
    # منصة التتويج
    st.markdown("### 🌟 القمة")
    cols = st.columns(3)
    
    # ترتيب العرض: 2 (فضية) - 1 (ذهبية) - 3 (برونزية)
    podium_order = [1, 0, 2] # Indices in top_3 list
    
    for i in podium_order:
        if i < len(top_3):
            user = top_3[i]
            rank = i + 1
            
            if rank == 1:
                medal = "🥇"
                color = "#FFD700" # Gold
                height = "160px"
                icon_size = "3rem"
            elif rank == 2:
                medal = "🥈"
                color = "#C0C0C0" # Silver
                height = "130px"
                icon_size = "2.5rem"
            else:
                medal = "🥉"
                color = "#CD7F32" # Bronze
                height = "110px"
                icon_size = "2rem"
            
            # تمييز المستخدم الحالي
            current_user = get_current_user()
            is_me = current_user and current_user.id == user["id"]
            border = f"3px solid {color}" if not is_me else f"3px solid #4CAF50"
            bg = f"linear-gradient(180deg, {color}22 0%, {color}00 100%)"
            
            # بناء محتوى الاسم بشكل منفصل لتجنب مشاكل f-string
            name_html = user['name']
            if is_me:
                name_html += '<br><span style="font-size:0.8rem; color: #fff;">(أنت)</span>'
            
            # بناء البطاقة
            card_html = f"""
            <div style="
                background: {bg};
                border: {border};
                border-radius: 15px 15px 0 0;
                padding: 1rem;
                text-align: center;
                height: {height};
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                margin-top: {20 if rank == 1 else 50}px;
            ">
                <div style="font-size: {icon_size}; margin-bottom: 0.5rem;">{medal}</div>
                <div style="font-weight: bold; color: {color}; width: 100%; text-align: center; margin-bottom: 0.5rem;">
                    {name_html}
                </div>
                <div style="font-size: 1.2rem; color: #fff; font-weight: bold;">
                    {user['score']} <span style="font-size: 0.8rem; color: #aaa;">نقطة</span>
                </div>
            </div>
            """
            
            with cols[1 if rank == 1 else 0 if rank == 2 else 2]:
                st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("---")
    
    # باقي القائمة
    if others:
        st.markdown("### 📜 المراتب التالية")
        for idx, user in enumerate(others):
            rank = idx + 4
            current_user = get_current_user()
            is_me = current_user and current_user.id == user["id"]
            
            bg_color = "rgba(255, 255, 255, 0.05)" if not is_me else "rgba(76, 175, 80, 0.1)"
            border_color = "#333" if not is_me else "#4CAF50"
            
            st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 20px;
                margin-bottom: 10px;
            ">
                <div style="width: 40px; font-weight: bold; color: #888; font-size: 1.1rem;">#{rank}</div>
                <div style="flex-grow: 1; font-weight: bold; color: #eee;">
                    {user['name']} {"<span style='color:#4CAF50; font-size:0.8rem;'>(أنت)</span>" if is_me else ""}
                </div>
                <div style="text-align: left;">
                    <span style="color: #FFC107; font-weight: bold; font-size: 1.1rem;">{user['score']}</span>
                    <span style="color: #666; font-size: 0.8rem; margin-right: 5px;">نقطة</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    # إذا لم يكن المستخدم في القائمة الكلية
    current_user = get_current_user()
    if current_user:
        user_in_list = any(u['id'] == current_user.id for u in data)
        if not user_in_list:
            st.info("لم تظهر في القائمة بعد. سجّل المزيد من النقاط لتنضم للمنافسة! 💪")

"""
لوحة التحكم الرئيسية
Dashboard Component
"""

import streamlit as st
from datetime import date, datetime, timedelta
from auth import get_current_user
from database import get_logs_by_date, log_productivity, get_user_profile, get_categories
from analytics import calculate_daily_score, calculate_progress_percentage
from config import (
    PRODUCTIVITY_LEVELS, 
    get_current_time_slot, 
    get_time_slot_label,
    get_all_time_slots
)

# احتفالات مختلفة لكل مستوى
CELEBRATIONS = {
    0: {
        "animation": "💩",
        "message": "Lazy Shit! 😴💤",
        "effect": None,
        "color": "#6c757d"
    },
    1: {
        "animation": "👣",
        "message": "خطوة صغيرة... استمر! 💪",
        "effect": None,
        "color": "#fd7e14"
    },
    2: {
        "animation": "⚡",
        "message": "جيد! أنت على الطريق الصحيح! 🎯",
        "effect": None,
        "color": "#ffc107"
    },
    3: {
        "animation": "🌟⭐✨",
        "message": "رائع! إنتاجية عالية! 🏆",
        "effect": "snow",
        "color": "#90EE90"
    },
    4: {
        "animation": "🔥🚀🎉🏆⭐",
        "message": "مذهل! أنت في ذروة الأداء! 🔥💯",
        "effect": "balloons",
        "color": "#28a745"
    }
}

def show_celebration(score: int):
    """عرض احتفال بسيط"""
    celebration = CELEBRATIONS.get(score, CELEBRATIONS[0])
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, {celebration['color']}33 0%, #1e1e1e 100%);
        border-radius: 20px;
        border: 2px solid {celebration['color']};
        margin: 1rem 0;
    ">
        <div style="font-size: 4rem;">{celebration['animation']}</div>
        <p style="font-size: 1.5rem; color: {celebration['color']}; margin-top: 1rem; font-weight: bold;">
            {celebration['message']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if celebration['effect'] == 'balloons':
        st.balloons()
    elif celebration['effect'] == 'snow':
        st.snow()

def get_previous_time_slot() -> int:
    """الحصول على رقم الفترة الزمنية السابقة"""
    current = get_current_time_slot()
    return max(0, current - 1)

def get_time_remaining_in_slot() -> tuple:
    """الحصول على الوقت المتبقي في الفترة الحالية"""
    now = datetime.now()
    current_minute = now.minute
    current_second = now.second
    
    if current_minute < 30:
        remaining_minutes = 29 - current_minute
        remaining_seconds = 59 - current_second
    else:
        remaining_minutes = 59 - current_minute
        remaining_seconds = 59 - current_second
    
    return remaining_minutes, remaining_seconds

def render_dashboard():
    """عرض لوحة التحكم الرئيسية"""
    
    user = get_current_user()
    if not user:
        st.error("يرجى تسجيل الدخول أولاً")
        return
    
    # العنوان
    st.markdown("""
    <h1 style="text-align: center; color: #4CAF50; margin-bottom: 0;">
        🎯 لوحة التحكم
    </h1>
    <p style="text-align: center; color: #888; margin-top: 0.5rem;">
        سجّل إنتاجيتك بنقرة واحدة
    </p>
    """, unsafe_allow_html=True)
    
    # الحصول على البيانات
    today = date.today()
    logs = get_logs_by_date(user.id, today)
    profile = get_user_profile(user.id)
    daily_goal = profile.get("daily_goal", 100) if profile else 100
    
    # حساب النقاط
    daily_score = calculate_daily_score(logs)
    progress = calculate_progress_percentage(daily_score, daily_goal)
    
    # التحقق من وجود احتفال
    if st.session_state.get("show_celebration") is not None:
        show_celebration(st.session_state.show_celebration)
        st.session_state.show_celebration = None
    
    # =============================================
    # الساعة الرملية - الوقت المتبقي (نمط Stopwatch)
    # =============================================
    
    current_slot = get_current_time_slot()
    current_slot_label = get_time_slot_label(current_slot)
    
    # حساب وقت انتهاء الفترة الحالية
    now = datetime.now()
    if now.minute < 30:
        end_minute = 30
        end_hour = now.hour
    else:
        end_minute = 0
        end_hour = now.hour + 1
    
    # timestamp لوقت الانتهاء بالمللي ثانية
    import time
    end_timestamp = int(time.mktime(now.replace(hour=end_hour % 24, minute=end_minute, second=0, microsecond=0).timetuple()) * 1000)
    
    import streamlit.components.v1 as components
    
    # التحقق هل الفترة السابقة مسجلة (لإيقاف المنبه)
    prev_slot = get_previous_time_slot()
    logged_slots_set = {log.get("time_slot") for log in logs}
    prev_slot_logged = prev_slot in logged_slots_set
    # هل الوقت انتهى فعلاً؟
    should_alert = (not prev_slot_logged) and (remaining_min <= 0 if (remaining_min := get_time_remaining_in_slot()[0]) is not None else False)
    
    # "true" أو "false" لـ JavaScript
    js_should_alert = "true" if should_alert else "false"
    
    timer_html = f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 1rem; border-radius: 15px; text-align: center; font-family: 'Tajawal', sans-serif;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 2rem; flex-wrap: wrap;">
            <div>
                <p style="color: #888; margin: 0; font-size: 0.8rem;">⏰ الفترة الحالية</p>
                <p style="color: #4CAF50; margin: 0; font-size: 1.2rem; font-weight: bold;">{current_slot_label}</p>
            </div>
            <div id="timer-box" style="background: #0d1b2a; padding: 1rem 2rem; border-radius: 10px; border: 2px solid #4CAF50;">
                <p style="color: #888; margin: 0; font-size: 0.8rem;">⏳ الوقت المتبقي</p>
                <p id="countdown-timer" style="color: #ffc107; margin: 0; font-size: 1.8rem; font-weight: bold; font-family: monospace;">
                    --:--
                </p>
            </div>
        </div>
    </div>
    
    <script>
    (function() {{
        var endTime = {end_timestamp};
        
        function updateTimer() {{
            var timerElement = document.getElementById('countdown-timer');
            var timerBox = document.getElementById('timer-box');
            if (!timerElement) return;
            
            var now = Date.now();
            var remaining = endTime - now;
            
            if (remaining <= 0) {{
                timerElement.innerHTML = '00:00 ⏰';
                timerElement.style.color = '#ff4444';
                return;
            }}
            
            var totalSeconds = Math.floor(remaining / 1000);
            var minutes = Math.floor(totalSeconds / 60);
            var seconds = totalSeconds % 60;
            
            var minStr = minutes < 10 ? '0' + minutes : minutes;
            var secStr = seconds < 10 ? '0' + seconds : seconds;
            timerElement.innerHTML = minStr + ':' + secStr;
            
            if (minutes < 2) {{
                timerElement.style.color = '#ff6b6b';
            }} else {{
                timerElement.style.color = '#ffc107';
            }}
        }}
        
        updateTimer();
        setInterval(updateTimer, 1000);
    }})();
    </script>
    """
    components.html(timer_html, height=120)
    
    # تحذير عند اقتراب انتهاء الفترة
    remaining_min, _ = get_time_remaining_in_slot()
    if remaining_min <= 2:
        st.warning(f"⚠️ الفترة الحالية على وشك الانتهاء!")
    
    # =============================================
    # ملخص اليوم
    # =============================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.9rem;">📊 النقاط اليومية</p>
            <h2 style="color: #4CAF50; margin: 0.5rem 0 0 0; font-size: 2rem;">{daily_score}</h2>
            <p style="color: #666; margin: 0; font-size: 0.8rem;">من {daily_goal}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.9rem;">✅ الفترات المسجلة</p>
            <h2 style="color: #9C27B0; margin: 0.5rem 0 0 0; font-size: 2rem;">{len(logs)}</h2>
            <p style="color: #666; margin: 0; font-size: 0.8rem;">من 48 فترة</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_score = daily_score / len(logs) if logs else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1f3d2d 0%, #1a2e1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.9rem;">📈 متوسط التقييم</p>
            <h2 style="color: #4CAF50; margin: 0.5rem 0 0 0; font-size: 2rem;">{avg_score:.1f}</h2>
            <p style="color: #666; margin: 0; font-size: 0.8rem;">من 4</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        remaining_goal = max(0, daily_goal - daily_score)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #3d2d1f 0%, #2e2a1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.9rem;">🎯 المتبقي للهدف</p>
            <h2 style="color: #FF9800; margin: 0.5rem 0 0 0; font-size: 2rem;">{remaining_goal}</h2>
            <p style="color: #666; margin: 0; font-size: 0.8rem;">نقطة</p>
        </div>
        """, unsafe_allow_html=True)
    
    # =============================================
    # مؤشر التقدم الدائري + مقارنة الأمس
    # =============================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    progress_color = "#28a745" if progress >= 100 else "#ffc107" if progress >= 50 else "#fd7e14"
    clamped = min(progress, 100)
    circumference = 2 * 3.14159 * 54
    dash_offset = circumference - (clamped / 100) * circumference
    
    # جلب بيانات الأمس
    yesterday = today - timedelta(days=1)
    yesterday_logs = get_logs_by_date(user.id, yesterday)
    yesterday_score = calculate_daily_score(yesterday_logs)
    diff = daily_score - yesterday_score
    diff_icon = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
    diff_color = "#4CAF50" if diff > 0 else "#f44336" if diff < 0 else "#888"
    diff_text = f"+{diff}" if diff > 0 else str(diff)
    
    col_circle, col_compare = st.columns([1, 2])
    
    with col_circle:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <svg width="140" height="140" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="54" fill="none" stroke="#333" stroke-width="8"/>
                <circle cx="60" cy="60" r="54" fill="none" stroke="{progress_color}" stroke-width="8"
                    stroke-linecap="round"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{dash_offset}"
                    transform="rotate(-90 60 60)"
                    style="transition: stroke-dashoffset 0.8s ease;"/>
                <text x="60" y="55" text-anchor="middle" fill="{progress_color}" font-size="22" font-weight="bold">{progress:.0f}%</text>
                <text x="60" y="75" text-anchor="middle" fill="#888" font-size="10">الهدف اليومي</text>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with col_compare:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 1.5rem; border-radius: 15px; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <p style="color: #888; margin: 0 0 0.5rem 0; font-size: 0.9rem;">📊 مقارنة مع الأمس</p>
            <div style="display: flex; justify-content: space-around; align-items: center; margin-bottom: 1rem;">
                <div style="text-align: center;">
                    <p style="color: #666; margin: 0; font-size: 0.8rem;">الأمس</p>
                    <p style="color: #FF9800; margin: 0; font-size: 1.5rem; font-weight: bold;">{yesterday_score}</p>
                </div>
                <div style="text-align: center;">
                    <p style="color: {diff_color}; margin: 0; font-size: 1.8rem;">{diff_icon}</p>
                    <p style="color: {diff_color}; margin: 0; font-size: 0.9rem; font-weight: bold;">{diff_text}</p>
                </div>
                <div style="text-align: center;">
                    <p style="color: #666; margin: 0; font-size: 0.8rem;">اليوم</p>
                    <p style="color: #4CAF50; margin: 0; font-size: 1.5rem; font-weight: bold;">{daily_score}</p>
                </div>
            </div>
            <p style="color: #aaa; margin: 0; text-align: center; font-size: 0.85rem;">
                {"🔥 أنت تتفوق على الأمس! استمر!" if diff > 0 else "💪 لحق نفسك! الأمس كان أفضل بـ " + str(abs(diff)) + " نقطة" if diff < 0 else "🟰 نفس مستوى الأمس"}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # =============================================
    # تسجيل الفترة - مع anchor للتمرير
    # =============================================
    
    st.markdown("---")
    st.markdown('<div id="rating-section"></div>', unsafe_allow_html=True)
    
    # التحقق من الفترة المختارة
    selected_slot = st.session_state.get("selected_slot")
    if selected_slot is not None:
        target_slot = selected_slot
        is_editing = True
    else:
        target_slot = get_previous_time_slot()
        is_editing = False
    
    target_slot_label = get_time_slot_label(target_slot)
    
    # التحقق مما إذا كانت الفترة مسجلة
    logged_slots = {log.get("time_slot"): log for log in logs}
    is_target_logged = target_slot in logged_slots
    
    if is_editing:
        title = "✏️ تعديل فترة"
        title_color = "#FF9800"
    else:
        title = "⏮️ الفترة السابقة"
        title_color = "#9C27B0"
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <h3 style="color: {title_color}; margin-bottom: 0.5rem;">{title}</h3>
        <p style="font-size: 1.5rem; color: #fafafa; margin: 0;">{target_slot_label}</p>
        {"<span style='color: #28a745;'>✓ مسجلة</span>" if is_target_logged else "<span style='color: #888;'>غير مسجلة</span>"}
    </div>
    """, unsafe_allow_html=True)
    
    if is_editing:
        if st.button("❌ إلغاء التحديد", key="cancel_edit"):
            st.session_state.selected_slot = None
            st.rerun()
    
    # الحصول على الفئات
    categories = get_categories(user.id)
    category_options = {f"{cat.get('icon', '📌')} {cat.get('name_ar', cat.get('name', ''))}": cat.get('name', '') for cat in categories}
    
    col_cat, col_empty = st.columns([2, 1])
    with col_cat:
        selected_category_display = st.selectbox(
            "📁 الفئة",
            options=list(category_options.keys()),
            key="dashboard_category"
        )
        selected_category = category_options.get(selected_category_display, "Work")
    
    st.markdown("<h4 style='text-align: center; color: #888;'>اختر مستوى الإنتاجية:</h4>", unsafe_allow_html=True)
    
    # أزرار التقييم
    cols = st.columns(5)
    
    for i, (score, level) in enumerate(PRODUCTIVITY_LEVELS.items()):
        with cols[i]:
            btn_label = f"{level['emoji']}\n{score}\n{level['name']}"
            if st.button(
                btn_label,
                key=f"quick_score_{score}",
                use_container_width=True,
                type="primary" if score == 4 else "secondary"
            ):
                try:
                    result = log_productivity(
                        user_id=user.id,
                        log_date=today,
                        time_slot=target_slot,
                        score=score,
                        category=selected_category
                    )
                    if result.get("status") == "success":
                        st.session_state.show_celebration = score
                        st.session_state.selected_slot = None
                        st.rerun()
                    else:
                        st.error(result.get("message", "حدث خطأ"))
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")
    
    # =============================================
    # ملخص اليوم - شبكة بسيطة
    # =============================================
    
    st.markdown("---")
    st.markdown("### 📅 ملخص اليوم")
    st.markdown("<small style='color: #888;'>💡 اضغط على أي فترة لتسجيلها أو تعديلها</small>", unsafe_allow_html=True)
    
    # عرض الشبكة
    render_day_grid_simple(logs, current_slot)
    
    # =============================================
    # زر التسجيل السريع العائم (Sticky)
    # =============================================
    import streamlit.components.v1 as components
    
    prev_slot = get_previous_time_slot()
    prev_logged = prev_slot in {log.get("time_slot") for log in logs}
    btn_text = "✏️ تعديل الفترة السابقة" if prev_logged else "⚡ سجّل الفترة السابقة"
    btn_bg = "#FF9800" if prev_logged else "#4CAF50"
    
    sticky_html = f"""
    <div id="sticky-log-btn" style="
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        z-index: 9999; 
        background: linear-gradient(135deg, {btn_bg}, {btn_bg}cc);
        color: white; padding: 12px 28px; border-radius: 50px;
        font-family: 'Tajawal', sans-serif; font-size: 1rem; font-weight: bold;
        cursor: pointer; box-shadow: 0 4px 15px {btn_bg}66;
        transition: transform 0.2s, box-shadow 0.2s;
        text-align: center;
    " onclick="window.parent.document.querySelector('[id*=rating-section]')?.scrollIntoView({{behavior: 'smooth'}})"
       onmouseover="this.style.transform='translateX(-50%) scale(1.05)'; this.style.boxShadow='0 6px 20px {btn_bg}88'"
       onmouseout="this.style.transform='translateX(-50%) scale(1)'; this.style.boxShadow='0 4px 15px {btn_bg}66'"
    >
        {btn_text}
    </div>
    """
    components.html(sticky_html, height=0)

def render_day_grid_simple(logs: list, current_slot: int):
    """عرض شبكة بسيطة بأزرار Streamlit مع الفئات والألوان"""
    
    logged_slots = {log.get("time_slot"): log for log in logs}
    selected_slot = st.session_state.get("selected_slot")
    
    # بناء خريطة ألوان وأسماء الفئات
    user = get_current_user()
    cat_colors = {}
    cat_icons = {}
    cat_names = {}
    if user:
        categories = get_categories(user.id)
        for cat in categories:
            cat_colors[cat.get('name', '')] = cat.get('color', '#4CAF50')
            cat_icons[cat.get('name', '')] = cat.get('icon', '📌')
            cat_names[cat.get('name', '')] = cat.get('name_ar', cat.get('name', ''))
    
    # إضافة JavaScript للتمرير عند اختيار فترة
    if selected_slot is not None:
        import streamlit.components.v1 as components
        components.html("""
        <script>
        (function() {
            var target = window.parent.document.getElementById('rating-section');
            if (target) {
                setTimeout(function() {
                    target.scrollIntoView({behavior: 'smooth', block: 'start'});
                }, 300);
            }
        })();
        </script>
        """, height=0)
    
    # 6 صفوف × 8 أعمدة
    for row in range(6):
        cols = st.columns(8)
        for col_idx in range(8):
            slot = row * 8 + col_idx
            with cols[col_idx]:
                log = logged_slots.get(slot)
                
                hour = slot // 2
                minute = (slot % 2) * 30
                
                is_selected = selected_slot == slot
                is_current = slot == current_slot
                
                if log:
                    score = log.get("score", 0)
                    level = PRODUCTIVITY_LEVELS[score]
                    category = log.get("category", "")
                    cat_icon = cat_icons.get(category, level["emoji"])
                    cat_color = cat_colors.get(category, level["color"])
                    cat_name = cat_names.get(category, category)
                    
                    # عرض الفترة مع اسم ولون الفئة
                    st.markdown(f"""
                    <div style="background: {cat_color}22; border: 2px solid {cat_color}; border-radius: 8px; padding: 4px; text-align: center; margin-bottom: 4px; min-height: 65px; display: flex; flex-direction: column; justify-content: center;">
                        <div style="font-size: 0.65rem; color: #aaa;">{hour}:{minute:02d}</div>
                        <div style="font-size: 1rem;">{cat_icon}</div>
                        <div style="font-size: 0.55rem; color: {cat_color}; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{cat_name}</div>
                        <div style="font-size: 0.55rem; color: #888;">{level['emoji']} {score}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # فترة غير مسجلة
                    border = "#4CAF50" if is_current else "#ffc107" if is_selected else "#333"
                    st.markdown(f"""
                    <div style="background: #1a1a1a; border: 1px solid {border}; border-radius: 8px; padding: 4px; text-align: center; margin-bottom: 4px; min-height: 55px; display: flex; flex-direction: column; justify-content: center; opacity: 0.6;">
                        <div style="font-size: 0.7rem; color: #666;">{hour}:{minute:02d}</div>
                        <div style="font-size: 1rem; color: #444;">·</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if st.button(
                    "📝" if not log else "✏️",
                    key=f"grid_{slot}",
                    use_container_width=True,
                ):
                    st.session_state.selected_slot = slot
                    st.session_state.scroll_to_top = True
                    st.rerun()

"""
صفحة التحليلات والرسوم البيانية
Analytics Page Component
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
import pandas as pd
import math
from auth import get_current_user
from database import get_logs_by_range, get_user_profile
from analytics import (
    generate_heatmap_data,
    calculate_trends,
    get_category_breakdown,
    get_statistics_summary,
    calculate_daily_score,
    get_logs_summary_by_date,
    compare_periods,
    calculate_longest_streak,
    count_full_goal_days,
    get_score_distribution,
    get_time_patterns,
    generate_recommendations,
    generate_period_report,
    generate_calendar_data
)
from config import PRODUCTIVITY_LEVELS, DAYS_OF_WEEK_AR

def render_analytics():
    """عرض صفحة التحليلات"""
    
    user = get_current_user()
    if not user:
        st.error("يرجى تسجيل الدخول أولاً")
        return
    
    st.markdown("""
    <h1 style="text-align: center; color: #2196F3;">
        📊 التحليلات والإحصائيات
    </h1>
    """, unsafe_allow_html=True)
    
    # تخطيط لوحة القيادة - Dashboard Layout
    # الصف العلوي: الفلاتر والإجراءات
    with st.container():
        c1, c2, c3, c4 = st.columns([1.5, 1.5, 2, 1])
        
        with c1:
            period = st.selectbox(
                "📅 الفترة",
                options=["الأسبوع الحالي", "الشهر الحالي", "آخر 7 أيام", "آخر 30 يوم"],
                key="analytics_period",
                label_visibility="collapsed"
            )
        
        # حساب التواريخ بناءً على الفترة المختارة (كما هو، لكن مختصر)
        today = date.today()
        if period == "الأسبوع الحالي":
            days_since_saturday = (today.weekday() + 2) % 7
            default_start = today - timedelta(days=days_since_saturday)
            default_end = default_start + timedelta(days=6)
        elif period == "الشهر الحالي":
            default_start = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            default_end = next_month - timedelta(days=next_month.day)
        elif period == "آخر 7 أيام":
            default_start = today - timedelta(days=6)
            default_end = today
        else:
            default_start = today - timedelta(days=29)
            default_end = today

        # تحديث الجلسة
        if "prev_analytics_period" not in st.session_state:
            st.session_state.prev_analytics_period = period
        if st.session_state.prev_analytics_period != period:
            st.session_state.prev_analytics_period = period
            st.session_state.analytics_start = default_start
            st.session_state.analytics_end = default_end

        with c2:
            start_date = st.date_input("من", value=default_start, key="analytics_start", label_visibility="collapsed")
        
        with c3:
            end_date = st.date_input("إلى", value=today, key="analytics_end", label_visibility="collapsed")
            
        # جلب البيانات الأولية
        all_logs = get_logs_by_range(user.id, start_date, end_date)
        
        with c4:
            # زر التصدير
            if all_logs:
                df_export = pd.DataFrame(all_logs)
                csv = df_export.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تصدير CSV",
                    data=csv,
                    file_name=f"productivity_logs_{start_date}_{end_date}.csv",
                    mime="text/csv",
                )
    
    if not all_logs:
        st.warning("لا توجد بيانات في هذه الفترة. ابدأ بتسجيل إنتاجيتك! 🚀")
        return

    # فلترة الفئات - Category Filter
    # نستخرج الفئات الموجودة في السجلات
    available_categories = sorted(list(set([log.get("category", "بدون فئة") for log in all_logs])))
    
    if available_categories:
        with st.expander("🔍 تصفية حسب الفئة", expanded=False):
            selected_categories = st.multiselect(
                "اختر الفئات للعرض:",
                options=available_categories,
                default=available_categories
            )
            
        # تطبيق الفلتر
        if selected_categories:
            logs = [log for log in all_logs if log.get("category", "بدون فئة") in selected_categories]
        else:
            logs = []
            st.warning("يرجى اختيار فئة واحدة على الأقل.")
            return
    else:
        logs = all_logs

    profile = get_user_profile(user.id)
    daily_goal = profile.get("daily_goal", 100) if profile else 100
    weekly_goal = profile.get("weekly_goal", 500) if profile else 500
    monthly_goal = profile.get("monthly_goal", 2000) if profile else 2000
    
    # 1. بطاقات الأداء الرئيسية (KPIs)
    stats = get_statistics_summary(logs, daily_goal)
    render_stats_cards(stats)
    
    st.markdown("---")
    
    # 2. لوحة الرسوم البيانية (Grid Layout)
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        # الاتجاه العام + الهدف
        render_trends_simplified(logs, daily_goal)
        
    with col_side:
        # تقدم الأهداف (دائري أو شريطي مبسط)
        render_goals_progress_simplified(user.id, weekly_goal, monthly_goal, logs)

    st.markdown("---")

    # 3. التبويبات التفصيلية
    tab_calendar, tab_cat, tab_heat, tab_time, tab_compare, tab_details = st.tabs([
        "📅 التقويم",
        "📊 الفئات",
        "🗓️ الحرارة",
        "⏰ الوقت",
        "🔄 مقارنة",
        "📋 تفاصيل"
    ])
    
    with tab_calendar:
        render_calendar_view(logs, daily_goal, start_date, end_date)
        
    with tab_cat:
        render_category_analysis(logs)
        
    with tab_heat:
         render_heatmap(logs)
         
    with tab_time:
        render_time_patterns(logs)
        
    with tab_compare:
        render_period_comparison(user.id, start_date, end_date)
        
    with tab_details:
        render_detailed_stats(logs, stats)

def render_calendar_view(logs: list, daily_goal: int, start_date: date, end_date: date):
    """عرض التقويم التفاعلي"""
    st.markdown("### 📅 تقويم الإنتاجية")
    
    data = generate_calendar_data(logs, daily_goal, start_date, end_date)
    stats = data["stats"]
    
    # ملخص سريع
    st.markdown(f"""
<div class="calendar-summary">
    <div class="summary-item">
        <div class="summary-count" style="color: #4CAF50;">{stats['achieved']}</div>
        <div class="summary-label">تجاوز الهدف</div>
    </div>
    <div class="summary-item">
        <div class="summary-count" style="color: #f44336;">{stats['missed']}</div>
        <div class="summary-label">لم يتحقق</div>
    </div>
    <div class="summary-item">
        <div class="summary-count" style="color: #9e9e9e;">{stats['vacation']}</div>
        <div class="summary-label">إجازة/راحة</div>
    </div>
</div>
""", unsafe_allow_html=True)
    
    # رأس الجدول (أيام الأسبوع)
    #cols = st.columns(7)
    #days_header = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    #for i, d in enumerate(days_header):
    #    cols[i].markdown(f"<div class='calendar-header-cell'>{d}</div>", unsafe_allow_html=True)
    
    # شبكة التقويم
    cards_html = '<div class="calendar-grid">'
    
    # رؤوس الأعمدة
    days_header = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
    for d in days_header:
        cards_html += f'<div class="calendar-header-cell">{d}</div>'
    
    # تعبئة فراغات قبل بداية الشهر/الفترة إذا لزم الأمر؟ 
    # في حالة "الأسبوع الحالي" نبدأ دائماً من السبت.
    # لكن إذا اختار "الشهر الحالي" قد يبدأ الشهر في وسط الأسبوع.
    # سنحتاج إلى إضافة خلايا فارغة في البداية لضبط المحاذاة مع أيام الأسبوع.
    
    start_weekday = start_date.weekday() # 0 = Monday, 5 = Saturday, 6 = Sunday
    # Our grid starts Saturday (index 0 for us)
    # Mapping Python weekday to our grid index:
    # Sat(5)->0, Sun(6)->1, Mon(0)->2, Tue(1)->3, Wed(2)->4, Thu(3)->5, Fri(4)->6
    
    grid_start_index = (start_weekday + 2) % 7
    
    for _ in range(grid_start_index):
        cards_html += '<div class="calendar-card future" style="opacity: 0;"></div>'
        
    for day in data["days"]:
        status = day["status"]
        date_str = day["date"].strftime("%Y-%m-%d")
        
        # محتوى البطاقة
        if status == "vacation":
            score_display = "إجازة"
            diff_display = "-"
            diff_class = ""
        elif status == "future":
            score_display = "-"
            diff_display = ""
            diff_class = ""
        else:
            score_display = f"{day['score']}"
            diff = day['difference']
            sign = "+" if diff > 0 else ""
            diff_display = f"{sign}{diff}"
            diff_class = "diff-val"
            
        cards_html += f'''
<div class="calendar-card {status}">
    <div class="date-header">
        <span class="day-name">{day['day_name']}</span>
        <span class="day-num">{day['day_num']}</span>
    </div>
    <div class="score-container">
        <div class="score-val">{score_display}</div>
        <div class="{diff_class}">{diff_display}</div>
    </div>
</div>
'''
        
    cards_html += '</div>'
    
    st.markdown(cards_html, unsafe_allow_html=True)

    # حساب المعدل المطلوب
    from datetime import date, timedelta
    today = date.today()
    
    from auth import get_current_user
    from database import get_user_profile
    
    curr_user = get_current_user()
    if curr_user:
        profile = get_user_profile(curr_user.id)
        w_goal = profile.get("weekly_goal", 500)
        m_goal = profile.get("monthly_goal", 2000)
        
        # Week Stats
        days_since_sat = (today.weekday() + 2) % 7
        week_start = today - timedelta(days=days_since_sat)
        w_logs = get_logs_by_range(curr_user.id, week_start, today)
        w_score = sum(l.get("score", 0) for l in w_logs)
        w_remaining = max(0, w_goal - w_score)
        w_days_left = 7 - days_since_sat # Includes today if we haven't synced yet? Assuming end of day calculation logic usually.
        # If "today" adds to score, then days left includes today.
        
        if w_days_left > 0:
            w_rate = w_remaining / w_days_left
        else:
            w_rate = 0 if w_remaining <= 0 else w_remaining # Should not happen if days logic correct
            
        # Month Stats
        m_start = today.replace(day=1)
        m_logs = get_logs_by_range(curr_user.id, m_start, today)
        m_score = sum(l.get("score", 0) for l in m_logs)
        m_remaining = max(0, m_goal - m_score)
        
        # Days in month
        import calendar
        _, num_days = calendar.monthrange(today.year, today.month)
        m_days_left = num_days - today.day + 1 # +1 to include today
        
        if m_days_left > 0:
            m_rate = m_remaining / m_days_left
        else:
            m_rate = 0
            
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 1rem; background: rgba(33, 150, 243, 0.1); border: 1px solid #2196F3; border-radius: 10px;">
            <h5 style="color: #2196F3; margin-bottom: 0.5rem;">🎯 المعدل المطلوب لتحقيق الأهداف (بناءً على الوضع الحالي)</h5>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div style="flex: 1;">
                    <span style="color: #aaa;">الأسبوعي ({w_remaining} نقطة متبقية / {w_days_left} يوم):</span>
                    <strong style="color: #fafafa; font-size: 1.1rem;">{w_rate:.1f} نقطة/يوم</strong>
                </div>
                <div style="flex: 1;">
                    <span style="color: #aaa;">الشهري ({m_remaining} نقطة متبقية / {m_days_left} يوم):</span>
                    <strong style="color: #fafafa; font-size: 1.1rem;">{m_rate:.1f} نقطة/يوم</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_goals_progress(user_id: str, weekly_goal: int, monthly_goal: int):
    """عرض تقدم الأهداف الأسبوعية والشهرية"""
    
    from datetime import date, timedelta
    
    today = date.today()
    
    # حساب بداية الأسبوع (السبت)
    days_since_saturday = (today.weekday() + 2) % 7
    week_start = today - timedelta(days=days_since_saturday)
    
    # حساب بداية الشهر
    month_start = today.replace(day=1)
    
    # جلب البيانات
    week_logs = get_logs_by_range(user_id, week_start, today)
    month_logs = get_logs_by_range(user_id, month_start, today)
    
    # حساب النقاط
    week_score = sum(log.get("score", 0) for log in week_logs)
    month_score = sum(log.get("score", 0) for log in month_logs)
    
    # حساب النسب
    week_progress = min((week_score / weekly_goal * 100), 100) if weekly_goal > 0 else 0
    month_progress = min((month_score / monthly_goal * 100), 100) if monthly_goal > 0 else 0
    
    st.markdown("### 🎯 تقدم الأهداف")
    
    col1, col2 = st.columns(2)
    
    with col1:
        week_color = "#28a745" if week_progress >= 100 else "#ffc107" if week_progress >= 50 else "#fd7e14"
        week_remaining = max(0, weekly_goal - week_score)
        days_left_week = 7 - days_since_saturday - 1
        
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <span style="color: #fafafa; font-size: 1.2rem; font-weight: bold; white-space: nowrap;">📆 الهدف الأسبوعي</span>
        <span style="color: {week_color}; font-size: 1.5rem; font-weight: bold;">{week_progress:.0f}%</span>
    </div>
    <div style="background: #333; border-radius: 10px; height: 25px; overflow: hidden; margin-bottom: 1rem;">
        <div style="background: linear-gradient(90deg, {week_color}, {week_color}88); height: 100%; width: {week_progress}%; transition: width 0.5s; border-radius: 10px;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; color: #888; font-size: 0.9rem;">
        <span>{week_score} / {weekly_goal} نقطة</span>
        <span>متبقي: {week_remaining} ({days_left_week} أيام)</span>
    </div>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        month_color = "#28a745" if month_progress >= 100 else "#ffc107" if month_progress >= 50 else "#fd7e14"
        month_remaining = max(0, monthly_goal - month_score)
        days_left_month = (today.replace(month=today.month % 12 + 1, day=1) - timedelta(days=1)).day - today.day
        
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); padding: 1.5rem; border-radius: 15px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
        <span style="color: #fafafa; font-size: 1.2rem; font-weight: bold; white-space: nowrap;">🗓️ الهدف الشهري</span>
        <span style="color: {month_color}; font-size: 1.5rem; font-weight: bold;">{month_progress:.0f}%</span>
    </div>
    <div style="background: #333; border-radius: 10px; height: 25px; overflow: hidden; margin-bottom: 1rem;">
        <div style="background: linear-gradient(90deg, {month_color}, {month_color}88); height: 100%; width: {month_progress}%; transition: width 0.5s; border-radius: 10px;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; color: #888; font-size: 0.9rem;">
        <span>{month_score} / {monthly_goal} نقطة</span>
        <span>متبقي: {month_remaining} ({days_left_month} يوم)</span>
    </div>
</div>
""", unsafe_allow_html=True)

def render_stats_cards(stats: dict):
    """عرض بطاقات الإحصائيات"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">📊 إجمالي النقاط</p>
    <h2 style="color: #4CAF50; margin: 0.5rem 0 0 0;">{stats['total_score']}</h2>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">✅ عدد السجلات</p>
    <h2 style="color: #9C27B0; margin: 0.5rem 0 0 0;">{stats['total_entries']}</h2>
</div>
""", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1f3d2d 0%, #1a2e1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">📈 متوسط التقييم</p>
    <h2 style="color: #4CAF50; margin: 0.5rem 0 0 0;">{stats['avg_score']:.2f}</h2>
</div>
""", unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #3d2d1f 0%, #2e2a1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">🔥 السلسلة</p>
    <h2 style="color: #FF9800; margin: 0.5rem 0 0 0;">{stats['streak']} يوم</h2>
</div>
""", unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #3d1f2d 0%, #2e1a1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">📅 أيام التتبع</p>
    <h2 style="color: #E91E63; margin: 0.5rem 0 0 0;">{stats['days_tracked']}</h2>
</div>
""", unsafe_allow_html=True)

def render_heatmap(logs: list):
    """عرض خريطة الحرارة"""
    
    st.markdown("### 🗓️ خريطة الحرارة (الساعات × أيام الأسبوع)")
    st.markdown("*متوسط الإنتاجية لكل ساعة في كل يوم من أيام الأسبوع*")
    
    df = generate_heatmap_data(logs)
    
    # إنشاء خريطة الحرارة باستخدام Plotly
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns,
        y=df.index,
        colorscale=[
            [0, '#2d2d2d'],      # 0 - رمادي
            [0.25, '#fd7e14'],   # 1 - برتقالي
            [0.5, '#ffc107'],    # 2 - أصفر
            [0.75, '#90EE90'],   # 3 - أخضر فاتح
            [1, '#28a745']       # 4 - أخضر غامق
        ],
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}<br>المتوسط: %{z:.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        xaxis_title="اليوم",
        yaxis_title="الساعة",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fafafa'),
        height=600,
        yaxis=dict(autorange='reversed')
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_trends(logs: list, daily_goal: int):
    """عرض الاتجاهات"""
    
    st.markdown("### 📈 اتجاه الإنتاجية")
    
    df = calculate_trends(logs)
    
    if df.empty:
        st.info("لا توجد بيانات كافية لعرض الاتجاهات")
        return
    
    # إنشاء الرسم البياني
    fig = go.Figure()
    
    # خط النقاط اليومية
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['score'],
        mode='lines+markers',
        name='النقاط اليومية',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.2)'
    ))
    
    # خط الهدف اليومي
    fig.add_hline(
        y=daily_goal,
        line_dash="dash",
        line_color="#FF9800",
        annotation_text=f"الهدف: {daily_goal}",
        annotation_position="right"
    )
    
    fig.update_layout(
        xaxis_title="التاريخ",
        yaxis_title="النقاط",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fafafa'),
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # عدد الفترات المسجلة يومياً
    st.markdown("### ✅ عدد الفترات المسجلة يومياً")
    
    fig2 = px.bar(
        df,
        x='date',
        y='count',
        color='count',
        color_continuous_scale=['#fd7e14', '#ffc107', '#90EE90', '#28a745'],
        labels={'date': 'التاريخ', 'count': 'عدد الفترات'}
    )
    
    fig2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fafafa'),
        height=300,
        showlegend=False
    )
    
    st.plotly_chart(fig2, use_container_width=True)

def render_category_analysis(logs: list):
    """عرض تحليل الفئات"""
    
    st.markdown("### 📊 تحليل الفئات")
    
    df = get_category_breakdown(logs)
    
    if df.empty:
        st.info("لا توجد بيانات كافية")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # رسم دائري
        fig = px.pie(
            df,
            values='total_score',
            names='category',
            title='توزيع النقاط حسب الفئات',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#fafafa'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # رسم بياني شريطي
        fig2 = px.bar(
            df,
            x='category',
            y='avg_score',
            title='متوسط التقييم حسب الفئات',
            color='avg_score',
            color_continuous_scale=['#fd7e14', '#ffc107', '#90EE90', '#28a745'],
            labels={'category': 'الفئة', 'avg_score': 'متوسط التقييم'}
        )
        
        fig2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#fafafa'),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # جدول التفاصيل
    st.markdown("#### 📋 تفاصيل الفئات")
    
    display_df = df.copy()
    display_df.columns = ['الفئة', 'إجمالي النقاط', 'عدد السجلات', 'متوسط التقييم']
    display_df['متوسط التقييم'] = display_df['متوسط التقييم'].round(2)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_detailed_stats(logs: list, stats: dict):
    """عرض الإحصائيات التفصيلية"""
    
    st.markdown("### 📋 إحصائيات تفصيلية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⏰ أفضل ساعة للإنتاجية")
        best_hour, best_hour_avg = stats['best_hour']
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <h1 style="color: #4CAF50; margin: 0;">{best_hour:02d}:00</h1>
    <p style="color: #888; margin: 0.5rem 0 0 0;">متوسط التقييم: {best_hour_avg:.2f}</p>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 📅 أفضل يوم في الأسبوع")
        best_day, best_day_avg = stats['best_day']
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <h1 style="color: #9C27B0; margin: 0;">{best_day}</h1>
    <p style="color: #888; margin: 0.5rem 0 0 0;">متوسط التقييم: {best_day_avg:.2f}</p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # توزيع التقييمات
    st.markdown("#### 📊 توزيع مستويات الإنتاجية")
    
    score_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for log in logs:
        score = log.get("score", 0)
        score_counts[score] = score_counts.get(score, 0) + 1
    
    # عرض البطاقات في صف واحد مع تصميم محسن
    cards_html = '<div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;">'
    
    for score, count in score_counts.items():
        level = PRODUCTIVITY_LEVELS[score]
        percentage = (count / len(logs) * 100) if logs else 0
        
        cards_html += f'''
<div style="
    background: {level['color']}22; 
    border: 2px solid {level['color']}; 
    border-radius: 15px; 
    padding: 1rem 1.5rem; 
    text-align: center;
    min-width: 100px;
    flex: 1;
">
    <div style="font-size: 2rem;">{level['emoji']}</div>
    <div style="color: {level['color']}; font-weight: bold; white-space: nowrap; font-size: 0.9rem;">{level['name']}</div>
    <div style="font-size: 1.5rem; color: #fafafa;">{count}</div>
    <div style="color: #888; font-size: 0.9rem;">{percentage:.1f}%</div>
</div>
'''
    
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)


# =============================================
# الميزات الجديدة - New Features
# =============================================

def render_period_comparison(user_id: str, current_start: date, current_end: date):
    """عرض مقارنة بين الفترة الحالية والسابقة"""
    
    st.markdown("### 🔄 مقارنة الفترات")
    st.markdown("*مقارنة الفترة الحالية بالفترة السابقة المماثلة*")
    
    # حساب الفترة السابقة
    period_days = (current_end - current_start).days
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=period_days)
    
    # جلب البيانات
    current_logs = get_logs_by_range(user_id, current_start, current_end)
    previous_logs = get_logs_by_range(user_id, previous_start, previous_end)
    
    comparison = compare_periods(current_logs, previous_logs)
    
    if comparison["previous_entries"] == 0 and comparison["current_entries"] == 0:
        st.info("لا توجد بيانات كافية للمقارنة. سجّل المزيد من الأنشطة!")
        return
    
    # بطاقات المقارنة
    col1, col2, col3 = st.columns(3)
    
    with col1:
        arrow = "📈" if comparison["score_change"] >= 0 else "📉"
        change_color = "#4CAF50" if comparison["score_change"] >= 0 else "#f44336"
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">📊 إجمالي النقاط</p>
    <h2 style="color: #4CAF50; margin: 0.5rem 0;">{comparison['current_score']}</h2>
    <p style="color: {change_color}; margin: 0; font-size: 1.1rem;">
        {arrow} {comparison['score_change_pct']:+.1f}%
    </p>
    <p style="color: #666; margin: 0.3rem 0 0 0; font-size: 0.8rem;">الفترة السابقة: {comparison['previous_score']}</p>
</div>
""", unsafe_allow_html=True)
    
    with col2:
        avg_arrow = "📈" if comparison["avg_change_pct"] >= 0 else "📉"
        avg_color = "#4CAF50" if comparison["avg_change_pct"] >= 0 else "#f44336"
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #2d1f3d 0%, #1a1a2e 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">📈 متوسط التقييم</p>
    <h2 style="color: #9C27B0; margin: 0.5rem 0;">{comparison['current_avg']:.2f}</h2>
    <p style="color: {avg_color}; margin: 0; font-size: 1.1rem;">
        {avg_arrow} {comparison['avg_change_pct']:+.1f}%
    </p>
    <p style="color: #666; margin: 0.3rem 0 0 0; font-size: 0.8rem;">الفترة السابقة: {comparison['previous_avg']:.2f}</p>
</div>
""", unsafe_allow_html=True)
    
    with col3:
        entries_change = comparison["current_entries"] - comparison["previous_entries"]
        entries_color = "#4CAF50" if entries_change >= 0 else "#f44336"
        entries_arrow = "📈" if entries_change >= 0 else "📉"
        st.markdown(f"""
<div style="background: linear-gradient(135deg, #1f3d2d 0%, #1a2e1a 100%); padding: 1.5rem; border-radius: 15px; text-align: center;">
    <p style="color: #888; margin: 0;">✅ عدد السجلات</p>
    <h2 style="color: #4CAF50; margin: 0.5rem 0;">{comparison['current_entries']}</h2>
    <p style="color: {entries_color}; margin: 0; font-size: 1.1rem;">
        {entries_arrow} {entries_change:+d} سجل
    </p>
    <p style="color: #666; margin: 0.3rem 0 0 0; font-size: 0.8rem;">الفترة السابقة: {comparison['previous_entries']}</p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # رسم بياني للمقارنة
    if current_logs or previous_logs:
        current_trends = calculate_trends(current_logs)
        previous_trends = calculate_trends(previous_logs)
        
        fig = go.Figure()
        
        if not current_trends.empty:
            fig.add_trace(go.Scatter(
                x=list(range(len(current_trends))),
                y=current_trends['score'],
                mode='lines+markers',
                name='الفترة الحالية',
                line=dict(color='#4CAF50', width=3),
                marker=dict(size=8)
            ))
        
        if not previous_trends.empty:
            fig.add_trace(go.Scatter(
                x=list(range(len(previous_trends))),
                y=previous_trends['score'],
                mode='lines+markers',
                name='الفترة السابقة',
                line=dict(color='#FF9800', width=2, dash='dash'),
                marker=dict(size=6)
            ))
        
        fig.update_layout(
            title="مقارنة النقاط اليومية",
            xaxis_title="اليوم",
            yaxis_title="النقاط",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#fafafa'),
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def render_time_patterns(logs: list):
    """عرض تحليل أنماط الوقت"""
    
    st.markdown("### ⏰ أنماط الوقت")
    st.markdown("*تحليل أدائك حسب أيام الأسبوع وساعات اليوم*")
    
    if not logs:
        st.info("لا توجد بيانات كافية")
        return
    
    patterns = get_time_patterns(logs)
    
    col1, col2 = st.columns(2)
    
    # 1. رادار الأيام
    with col1:
        st.markdown("#### 📅 أداؤك حسب أيام الأسبوع")
        
        if patterns["days_ranking"]:
            days = [d["day"] for d in patterns["days_ranking"]]
            avgs = [d["avg"] for d in patterns["days_ranking"]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=avgs + [avgs[0]],
                theta=days + [days[0]],
                fill='toself',
                fillcolor='rgba(76, 175, 80, 0.2)',
                line=dict(color='#4CAF50', width=2),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 4], color='#888'),
                    bgcolor='rgba(0,0,0,0)',
                    angularaxis=dict(color='#fafafa')
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa'),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ترتيب الأيام
            for i, d in enumerate(patterns["days_ranking"]):
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
                bar_width = (d["avg"] / 4) * 100
                bar_color = "#4CAF50" if d["avg"] >= 3 else "#ffc107" if d["avg"] >= 2 else "#fd7e14"
                st.markdown(f"""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 5px;">
    <span style="font-size: 1.2rem; min-width: 30px;">{medal}</span>
    <span style="color: #fafafa; min-width: 70px;">{d['day']}</span>
    <div style="flex: 1; background: #333; border-radius: 5px; height: 20px; overflow: hidden;">
        <div style="background: {bar_color}; height: 100%; width: {bar_width}%; border-radius: 5px;"></div>
    </div>
    <span style="color: {bar_color}; font-weight: bold; min-width: 40px;">{d['avg']:.1f}</span>
</div>
""", unsafe_allow_html=True)
    
    # 2. ساعات اليوم
    with col2:
        st.markdown("#### ⏰ أداؤك حسب ساعات اليوم")
        
        if patterns["hours_ranking"]:
            hours_sorted = sorted(patterns["hours_ranking"], key=lambda x: x["hour"])
            hours_labels = [h["label"] for h in hours_sorted]
            hours_avgs = [h["avg"] for h in hours_sorted]
            
            # ألوان متدرجة حسب الأداء
            colors = []
            for avg in hours_avgs:
                if avg >= 3:
                    colors.append("#4CAF50")
                elif avg >= 2:
                    colors.append("#ffc107")
                elif avg >= 1:
                    colors.append("#fd7e14")
                else:
                    colors.append("#6c757d")
            
            fig = go.Figure(data=[go.Bar(
                x=hours_labels,
                y=hours_avgs,
                marker_color=colors,
                hovertemplate="<b>%{x}</b><br>المتوسط: %{y:.2f}<extra></extra>"
            )])
            
            fig.update_layout(
                xaxis_title="الساعة",
                yaxis_title="متوسط التقييم",
                yaxis=dict(range=[0, 4]),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#fafafa'),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # فترات الذروة والهبوط
            st.markdown("##### 🔥 فترات الذروة")
            for ph in patterns["peak_hours"][:3]:
                st.markdown(f"""
                <div style="background: #4CAF5022; border-right: 4px solid #4CAF50; padding: 0.5rem 1rem; border-radius: 8px; margin-bottom: 5px;">
                    <span style="color: #4CAF50; font-weight: bold;">{ph['label']}</span>
                    <span style="color: #888; margin-right: 10px;">المتوسط: {ph['avg']:.1f}/4</span>
                    <span style="color: #666;">({ph['count']} تسجيل)</span>
                </div>
                """, unsafe_allow_html=True)
            
            if patterns["low_hours"]:
                st.markdown("##### 📉 فترات تحتاج تحسين")
                for lh in patterns["low_hours"][-3:]:
                    st.markdown(f"""
                    <div style="background: #fd7e1422; border-right: 4px solid #fd7e14; padding: 0.5rem 1rem; border-radius: 8px; margin-bottom: 5px;">
                        <span style="color: #fd7e14; font-weight: bold;">{lh['label']}</span>
                        <span style="color: #888; margin-right: 10px;">المتوسط: {lh['avg']:.1f}/4</span>
                        <span style="color: #666;">({lh['count']} تسجيل)</span>
                    </div>
                    """, unsafe_allow_html=True)


def render_recommendations(logs: list, daily_goal: int):
    """عرض التوصيات الذكية"""
    
    recommendations = generate_recommendations(logs, daily_goal)
    
    if not recommendations:
        return
    
    st.markdown("### 💡 توصيات ذكية")
    
    cols = st.columns(min(len(recommendations), 3))
    
    for i, rec in enumerate(recommendations[:3]):
        with cols[i % 3]:
            # ألوان حسب النوع
            if rec["type"] == "success":
                border_color = "#4CAF50"
                bg = "#4CAF5015"
            elif rec["type"] == "warning":
                border_color = "#FF9800"
                bg = "#FF980015"
            else:
                border_color = "#2196F3"
                bg = "#2196F315"
            
            st.markdown(f"""
            <div style="background: {bg}; border: 1px solid {border_color}; border-radius: 15px; padding: 1.5rem; text-align: center; min-height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{rec['icon']}</div>
                <p style="color: {border_color}; font-weight: bold; margin: 0 0 0.5rem 0; font-size: 0.95rem;">{rec['title']}</p>
                <p style="color: #aaa; margin: 0; font-size: 0.85rem;">{rec['text']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # عرض توصيات إضافية
    if len(recommendations) > 3:
        with st.expander("💡 المزيد من التوصيات"):
            for rec in recommendations[3:]:
                border_color = "#4CAF50" if rec["type"] == "success" else "#FF9800" if rec["type"] == "warning" else "#2196F3"
                st.markdown(f"""
                <div style="background: rgba(0,0,0,0.2); border-right: 4px solid {border_color}; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.3rem;">{rec['icon']}</span>
                    <strong style="color: {border_color};">{rec['title']}</strong>
                    <p style="color: #aaa; margin: 0.3rem 0 0 0;">{rec['text']}</p>
                </div>
                """, unsafe_allow_html=True)


def render_period_report(logs: list, daily_goal: int, period_name: str):
    """عرض تقرير شامل للفترة"""
    
    st.markdown("### 📃 تقرير الفترة")
    
    # دليل الرموز والشرح المبسط
    with st.expander("ℹ️ دليل قراءة الرسوم البيانية"):
        st.markdown("""
        - **النقاط (Score)**: مقياس لإنتاجيتك يعتمد على عدد ومدة الجلسات.
        - **الهدف (Goal)**: الخط المتقطع يمثل هدفك اليومي. حاول أن تبقي منحنى النقاط فوقه!
        - **خريطة الحرارة**: الألوان الداكنة تعني نشاطاً مكثفاً في ذلك الوقت.
        - **التقويم**: 🟩 حققت الهدف | 🟥 لم تحقق الهدف | ⬜ عطلة/راحة.
        """)
    
    report = generate_period_report(logs, daily_goal, period_name)
    
    if not report["has_data"]:
        st.info("لا توجد بيانات لإنشاء التقرير")
        return
    
    # العنوان
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #4CAF50; margin: 0;">📃 تقرير {report['period_name']}</h2>
        <p style="color: #888; margin: 0.5rem 0 0 0;">{report['days_tracked']} يوم تتبع | {report['total_entries']} سجل</p>
    </div>
    """, unsafe_allow_html=True)
    
    # الإحصائيات الأساسية
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: #1a2e1a; padding: 1rem; border-radius: 10px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.8rem;">📊 إجمالي النقاط</p>
            <h2 style="color: #4CAF50; margin: 0.3rem 0;">{report['total_score']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: #2e1a2e; padding: 1rem; border-radius: 10px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.8rem;">📈 المتوسط اليومي</p>
            <h2 style="color: #9C27B0; margin: 0.3rem 0;">{report['daily_avg']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: #2e2a1a; padding: 1rem; border-radius: 10px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.8rem;">🏆 أيام الهدف</p>
            <h2 style="color: #FF9800; margin: 0.3rem 0;">{report['full_goal_days']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: #1a2e3d; padding: 1rem; border-radius: 10px; text-align: center;">
            <p style="color: #888; margin: 0; font-size: 0.8rem;">🔥 أطول سلسلة</p>
            <h2 style="color: #2196F3; margin: 0.3rem 0;">{report['longest_streak']} يوم</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # أبرز المعلومات
        st.markdown("#### 🌟 أبرز المعلومات")
        
        if report["best_day"]:
            st.markdown(f"""
            <div style="background: rgba(0,0,0,0.2); border-right: 4px solid #4CAF50; padding: 1rem; border-radius: 8px; margin-bottom: 8px;">
                <strong style="color: #4CAF50;">📅 أفضل يوم:</strong>
                <span style="color: #fafafa;"> {report['best_day']['day']} (متوسط {report['best_day']['avg']:.1f}/4)</span>
            </div>
            """, unsafe_allow_html=True)
        
        if report["peak_hour"]:
            st.markdown(f"""
            <div style="background: rgba(0,0,0,0.2); border-right: 4px solid #2196F3; padding: 1rem; border-radius: 8px; margin-bottom: 8px;">
                <strong style="color: #2196F3;">⏰ أفضل ساعة:</strong>
                <span style="color: #fafafa;"> {report['peak_hour']['label']} (متوسط {report['peak_hour']['avg']:.1f}/4)</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.2); border-right: 4px solid #9C27B0; padding: 1rem; border-radius: 8px; margin-bottom: 8px;">
            <strong style="color: #9C27B0;">📁 الفئة الأكثر:</strong>
            <span style="color: #fafafa;"> {report['top_category']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.2); border-right: 4px solid #FF9800; padding: 1rem; border-radius: 8px; margin-bottom: 8px;">
            <strong style="color: #FF9800;">✨ أداء عالي:</strong>
            <span style="color: #fafafa;"> {report['high_performance_pct']}% من الفترات</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # رسم دائري لتوزيع الدرجات
        st.markdown("#### 📊 توزيع الدرجات")
        
        dist = report["score_distribution"]
        labels = [PRODUCTIVITY_LEVELS[i]["name"] for i in range(5)]
        values = [dist[i] for i in range(5)]
        colors = [PRODUCTIVITY_LEVELS[i]["color"] for i in range(5)]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='percent+label',
            textposition='outside',
            hovertemplate="<b>%{label}</b><br>العدد: %{value}<br>النسبة: %{percent}<extra></extra>"
        )])
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#fafafa'),
            height=350,
            showlegend=False,
            margin=dict(t=10, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_trends_simplified(logs: list, daily_goal: int):
    """عرض مبسط للاتجاهات للوحة القيادة"""
    st.markdown("##### 📈 اتجاه الإنتاجية")
    
    df = calculate_trends(logs)
    if df.empty:
        st.info("لا توجد بيانات")
        return

    # استخدام Plotly لرسم نظيف
    fig = go.Figure()
    
    # المساحة المظللة للأداء
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['score'],
        mode='lines', # خط فقط بدون نقاط لتقليل الضوضاء
        name='النقاط',
        line=dict(color='#4CAF50', width=2),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.1)',
        hovertemplate="<b>%{x}</b><br>النقاط: %{y}<extra></extra>"
    ))
    
    # خط الهدف
    fig.add_hline(
        y=daily_goal,
        line_dash="dot",
        line_color="rgba(255, 152, 0, 0.5)",
        annotation_text="الهدف",
        annotation_position="top right"
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=20),
        xaxis_title="",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fafafa', size=10),
        height=250,
        showlegend=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_goals_progress_simplified(user_id: str, weekly_goal: int, monthly_goal: int, current_logs: list):
    """عرض مبسط للأهداف للوحة القيادة"""
    st.markdown("##### 🎯 الأهداف")
    
    # نحسب التقدم بناءً على الفلاتر الحالية (logs) إذا أردنا
    # لكن الأهداف عادة ما تكون عامة، لذا سنعرض الأهداف العامة (أسبوعي/شهري)
    # ولكن المستخدم قد يكون "فلتر" البيانات، مما يجعل عرض الأهداف مربكاً
    # لذا سنعرض مجموع النقاط "للفلتر الحالي" كنسبة من الهدف اليومي المتراكم؟
    # الأبسط: عرض الأهداف العامة (أسبوع/شهر) دائمًا، بشكل مصغر.
    
    # إعادة استخدام منطق حساب الأهداف (مكرر قليلاً لكن آمن)
    from datetime import date, timedelta
    today = date.today()
    days_since_saturday = (today.weekday() + 2) % 7
    week_start = today - timedelta(days=days_since_saturday)
    month_start = today.replace(day=1)
    
    # نستخدم get_logs_by_range لجلب البيانات "الخام" للأهداف، بغض النظر عن الفلتر
    # لأن الهدف هو "هدفي الأسبوعي" وليس "هدفي الأسبوعي في العمل فقط" (عادة)
    # إلا إذا أراد المستخدم تخصيص أهداف للفئات (feature creep)
    
    week_logs = get_logs_by_range(user_id, week_start, today)
    month_logs = get_logs_by_range(user_id, month_start, today)
    
    week_score = sum(log.get("score", 0) for log in week_logs)
    month_score = sum(log.get("score", 0) for log in month_logs)
    
    week_ids = {l['id'] for l in week_logs}
    month_ids = {l['id'] for l in month_logs}

    week_progress = min((week_score / weekly_goal * 100), 100) if weekly_goal > 0 else 0
    month_progress = min((month_score / monthly_goal * 100), 100) if monthly_goal > 0 else 0

    col1, col2 = st.columns(2)
    
    with col1:
        color = "#4CAF50" if week_progress >= 100 else "#FF9800"
        st.markdown(f"""
<div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px;">
    <div style="font-size: 0.8rem; color: #aaa;">الأسبوع</div>
    <div style="font-weight: bold; font-size: 1.2rem; color: {color};">{week_progress:.0f}%</div>
    <div style="font-size: 0.7rem; color: #666;">{week_score}/{weekly_goal}</div>
</div>
""", unsafe_allow_html=True)
        
    with col2:
        color = "#4CAF50" if month_progress >= 100 else "#2196F3"
        st.markdown(f"""
<div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 10px;">
    <div style="font-size: 0.8rem; color: #aaa;">الشهر</div>
    <div style="font-weight: bold; font-size: 1.2rem; color: {color};">{month_progress:.0f}%</div>
    <div style="font-size: 0.7rem; color: #666;">{month_score}/{monthly_goal}</div>
</div>
""", unsafe_allow_html=True)

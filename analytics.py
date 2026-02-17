"""
التحليلات والإحصائيات
Analytics and Statistics
"""

from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
import pandas as pd
from config import PRODUCTIVITY_LEVELS, DAYS_OF_WEEK_AR

def calculate_daily_score(logs: List[Dict]) -> int:
    """حساب النقاط اليومية"""
    return sum(log.get("score", 0) for log in logs)

def calculate_max_daily_score(slots_logged: int = 48) -> int:
    """حساب أقصى نقاط ممكنة"""
    return slots_logged * 4

def calculate_progress_percentage(current: int, goal: int) -> float:
    """حساب نسبة التقدم"""
    if goal <= 0:
        return 0
    return min((current / goal) * 100, 100)

def calculate_streak(logs_by_date: Dict[date, int], daily_goal: int) -> int:
    """
    حساب سلسلة الأيام المتتالية التي تحقق فيها الهدف اليومي
    
    Args:
        logs_by_date: قاموس {التاريخ: مجموع النقاط}
        daily_goal: الهدف اليومي
    
    Returns:
        عدد الأيام المتتالية
    """
    today = date.today()
    streak = 0
    current_date = today
    
    # التحقق من اليوم الأول (اليوم أو الأمس)
    if current_date not in logs_by_date or logs_by_date[current_date] < daily_goal:
        # إذا لم يتحقق الهدف اليوم، نبدأ من الأمس
        current_date = today - timedelta(days=1)
    
    # حساب السلسلة
    while current_date in logs_by_date:
        if logs_by_date[current_date] >= daily_goal:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak

def get_logs_summary_by_date(logs: List[Dict]) -> Dict[date, int]:
    """تجميع النقاط حسب التاريخ"""
    summary = {}
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        
        if log_date not in summary:
            summary[log_date] = 0
        summary[log_date] += log.get("score", 0)
    
    return summary

def generate_heatmap_data(logs: List[Dict]) -> pd.DataFrame:
    """
    تجهيز بيانات خريطة الحرارة (الساعات × أيام الأسبوع)
    
    Returns:
        DataFrame مع الساعات كصفوف وأيام الأسبوع كأعمدة
    """
    # إنشاء مصفوفة فارغة (24 ساعة × 7 أيام)
    data = [[0 for _ in range(7)] for _ in range(24)]
    counts = [[0 for _ in range(7)] for _ in range(24)]
    
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        
        time_slot = log.get("time_slot", 0)
        hour = time_slot // 2
        day_of_week = log_date.weekday()  # 0 = Monday
        
        data[hour][day_of_week] += log.get("score", 0)
        counts[hour][day_of_week] += 1
    
    # حساب المتوسط
    for h in range(24):
        for d in range(7):
            if counts[h][d] > 0:
                data[h][d] = data[h][d] / counts[h][d]
    
    df = pd.DataFrame(
        data,
        index=[f"{h:02d}:00" for h in range(24)],
        columns=DAYS_OF_WEEK_AR
    )
    
    return df

def generate_daily_heatmap(logs: List[Dict], target_date: date) -> List[Dict]:
    """
    تجهيز بيانات خريطة حرارة يوم واحد (48 فترة)
    """
    # إنشاء قائمة بـ 48 فترة
    slots_data = []
    logs_dict = {log.get("time_slot"): log for log in logs}
    
    for slot in range(48):
        log = logs_dict.get(slot)
        slots_data.append({
            "slot": slot,
            "hour": slot // 2,
            "minute": (slot % 2) * 30,
            "score": log.get("score", 0) if log else None,
            "category": log.get("category", "") if log else "",
            "logged": log is not None
        })
    
    return slots_data

def calculate_trends(logs: List[Dict], period: str = "week") -> pd.DataFrame:
    """
    حساب الاتجاهات الأسبوعية أو الشهرية
    
    Args:
        logs: قائمة السجلات
        period: "week" أو "month"
    
    Returns:
        DataFrame مع التواريخ والنقاط
    """
    if not logs:
        return pd.DataFrame(columns=["date", "score", "count"])
    
    # تجميع حسب التاريخ
    daily_data = {}
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        
        if log_date not in daily_data:
            daily_data[log_date] = {"score": 0, "count": 0}
        
        daily_data[log_date]["score"] += log.get("score", 0)
        daily_data[log_date]["count"] += 1
    
    # تحويل إلى DataFrame
    df = pd.DataFrame([
        {"date": d, "score": v["score"], "count": v["count"]}
        for d, v in sorted(daily_data.items())
    ])
    
    return df

def get_category_breakdown(logs: List[Dict]) -> pd.DataFrame:
    """تحليل حسب الفئات"""
    if not logs:
        return pd.DataFrame(columns=["category", "total_score", "count", "avg_score"])
    
    category_data = {}
    for log in logs:
        cat = log.get("category", "غير محدد")
        if cat not in category_data:
            category_data[cat] = {"total": 0, "count": 0}
        
        category_data[cat]["total"] += log.get("score", 0)
        category_data[cat]["count"] += 1
    
    df = pd.DataFrame([
        {
            "category": cat,
            "total_score": v["total"],
            "count": v["count"],
            "avg_score": v["total"] / v["count"] if v["count"] > 0 else 0
        }
        for cat, v in category_data.items()
    ])
    
    return df.sort_values("total_score", ascending=False)

def get_best_hour(logs: List[Dict]) -> Tuple[int, float]:
    """الحصول على أفضل ساعة في اليوم"""
    if not logs:
        return (0, 0)
    
    hourly_data = {}
    for log in logs:
        hour = log.get("time_slot", 0) // 2
        if hour not in hourly_data:
            hourly_data[hour] = {"total": 0, "count": 0}
        
        hourly_data[hour]["total"] += log.get("score", 0)
        hourly_data[hour]["count"] += 1
    
    # حساب المتوسط لكل ساعة
    hour_avgs = {
        h: v["total"] / v["count"] if v["count"] > 0 else 0
        for h, v in hourly_data.items()
    }
    
    if not hour_avgs:
        return (0, 0)
    
    best_hour = max(hour_avgs, key=hour_avgs.get)
    return (best_hour, hour_avgs[best_hour])

def get_best_day(logs: List[Dict]) -> Tuple[str, float]:
    """الحصول على أفضل يوم في الأسبوع"""
    if not logs:
        return (DAYS_OF_WEEK_AR[0], 0)
    
    daily_data = {}
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        
        day = log_date.weekday()
        if day not in daily_data:
            daily_data[day] = {"total": 0, "count": 0}
        
        daily_data[day]["total"] += log.get("score", 0)
        daily_data[day]["count"] += 1
    
    # حساب المتوسط لكل يوم
    day_avgs = {
        d: v["total"] / v["count"] if v["count"] > 0 else 0
        for d, v in daily_data.items()
    }
    
    if not day_avgs:
        return (DAYS_OF_WEEK_AR[0], 0)
    
    best_day = max(day_avgs, key=day_avgs.get)
    return (DAYS_OF_WEEK_AR[best_day], day_avgs[best_day])

def get_statistics_summary(logs: List[Dict], daily_goal: int) -> Dict:
    """الحصول على ملخص الإحصائيات"""
    if not logs:
        return {
            "total_score": 0,
            "total_entries": 0,
            "avg_score": 0,
            "best_hour": (0, 0),
            "best_day": (DAYS_OF_WEEK_AR[0], 0),
            "streak": 0,
            "days_tracked": 0
        }
    
    total_score = sum(log.get("score", 0) for log in logs)
    total_entries = len(logs)
    
    # عدد الأيام المسجلة
    unique_dates = set()
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        unique_dates.add(log_date)
    
    # حساب السلسلة
    logs_by_date = get_logs_summary_by_date(logs)
    streak = calculate_streak(logs_by_date, daily_goal)
    
    return {
        "total_score": total_score,
        "total_entries": total_entries,
        "avg_score": total_score / total_entries if total_entries > 0 else 0,
        "best_hour": get_best_hour(logs),
        "best_day": get_best_day(logs),
        "streak": streak,
        "days_tracked": len(unique_dates)
    }


# =============================================
# تحليلات متقدمة - Advanced Analytics
# =============================================

def compare_periods(current_logs: List[Dict], previous_logs: List[Dict]) -> Dict:
    """
    مقارنة فترتين زمنيتين
    مثال: الأسبوع الحالي vs الأسبوع الماضي
    """
    current_score = sum(log.get("score", 0) for log in current_logs)
    previous_score = sum(log.get("score", 0) for log in previous_logs)
    
    current_entries = len(current_logs)
    previous_entries = len(previous_logs)
    
    current_avg = current_score / current_entries if current_entries > 0 else 0
    previous_avg = previous_score / previous_entries if previous_entries > 0 else 0
    
    # نسبة التغيير
    if previous_score > 0:
        score_change_pct = ((current_score - previous_score) / previous_score) * 100
    else:
        score_change_pct = 100 if current_score > 0 else 0
    
    if previous_avg > 0:
        avg_change_pct = ((current_avg - previous_avg) / previous_avg) * 100
    else:
        avg_change_pct = 100 if current_avg > 0 else 0
    
    return {
        "current_score": current_score,
        "previous_score": previous_score,
        "score_change": current_score - previous_score,
        "score_change_pct": score_change_pct,
        "current_avg": current_avg,
        "previous_avg": previous_avg,
        "avg_change_pct": avg_change_pct,
        "current_entries": current_entries,
        "previous_entries": previous_entries,
    }


def calculate_longest_streak(logs: List[Dict], daily_goal: int) -> int:
    """حساب أطول سلسلة متتالية على الإطلاق"""
    logs_by_date = get_logs_summary_by_date(logs)
    if not logs_by_date:
        return 0
    
    sorted_dates = sorted(logs_by_date.keys())
    longest = 0
    current = 0
    
    for i, d in enumerate(sorted_dates):
        if logs_by_date[d] >= daily_goal:
            if i == 0 or (d - sorted_dates[i-1]).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)
        else:
            current = 0
    
    return longest


def count_full_goal_days(logs: List[Dict], daily_goal: int) -> int:
    """عدد الأيام التي تحقق فيها الهدف الكامل"""
    logs_by_date = get_logs_summary_by_date(logs)
    return sum(1 for score in logs_by_date.values() if score >= daily_goal)


def get_score_distribution(logs: List[Dict]) -> Dict[int, int]:
    """توزيع الدرجات (كم مرة حصل المستخدم على كل درجة)"""
    dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for log in logs:
        score = log.get("score", 0)
        if score in dist:
            dist[score] += 1
    return dist


def get_time_patterns(logs: List[Dict]) -> Dict:
    """
    تحليل الأنماط الزمنية المتقدمة
    - ترتيب أيام الأسبوع من الأفضل للأسوأ
    - ترتيب ساعات اليوم من الأفضل للأسوأ
    - فترات الذروة والهبوط
    """
    if not logs:
        return {"days_ranking": [], "hours_ranking": [], "peak_hours": [], "low_hours": []}
    
    # تحليل الأيام
    daily_data = {}
    for log in logs:
        log_date = log.get("log_date")
        if isinstance(log_date, str):
            log_date = datetime.strptime(log_date, "%Y-%m-%d").date()
        day = log_date.weekday()
        if day not in daily_data:
            daily_data[day] = {"total": 0, "count": 0}
        daily_data[day]["total"] += log.get("score", 0)
        daily_data[day]["count"] += 1
    
    days_ranking = []
    for d in range(7):
        if d in daily_data and daily_data[d]["count"] > 0:
            avg = daily_data[d]["total"] / daily_data[d]["count"]
            days_ranking.append({"day": DAYS_OF_WEEK_AR[d], "avg": round(avg, 2), "count": daily_data[d]["count"]})
    days_ranking.sort(key=lambda x: x["avg"], reverse=True)
    
    # تحليل الساعات
    hourly_data = {}
    for log in logs:
        hour = log.get("time_slot", 0) // 2
        if hour not in hourly_data:
            hourly_data[hour] = {"total": 0, "count": 0}
        hourly_data[hour]["total"] += log.get("score", 0)
        hourly_data[hour]["count"] += 1
    
    hours_ranking = []
    for h, v in hourly_data.items():
        if v["count"] > 0:
            avg = v["total"] / v["count"]
            hours_ranking.append({"hour": h, "label": f"{h:02d}:00", "avg": round(avg, 2), "count": v["count"]})
    hours_ranking.sort(key=lambda x: x["avg"], reverse=True)
    
    peak_hours = hours_ranking[:3] if len(hours_ranking) >= 3 else hours_ranking
    low_hours = hours_ranking[-3:] if len(hours_ranking) >= 3 else []
    
    return {
        "days_ranking": days_ranking,
        "hours_ranking": hours_ranking,
        "peak_hours": peak_hours,
        "low_hours": low_hours
    }


def generate_recommendations(logs: List[Dict], daily_goal: int) -> List[Dict]:
    """
    توليد توصيات ذكية بناءً على البيانات
    """
    recommendations = []
    
    if not logs:
        recommendations.append({
            "icon": "🚀",
            "title": "ابدأ رحلتك!",
            "text": "سجّل أول نشاط لك اليوم وابدأ بتتبع إنتاجيتك.",
            "type": "info"
        })
        return recommendations
    
    logs_by_date = get_logs_summary_by_date(logs)
    patterns = get_time_patterns(logs)
    score_dist = get_score_distribution(logs)
    total_entries = len(logs)
    
    # 1. تقدم نحو الهدف
    today = date.today()
    today_score = logs_by_date.get(today, 0)
    if today_score > 0:
        progress = (today_score / daily_goal) * 100 if daily_goal > 0 else 0
        if progress >= 100:
            recommendations.append({
                "icon": "🏆",
                "title": "أحسنت! حققت هدفك اليوم!",
                "text": f"حصلت على {today_score} من {daily_goal} نقطة. استمر هكذا!",
                "type": "success"
            })
        elif progress >= 70:
            recommendations.append({
                "icon": "💪",
                "title": f"أنت قريب! {progress:.0f}% من هدفك اليومي",
                "text": f"تحتاج {daily_goal - today_score} نقطة إضافية فقط.",
                "type": "warning"
            })
    
    # 2. أفضل ساعات
    if patterns["peak_hours"]:
        best = patterns["peak_hours"][0]
        recommendations.append({
            "icon": "⏰",
            "title": f"أفضل وقت لك: {best['label']}",
            "text": f"متوسط أدائك في هذه الساعة {best['avg']:.1f}/4. حاول جدولة المهام المهمة هنا.",
            "type": "info"
        })
    
    # 3. فترات ضعيفة
    if patterns["low_hours"]:
        worst = patterns["low_hours"][-1]
        if worst["avg"] < 2:
            recommendations.append({
                "icon": "📉",
                "title": f"فترة تحتاج تحسين: {worst['label']}",
                "text": f"متوسط أدائك {worst['avg']:.1f}/4. جرّب استراحة قصيرة أو تغيير النشاط.",
                "type": "warning"
            })
    
    # 4. أفضل يوم
    if patterns["days_ranking"]:
        best_day = patterns["days_ranking"][0]
        worst_day = patterns["days_ranking"][-1]
        if len(patterns["days_ranking"]) > 1 and best_day["avg"] > worst_day["avg"]:
            recommendations.append({
                "icon": "📅",
                "title": f"يومك المفضل: {best_day['day']}",
                "text": f"أداؤك في {best_day['day']} ({best_day['avg']:.1f}) أعلى من {worst_day['day']} ({worst_day['avg']:.1f}). طبّق نفس الروتين!",
                "type": "info"
            })
    
    # 5. توزيع الدرجات
    if total_entries > 0:
        high_pct = ((score_dist.get(3, 0) + score_dist.get(4, 0)) / total_entries) * 100
        if high_pct >= 60:
            recommendations.append({
                "icon": "🌟",
                "title": f"{high_pct:.0f}% من فتراتك عالية الإنتاجية!",
                "text": "أنت تحقق أداءً ممتازاً. حافظ على هذا المستوى.",
                "type": "success"
            })
        elif high_pct < 30:
            recommendations.append({
                "icon": "💡",
                "title": "نصيحة لزيادة الإنتاجية",
                "text": "جرّب تقنية Pomodoro: 25 دقيقة عمل ثم 5 دقائق راحة.",
                "type": "info"
            })
    
    return recommendations


def generate_period_report(logs: List[Dict], daily_goal: int, period_name: str) -> Dict:
    """
    توليد تقرير شامل لفترة معينة
    """
    if not logs:
        return {"has_data": False}
    
    logs_by_date = get_logs_summary_by_date(logs)
    total_score = sum(log.get("score", 0) for log in logs)
    total_entries = len(logs)
    days_tracked = len(logs_by_date)
    daily_avg = total_score / days_tracked if days_tracked > 0 else 0
    full_days = count_full_goal_days(logs, daily_goal)
    longest = calculate_longest_streak(logs, daily_goal)
    patterns = get_time_patterns(logs)
    score_dist = get_score_distribution(logs)
    
    # حساب الفئة الأكثر استخداماً
    cat_data = {}
    for log in logs:
        cat = log.get("category", "غير محدد")
        cat_data[cat] = cat_data.get(cat, 0) + 1
    top_category = max(cat_data, key=cat_data.get) if cat_data else "غير محدد"
    
    return {
        "has_data": True,
        "period_name": period_name,
        "total_score": total_score,
        "total_entries": total_entries,
        "days_tracked": days_tracked,
        "daily_avg": round(daily_avg, 1),
        "full_goal_days": full_days,
        "longest_streak": longest,
        "best_day": patterns["days_ranking"][0] if patterns["days_ranking"] else None,
        "peak_hour": patterns["peak_hours"][0] if patterns["peak_hours"] else None,
        "top_category": top_category,
        "score_distribution": score_dist,
        "high_performance_pct": round(
            ((score_dist.get(3, 0) + score_dist.get(4, 0)) / total_entries * 100) if total_entries > 0 else 0, 1
        )
    }

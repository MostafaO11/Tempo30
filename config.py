"""
إعدادات التطبيق والثوابت
Application Configuration and Constants
"""

import os
import json
from datetime import datetime
from pathlib import Path

# تحميل متغيرات البيئة
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# إعدادات Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# وضع التخزين المحلي (للتطوير بدون Supabase)
USE_LOCAL_STORAGE = not SUPABASE_URL or not SUPABASE_KEY
LOCAL_DATA_DIR = Path(__file__).parent / "local_data"

def get_supabase_client():
    """إنشاء عميل Supabase"""
    if USE_LOCAL_STORAGE:
        return None
    try:
        from supabase import create_client, Client
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except ImportError:
        return None

# =============================================
# الثوابت - Constants
# =============================================

# عدد الفترات الزمنية في اليوم (كل 30 دقيقة)
TOTAL_TIME_SLOTS = 48

# مستويات الإنتاجية مع الألوان
PRODUCTIVITY_LEVELS = {
    0: {
        "name": "لا إنتاجية",
        "name_en": "No Productivity",
        "color": "#6c757d",
        "bg_color": "#2d2d2d",
        "emoji": "😴"
    },
    1: {
        "name": "منخفضة",
        "name_en": "Low",
        "color": "#fd7e14",
        "bg_color": "#3d2a1a",
        "emoji": "😐"
    },
    2: {
        "name": "متوسطة",
        "name_en": "Moderate",
        "color": "#ffc107",
        "bg_color": "#3d3a1a",
        "emoji": "🙂"
    },
    3: {
        "name": "عالية",
        "name_en": "High",
        "color": "#90EE90",
        "bg_color": "#1a3d1a",
        "emoji": "😊"
    },
    4: {
        "name": "ذروة الأداء",
        "name_en": "Peak Performance",
        "color": "#28a745",
        "bg_color": "#0d3d0d",
        "emoji": "🔥"
    }
}

# الفئات الافتراضية
DEFAULT_CATEGORIES = [
    {"name": "Work", "name_ar": "العمل", "color": "#2196F3", "icon": "💼"},
    {"name": "Study", "name_ar": "الدراسة", "color": "#9C27B0", "icon": "📚"},
    {"name": "Health", "name_ar": "الصحة", "color": "#4CAF50", "icon": "🏃"},
    {"name": "Finance", "name_ar": "المالية", "color": "#FF9800", "icon": "💰"},
    {"name": "Leisure", "name_ar": "الترفيه", "color": "#E91E63", "icon": "🎮"},
    {"name": "Personal", "name_ar": "شخصي", "color": "#00BCD4", "icon": "🏠"},
    {"name": "Social", "name_ar": "اجتماعي", "color": "#FFEB3B", "icon": "👥"},
]

# الأهداف الافتراضية
DEFAULT_GOALS = {
    "daily": 100,
    "weekly": 500,
    "monthly": 2000
}

# أيام الأسبوع بالعربية
DAYS_OF_WEEK_AR = [
    "الإثنين",
    "الثلاثاء",
    "الأربعاء",
    "الخميس",
    "الجمعة",
    "السبت",
    "الأحد"
]

# أشهر السنة بالعربية
MONTHS_AR = [
    "يناير", "فبراير", "مارس", "أبريل",
    "مايو", "يونيو", "يوليو", "أغسطس",
    "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

def get_time_slot_label(slot: int) -> str:
    """
    تحويل رقم الفترة الزمنية إلى نص مقروء
    مثال: slot 0 -> "00:00 - 00:30"
    """
    start_hour = slot // 2
    start_minute = (slot % 2) * 30
    end_hour = start_hour if start_minute == 0 else start_hour + 1 if start_minute == 30 else start_hour
    end_minute = 30 if start_minute == 0 else 0
    
    if start_minute == 30:
        end_hour = start_hour + 1
        end_minute = 0
    else:
        end_minute = 30
    
    return f"{start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}"

def get_current_time_slot() -> int:
    """الحصول على رقم الفترة الزمنية الحالية"""
    now = datetime.now()
    return (now.hour * 2) + (1 if now.minute >= 30 else 0)

def get_all_time_slots() -> list:
    """الحصول على قائمة بجميع الفترات الزمنية"""
    return [(i, get_time_slot_label(i)) for i in range(TOTAL_TIME_SLOTS)]

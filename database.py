"""
عمليات قاعدة البيانات - الوضع المحلي
Database Operations - Local Mode
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict
import json
from pathlib import Path
import streamlit as st
from config import LOCAL_DATA_DIR, DEFAULT_CATEGORIES

def _get_logs_file(user_id: str):
    """الحصول على مسار ملف السجلات"""
    user_dir = LOCAL_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "productivity_logs.json"

def _get_profile_file(user_id: str):
    """الحصول على مسار ملف الملف الشخصي"""
    user_dir = LOCAL_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "profile.json"

def _get_categories_file(user_id: str):
    """الحصول على مسار ملف الفئات"""
    user_dir = LOCAL_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "categories.json"

def _get_hidden_defaults_file(user_id: str):
    """الحصول على مسار ملف الفئات الافتراضية المخفية"""
    user_dir = LOCAL_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "hidden_defaults.json"

def _load_json(file_path: Path, default=None):
    """تحميل ملف JSON"""
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else []

def _save_json(file_path: Path, data):
    """حفظ ملف JSON"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# =============================================
# عمليات سجلات الإنتاجية
# =============================================

def log_productivity(
    user_id: str,
    log_date: date,
    time_slot: int,
    score: int,
    category: str,
    notes: str = None
) -> dict:
    """تسجيل الإنتاجية"""
    try:
        logs_file = _get_logs_file(user_id)
        logs = _load_json(logs_file, [])
        
        # البحث عن سجل موجود
        existing_idx = None
        for i, log in enumerate(logs):
            if log.get("log_date") == str(log_date) and log.get("time_slot") == time_slot:
                existing_idx = i
                break
        
        log_data = {
            "id": f"{log_date}_{time_slot}_{datetime.now().timestamp()}",
            "user_id": user_id,
            "log_date": str(log_date),
            "time_slot": time_slot,
            "score": score,
            "category": category,
            "notes": notes,
            "updated_at": datetime.now().isoformat()
        }
        
        if existing_idx is not None:
            log_data["id"] = logs[existing_idx]["id"]
            logs[existing_idx] = log_data
        else:
            logs.append(log_data)
        
        _save_json(logs_file, logs)
        
        return {
            "status": "success",
            "message": "تم تسجيل الإنتاجية بنجاح!",
            "data": log_data
        }
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def get_logs_by_date(user_id: str, log_date: date) -> List[Dict]:
    """الحصول على سجلات يوم معين"""
    try:
        logs_file = _get_logs_file(user_id)
        logs = _load_json(logs_file, [])
        
        filtered = [l for l in logs if l.get("log_date") == str(log_date)]
        return sorted(filtered, key=lambda x: x.get("time_slot", 0))
        
    except Exception as e:
        return []

def get_logs_by_range(user_id: str, start_date: date, end_date: date) -> List[Dict]:
    """الحصول على سجلات فترة زمنية"""
    try:
        logs_file = _get_logs_file(user_id)
        logs = _load_json(logs_file, [])
        
        filtered = []
        for log in logs:
            log_date_str = log.get("log_date")
            if log_date_str:
                log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()
                if start_date <= log_date <= end_date:
                    filtered.append(log)
        
        return sorted(filtered, key=lambda x: (x.get("log_date"), x.get("time_slot", 0)))
        
    except Exception as e:
        return []

def get_log_by_slot(user_id: str, log_date: date, time_slot: int) -> Optional[Dict]:
    """الحصول على سجل فترة زمنية محددة"""
    logs = get_logs_by_date(user_id, log_date)
    for log in logs:
        if log.get("time_slot") == time_slot:
            return log
    return None

def delete_log(log_id: str, user_id: str = None) -> dict:
    """حذف سجل"""
    try:
        if not user_id:
            from auth import get_current_user
            user = get_current_user()
            if user:
                user_id = user.id
        
        if not user_id:
            return {"status": "error", "message": "المستخدم غير موجود"}
        
        logs_file = _get_logs_file(user_id)
        logs = _load_json(logs_file, [])
        
        logs = [l for l in logs if l.get("id") != log_id]
        _save_json(logs_file, logs)
        
        return {"status": "success", "message": "تم الحذف بنجاح"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

# =============================================
# عمليات الملف الشخصي
# =============================================

def get_user_profile(user_id: str) -> Optional[Dict]:
    """الحصول على ملف المستخدم"""
    try:
        profile_file = _get_profile_file(user_id)
        profile = _load_json(profile_file, None)
        
        if profile is None:
            # إنشاء ملف شخصي افتراضي
            profile = {
                "id": user_id,
                "display_name": "",
                "daily_goal": 100,
                "weekly_goal": 500,
                "monthly_goal": 2000,
                "created_at": datetime.now().isoformat()
            }
            _save_json(profile_file, profile)
        
        return profile
        
    except Exception as e:
        return None

def create_user_profile(user_id: str, display_name: str = None) -> dict:
    """إنشاء ملف شخصي جديد"""
    try:
        profile = {
            "id": user_id,
            "display_name": display_name,
            "daily_goal": 100,
            "weekly_goal": 500,
            "monthly_goal": 2000,
            "created_at": datetime.now().isoformat()
        }
        
        profile_file = _get_profile_file(user_id)
        _save_json(profile_file, profile)
        
        return {"status": "success", "data": profile}
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def update_user_profile(user_id: str, updates: Dict) -> dict:
    """تحديث ملف المستخدم"""
    try:
        profile = get_user_profile(user_id) or {}
        profile.update(updates)
        profile["updated_at"] = datetime.now().isoformat()
        
        profile_file = _get_profile_file(user_id)
        _save_json(profile_file, profile)
        
        return {"status": "success", "message": "تم التحديث بنجاح", "data": profile}
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def update_user_goals(user_id: str, daily: int, weekly: int, monthly: int) -> dict:
    """تحديث أهداف المستخدم"""
    return update_user_profile(user_id, {
        "daily_goal": daily,
        "weekly_goal": weekly,
        "monthly_goal": monthly
    })

# =============================================
# عمليات الفئات
# =============================================

def get_categories(user_id: str = None) -> List[Dict]:
    """الحصول على الفئات"""
    # جلب الفئات الافتراضية المخفية
    hidden_names = []
    if user_id:
        try:
            hidden_file = _get_hidden_defaults_file(user_id)
            hidden_names = _load_json(hidden_file, [])
        except:
            pass
    
    # نسخ الفئات الافتراضية مع إضافة علامة is_default (مع استثناء المخفية)
    categories = []
    for cat in DEFAULT_CATEGORIES:
        if cat.get("name") in hidden_names:
            continue
        c = cat.copy()
        c["is_default"] = True
        categories.append(c)
    
    if user_id:
        try:
            cats_file = _get_categories_file(user_id)
            custom_cats = _load_json(cats_file, [])
            for cat in custom_cats:
                cat["is_default"] = False
            categories.extend(custom_cats)
        except:
            pass
    
    return categories


def hide_default_category(user_id: str, category_name: str) -> dict:
    """إخفاء/حذف فئة افتراضية للمستخدم"""
    try:
        hidden_file = _get_hidden_defaults_file(user_id)
        hidden = _load_json(hidden_file, [])
        
        if category_name not in hidden:
            hidden.append(category_name)
            _save_json(hidden_file, hidden)
        
        return {"status": "success", "message": "تم حذف الفئة بنجاح"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def add_category(user_id: str, name: str, name_ar: str, color: str, icon: str) -> dict:
    """إضافة فئة جديدة"""
    try:
        cats_file = _get_categories_file(user_id)
        cats = _load_json(cats_file, [])
        
        new_cat = {
            "id": f"custom_{datetime.now().timestamp()}",
            "name": name,
            "name_ar": name_ar,
            "color": color,
            "icon": icon,
            "is_default": False
        }
        
        cats.append(new_cat)
        _save_json(cats_file, cats)
        
        return {"status": "success", "data": new_cat}
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def delete_category(category_id: str, user_id: str = None) -> dict:
    """حذف فئة مخصصة"""
    try:
        if not user_id:
            from auth import get_current_user
            user = get_current_user()
            if user:
                user_id = user.id
        
        if not user_id:
            return {"status": "error", "message": "المستخدم غير موجود"}
        
        cats_file = _get_categories_file(user_id)
        cats = _load_json(cats_file, [])
        
        cats = [c for c in cats if c.get("id") != category_id]
        _save_json(cats_file, cats)
        
        return {"status": "success", "message": "تم الحذف بنجاح"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def get_user_theme(user_id: str) -> dict:
    """الحصول على ثيم المستخدم"""
    try:
        user_dir = LOCAL_DATA_DIR / user_id
        theme_file = user_dir / "theme.json"
        return _load_json(theme_file, {})
    except:
        return {}

# =============================================
# عمليات المهام (To-Do List)
# =============================================

def _get_tasks_file(user_id: str):
    """الحصول على مسار ملف المهام"""
    user_dir = LOCAL_DATA_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "tasks.json"

def get_tasks(user_id: str, task_type: str = None) -> List[Dict]:
    """الحصول على المهام (مع تنظيف المنتهية تلقائياً)"""
    try:
        tasks_file = _get_tasks_file(user_id)
        tasks = _load_json(tasks_file, [])
        
        # تنظيف المهام المنتهية
        today = date.today()
        cleaned = []
        for task in tasks:
            t_type = task.get("type", "daily")
            created = datetime.strptime(task.get("created_at", str(today)), "%Y-%m-%d").date()
            
            if t_type == "daily" and created < today:
                continue  # حذف المهام اليومية القديمة
            elif t_type == "weekly":
                # حذف إذا مر أسبوع
                if (today - created).days >= 7:
                    continue
            elif t_type == "monthly":
                # حذف إذا تغير الشهر
                if created.month != today.month or created.year != today.year:
                    continue
            cleaned.append(task)
        
        # حفظ النسخة المنظفة إذا تغيرت
        if len(cleaned) != len(tasks):
            _save_json(tasks_file, cleaned)
        
        if task_type:
            return [t for t in cleaned if t.get("type") == task_type]
        return cleaned
        
    except Exception as e:
        return []

def add_task(user_id: str, title: str, task_type: str = "daily", 
             notes: str = "", due_date: str = None, 
             list_id: str = None, parent_id: str = None) -> dict:
    """إضافة مهمة جديدة مع الخصائص الجديدة"""
    try:
        tasks_file = _get_tasks_file(user_id)
        tasks = _load_json(tasks_file, [])
        
        new_task = {
            "id": f"task_{datetime.now().timestamp()}",
            "title": title,
            "type": task_type,
            "completed": False,
            "starred": False,
            "notes": notes,
            "due_date": due_date,
            "list_id": list_id,     # For future custom lists
            "parent_id": parent_id, # For future subtasks
            "created_at": str(date.today()),
            "updated_at": datetime.now().isoformat()
        }
        
        tasks.append(new_task)
        _save_json(tasks_file, tasks)
        
        return {"status": "success", "data": new_task}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def update_task(user_id: str, task_id: str, updates: dict) -> dict:
    """تحديث بيانات المهمة"""
    try:
        tasks_file = _get_tasks_file(user_id)
        tasks = _load_json(tasks_file, [])
        
        updated = False
        for task in tasks:
            if task.get("id") == task_id:
                task.update(updates)
                task["updated_at"] = datetime.now().isoformat()
                updated = True
                break
        
        if updated:
            _save_json(tasks_file, tasks)
            return {"status": "success", "message": "تم التحديث"}
        return {"status": "error", "message": "المهمة غير موجودة"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def toggle_task(user_id: str, task_id: str) -> dict:
    """تبديل حالة المهمة (مكتملة/غير مكتملة)"""
    # This can now use update_task, but keeping separate for backward compatibility wrapping
    try:
        tasks_file = _get_tasks_file(user_id)
        tasks = _load_json(tasks_file, [])
        
        for task in tasks:
            if task.get("id") == task_id:
                task["completed"] = not task.get("completed", False)
                task["updated_at"] = datetime.now().isoformat()
                break
        
        _save_json(tasks_file, tasks)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def delete_task(user_id: str, task_id: str) -> dict:
    """حذف مهمة"""
    try:
        tasks_file = _get_tasks_file(user_id)
        tasks = _load_json(tasks_file, [])
        
        tasks = [t for t in tasks if t.get("id") != task_id]
        _save_json(tasks_file, tasks)
        
        return {"status": "success", "message": "تم الحذف"}
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}


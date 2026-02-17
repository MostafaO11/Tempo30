"""
نظام المصادقة - الوضع المحلي
Authentication System - Local Mode
"""

import streamlit as st
import json
import hashlib
from pathlib import Path
from datetime import datetime
from config import USE_LOCAL_STORAGE, LOCAL_DATA_DIR

def init_auth_state():
    """تهيئة حالة المصادقة في الجلسة"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

def _get_users_file():
    """الحصول على مسار ملف المستخدمين"""
    LOCAL_DATA_DIR.mkdir(exist_ok=True)
    return LOCAL_DATA_DIR / "users.json"

def _load_users():
    """تحميل المستخدمين من الملف"""
    users_file = _get_users_file()
    if users_file.exists():
        with open(users_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save_users(users):
    """حفظ المستخدمين في الملف"""
    users_file = _get_users_file()
    with open(users_file, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def _hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

class LocalUser:
    """كائن المستخدم المحلي"""
    def __init__(self, user_data):
        self.id = user_data.get("id")
        self.email = user_data.get("email")
        self.user_metadata = user_data.get("metadata", {})

def sign_up(email: str, password: str, display_name: str = None) -> dict:
    """إنشاء حساب جديد"""
    try:
        users = _load_users()
        
        if email in users:
            return {"status": "error", "message": "هذا البريد الإلكتروني مسجل بالفعل"}
        
        if len(password) < 6:
            return {"status": "error", "message": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"}
        
        user_id = hashlib.md5(email.encode()).hexdigest()
        
        users[email] = {
            "id": user_id,
            "email": email,
            "password": _hash_password(password),
            "metadata": {
                "display_name": display_name or email.split("@")[0]
            },
            "created_at": datetime.now().isoformat()
        }
        
        _save_users(users)
        
        return {
            "status": "success",
            "message": "تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.",
            "user": LocalUser(users[email])
        }
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def sign_in(email: str, password: str) -> dict:
    """تسجيل الدخول"""
    try:
        users = _load_users()
        
        if email not in users:
            return {"status": "error", "message": "بيانات الدخول غير صحيحة"}
        
        user_data = users[email]
        
        if user_data["password"] != _hash_password(password):
            return {"status": "error", "message": "بيانات الدخول غير صحيحة"}
        
        user = LocalUser(user_data)
        st.session_state.user = user
        st.session_state.access_token = user.id
        
        return {
            "status": "success",
            "message": "تم تسجيل الدخول بنجاح!",
            "user": user
        }
        
    except Exception as e:
        return {"status": "error", "message": f"خطأ: {str(e)}"}

def sign_out():
    """تسجيل الخروج"""
    st.session_state.user = None
    st.session_state.access_token = None
    return {"status": "success", "message": "تم تسجيل الخروج"}

def reset_password(email: str) -> dict:
    """إعادة تعيين كلمة المرور (غير متاحة في الوضع المحلي)"""
    return {
        "status": "info",
        "message": "هذه الميزة غير متاحة في الوضع المحلي"
    }

def get_current_user():
    """الحصول على المستخدم الحالي"""
    return st.session_state.get("user")

def is_authenticated() -> bool:
    """التحقق من حالة المصادقة"""
    return st.session_state.get("user") is not None

def get_user_display_name() -> str:
    """الحصول على الاسم المعروض للمستخدم"""
    user = get_current_user()
    if user:
        metadata = user.user_metadata or {}
        return metadata.get("display_name", user.email.split("@")[0])
    return "زائر"

def render_auth_page():
    """عرض صفحة المصادقة"""
    
    st.markdown("""
    <style>
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
    }
    .auth-title {
        text-align: center;
        font-size: 2rem;
        margin-bottom: 2rem;
        color: #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="auth-title">🎯 متتبع الإنتاجية</h1>', unsafe_allow_html=True)
    
    # تنبيه الوضع المحلي
    if USE_LOCAL_STORAGE:
        st.info("🔧 يعمل التطبيق في الوضع المحلي. البيانات تُحفظ على جهازك.")
    
    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("📧 البريد الإلكتروني", key="login_email")
            password = st.text_input("🔒 كلمة المرور", type="password", key="login_password")
            submit = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submit:
                if email and password:
                    result = sign_in(email, password)
                    if result["status"] == "success":
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.warning("يرجى ملء جميع الحقول")
    
    with tab2:
        with st.form("signup_form"):
            display_name = st.text_input("👤 الاسم", key="signup_name")
            email = st.text_input("📧 البريد الإلكتروني", key="signup_email")
            password = st.text_input("🔒 كلمة المرور", type="password", key="signup_password")
            password_confirm = st.text_input("🔒 تأكيد كلمة المرور", type="password", key="signup_password_confirm")
            submit = st.form_submit_button("إنشاء حساب", use_container_width=True)
            
            if submit:
                if email and password and password_confirm:
                    if password != password_confirm:
                        st.error("كلمتا المرور غير متطابقتين")
                    elif len(password) < 6:
                        st.error("كلمة المرور يجب أن تكون 6 أحرف على الأقل")
                    else:
                        result = sign_up(email, password, display_name)
                        if result["status"] == "success":
                            st.success(result["message"])
                        else:
                            st.error(result["message"])
                else:
                    st.warning("يرجى ملء جميع الحقول")

    # حساب تجريبي سريع
    st.markdown("---")
    st.markdown("### 🚀 تجربة سريعة")
    if st.button("إنشاء حساب تجريبي والدخول", use_container_width=True):
        demo_email = "demo@example.com"
        demo_password = "demo123"
        
        # إنشاء الحساب إذا لم يكن موجوداً
        sign_up(demo_email, demo_password, "مستخدم تجريبي")
        
        # تسجيل الدخول
        result = sign_in(demo_email, demo_password)
        if result["status"] == "success":
            st.success("تم الدخول بالحساب التجريبي!")
            st.rerun()

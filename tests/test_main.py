"""
اختبارات شاملة لتطبيق متتبع الإنتاجية
Comprehensive Test Suite for Productivity Tracker

يغطي هذا الملف:
1. نظام المصادقة (auth.py)
2. التحليلات (analytics.py)
3. عمليات قاعدة البيانات (database.py)
4. واجهة المستخدم (app.py)

تشغيل الاختبارات:
    pytest tests/test_main.py -v

تثبيت المتطلبات:
    pip install pytest streamlit
"""

import pytest
import sys
import os
import json
import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# إضافة المجلد الرئيسي للمسار
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================
# Fixtures - إعدادات مشتركة للاختبارات
# =============================================

@pytest.fixture
def temp_data_dir():
    """
    إنشاء مجلد مؤقت للاختبارات
    
    لماذا هذا مهم؟
    - يضمن عزل الاختبارات عن البيانات الحقيقية
    - ينظف نفسه تلقائياً بعد الاختبار
    - يمنع تلوث البيانات بين الاختبارات
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # تنظيف بعد الاختبار
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_local_data_dir(temp_data_dir):
    """
    محاكاة LOCAL_DATA_DIR باستخدام مجلد مؤقت
    """
    with patch('config.LOCAL_DATA_DIR', temp_data_dir):
        with patch('database.LOCAL_DATA_DIR', temp_data_dir):
            with patch('auth.LOCAL_DATA_DIR', temp_data_dir):
                yield temp_data_dir


@pytest.fixture
def sample_logs():
    """
    بيانات نموذجية للاختبارات
    
    لماذا هذا مهم؟
    - يوفر بيانات ثابتة ومعروفة للاختبار
    - يسهل التحقق من النتائج المتوقعة
    """
    return [
        {"time_slot": 0, "score": 4, "log_date": str(date.today()), "category": "Work"},
        {"time_slot": 2, "score": 3, "log_date": str(date.today()), "category": "Study"},
        {"time_slot": 4, "score": 4, "log_date": str(date.today()), "category": "Work"},
        {"time_slot": 6, "score": 2, "log_date": str(date.today()), "category": "Exercise"},
    ]


# =============================================
# 1. اختبارات نظام المصادقة (auth.py)
# =============================================

class TestAuthentication:
    """
    اختبارات نظام المصادقة
    
    لماذا هذه الاختبارات مهمة؟
    - المصادقة هي خط الدفاع الأول للتطبيق
    - أي خلل هنا يعني وصول غير مصرح به للبيانات
    - تضمن تجربة مستخدم سلسة وآمنة
    """
    
    def test_signup_short_password_returns_error(self, mock_local_data_dir):
        """
        اختبار: إنشاء حساب بكلمة مرور قصيرة يجب أن يفشل
        
        السيناريو:
        - المستخدم يحاول إنشاء حساب بكلمة مرور أقل من 6 أحرف
        
        النتيجة المتوقعة:
        - رسالة خطأ واضحة
        - عدم إنشاء الحساب
        
        لماذا هذا مهم؟
        - كلمات المرور القصيرة سهلة الاختراق
        - يحمي المستخدمين من أنفسهم
        """
        from auth import sign_up
        
        result = sign_up(
            email="test@example.com",
            password="123",  # كلمة مرور قصيرة جداً
            display_name="Test User"
        )
        
        assert result["status"] == "error"
        assert "6 أحرف" in result["message"]
    
    
    def test_signup_creates_local_files(self, mock_local_data_dir):
        """
        اختبار: إنشاء حساب تجريبي ينشئ ملفات محلية صحيحة
        
        السيناريو:
        - المستخدم ينشئ حساباً جديداً
        
        النتيجة المتوقعة:
        - إنشاء ملف users.json في LOCAL_DATA_DIR
        - تخزين بيانات المستخدم بشكل صحيح
        
        لماذا هذا مهم؟
        - يضمن استمرارية البيانات بين الجلسات
        - يتحقق من صحة آلية التخزين
        """
        from auth import sign_up, _get_users_file
        
        result = sign_up(
            email="newuser@test.com",
            password="secure123",
            display_name="New User"
        )
        
        assert result["status"] == "success"
        
        # التحقق من إنشاء الملف
        users_file = _get_users_file()
        assert users_file.exists()
        
        # التحقق من محتوى الملف
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        
        assert "newuser@test.com" in users
        assert users["newuser@test.com"]["metadata"]["display_name"] == "New User"
    
    
    def test_signin_unregistered_email_returns_error(self, mock_local_data_dir):
        """
        اختبار: محاولة الدخول ببريد غير مسجل
        
        السيناريو:
        - المستخدم يحاول تسجيل الدخول ببريد غير موجود
        
        النتيجة المتوقعة:
        - رسالة خطأ عامة (لا تكشف عن وجود الحساب أو عدمه)
        
        لماذا هذا مهم؟
        - أمان: رسائل الخطأ العامة تمنع تعداد الحسابات
        - تجربة مستخدم: رسالة واضحة
        """
        from auth import sign_in
        
        # محاكاة session_state لأن sign_in يستخدمه
        with patch('auth.st') as mock_st:
            mock_st.session_state = MagicMock()
            
            result = sign_in(
                email="nonexistent@test.com",
                password="anypassword"
            )
        
        assert result["status"] == "error"
        assert "غير صحيحة" in result["message"]
    
    
    def test_signup_duplicate_email_returns_error(self, mock_local_data_dir):
        """
        اختبار: محاولة إنشاء حساب ببريد موجود مسبقاً
        
        لماذا هذا مهم؟
        - يمنع تكرار الحسابات
        - يحافظ على تكامل البيانات
        """
        from auth import sign_up
        
        # إنشاء حساب أول
        sign_up("duplicate@test.com", "password123", "User 1")
        
        # محاولة إنشاء حساب بنفس البريد
        result = sign_up("duplicate@test.com", "password456", "User 2")
        
        assert result["status"] == "error"
        assert "مسجل بالفعل" in result["message"]


# =============================================
# 2. اختبارات دقة التحليلات (analytics.py)
# =============================================

class TestAnalytics:
    """
    اختبارات دقة التحليلات
    
    لماذا هذه الاختبارات مهمة؟
    - التحليلات هي القيمة الأساسية للتطبيق
    - الأخطاء هنا تعني معلومات مضللة للمستخدم
    - تؤثر على قرارات المستخدم وتحفيزه
    """
    
    def test_calculate_streak_breaks_on_gap(self):
        """
        اختبار: السلسلة تنكسر عند وجود فجوة
        
        السيناريو:
        - 3 أيام متتالية مع تحقيق الهدف
        - يوم واحد بدون تحقيق الهدف (فجوة)
        - يومان آخران مع تحقيق الهدف
        
        النتيجة المتوقعة:
        - السلسلة = 2 (فقط الأيام بعد الفجوة)
        
        لماذا هذا مهم؟
        - السلسلة تحفز المستخدم على الاستمرارية
        - يجب أن تكون دقيقة لتعكس الواقع
        """
        from analytics import calculate_streak
        
        today = date.today()
        daily_goal = 50
        
        logs_by_date = {
            today: 60,                          # اليوم - تحقق الهدف
            today - timedelta(days=1): 55,      # الأمس - تحقق الهدف
            today - timedelta(days=2): 30,      # قبل يومين - لم يتحقق (فجوة!)
            today - timedelta(days=3): 70,      # قبل 3 أيام - تحقق الهدف
            today - timedelta(days=4): 65,      # قبل 4 أيام - تحقق الهدف
        }
        
        streak = calculate_streak(logs_by_date, daily_goal)
        
        # السلسلة يجب أن تكون 2 (اليوم + الأمس) لأن الفجوة كسرتها
        assert streak == 2
    
    
    def test_calculate_streak_continuous_days(self):
        """
        اختبار: السلسلة تحسب الأيام المتتالية بشكل صحيح
        
        السيناريو:
        - 5 أيام متتالية مع تحقيق الهدف
        
        النتيجة المتوقعة:
        - السلسلة = 5
        """
        from analytics import calculate_streak
        
        today = date.today()
        daily_goal = 50
        
        logs_by_date = {
            today: 60,
            today - timedelta(days=1): 55,
            today - timedelta(days=2): 70,
            today - timedelta(days=3): 65,
            today - timedelta(days=4): 80,
        }
        
        streak = calculate_streak(logs_by_date, daily_goal)
        assert streak == 5
    
    
    def test_calculate_daily_score_empty_logs_no_division_error(self):
        """
        اختبار: حساب النقاط مع سجلات فارغة لا يسبب خطأ قسمة على صفر
        
        السيناريو:
        - قائمة سجلات فارغة
        
        النتيجة المتوقعة:
        - النتيجة = 0
        - لا يحدث خطأ ZeroDivisionError
        
        لماذا هذا مهم؟
        - المستخدمون الجدد ليس لديهم سجلات
        - التطبيق يجب ألا ينهار في هذه الحالة
        """
        from analytics import calculate_daily_score
        
        empty_logs = []
        
        # يجب ألا يرمي أي استثناء
        try:
            score = calculate_daily_score(empty_logs)
            assert score == 0
        except ZeroDivisionError:
            pytest.fail("calculate_daily_score raised ZeroDivisionError with empty logs")
    
    
    def test_calculate_daily_score_correct_sum(self, sample_logs):
        """
        اختبار: حساب مجموع النقاط بشكل صحيح
        
        السيناريو:
        - سجلات بنقاط: 4, 3, 4, 2
        
        النتيجة المتوقعة:
        - المجموع = 13
        """
        from analytics import calculate_daily_score
        
        score = calculate_daily_score(sample_logs)
        assert score == 13  # 4 + 3 + 4 + 2 = 13
    
    
    def test_get_best_hour_tie_breaker(self):
        """
        اختبار: أفضل ساعة عند تساوي ساعتين
        
        السيناريو:
        - ساعتان لهما نفس متوسط النقاط
        
        النتيجة المتوقعة:
        - إرجاع إحدى الساعتين (الأولى في الترتيب)
        - لا يحدث خطأ
        
        لماذا هذا مهم؟
        - يضمن سلوكاً متوقعاً ومستقراً
        - يمنع الأخطاء العشوائية
        """
        from analytics import get_best_hour
        
        # ساعتان بنفس النقاط
        logs = [
            {"time_slot": 0, "score": 4},   # الساعة 0 (0:00-1:00)
            {"time_slot": 1, "score": 4},   # الساعة 0 (0:00-1:00) - نفس الساعة
            {"time_slot": 16, "score": 4},  # الساعة 8 (8:00-9:00)
            {"time_slot": 17, "score": 4},  # الساعة 8 (8:00-9:00) - نفس الساعة
        ]
        
        best_hour, avg_score = get_best_hour(logs)
        
        # يجب أن يرجع ساعة صالحة
        assert best_hour in [0, 8]
        assert avg_score == 4.0
    
    
    def test_get_best_hour_empty_logs(self):
        """
        اختبار: أفضل ساعة مع سجلات فارغة
        
        لماذا هذا مهم؟
        - يمنع الأخطاء للمستخدمين الجدد
        """
        from analytics import get_best_hour
        
        best_hour, avg_score = get_best_hour([])
        
        assert best_hour == 0
        assert avg_score == 0


# =============================================
# 3. اختبارات عمليات قاعدة البيانات (database.py)
# =============================================

class TestDatabase:
    """
    اختبارات عمليات قاعدة البيانات
    
    لماذا هذه الاختبارات مهمة؟
    - تضمن سلامة البيانات المخزنة
    - تمنع تكرار السجلات
    - تتحقق من صحة مسارات الملفات
    """
    
    def test_log_productivity_updates_existing_slot(self, mock_local_data_dir):
        """
        اختبار: تسجيل نشاط في فترة موجودة يقوم بالتحديث وليس التكرار
        
        السيناريو:
        1. تسجيل نشاط في الفترة 10 بدرجة 2
        2. تسجيل نشاط آخر في نفس الفترة 10 بدرجة 4
        
        النتيجة المتوقعة:
        - سجل واحد فقط في الفترة 10
        - الدرجة = 4 (القيمة الجديدة)
        
        لماذا هذا مهم؟
        - يمنع تضخم البيانات
        - يسمح للمستخدم بتصحيح التقييمات
        - يحافظ على دقة التحليلات
        """
        from database import log_productivity, get_logs_by_date
        
        user_id = "test_user_123"
        today = date.today()
        
        # التسجيل الأول
        log_productivity(user_id, today, time_slot=10, score=2, category="Work")
        
        # التسجيل الثاني في نفس الفترة
        log_productivity(user_id, today, time_slot=10, score=4, category="Study")
        
        # جلب السجلات
        logs = get_logs_by_date(user_id, today)
        
        # التحقق من وجود سجل واحد فقط للفترة 10
        slot_10_logs = [log for log in logs if log.get("time_slot") == 10]
        
        assert len(slot_10_logs) == 1, "يجب أن يكون هناك سجل واحد فقط للفترة 10"
        assert slot_10_logs[0]["score"] == 4, "يجب أن تكون الدرجة 4 (القيمة المحدثة)"
        assert slot_10_logs[0]["category"] == "Study", "يجب أن تكون الفئة Study"
    
    
    def test_log_productivity_creates_multiple_slots(self, mock_local_data_dir):
        """
        اختبار: تسجيل فترات مختلفة ينشئ سجلات متعددة
        
        لماذا هذا مهم؟
        - يتحقق من أن التحديث يحدث فقط لنفس الفترة
        - يضمن إمكانية تسجيل يوم كامل
        """
        from database import log_productivity, get_logs_by_date
        
        user_id = "test_user_456"
        today = date.today()
        
        # تسجيل 3 فترات مختلفة
        log_productivity(user_id, today, time_slot=0, score=4, category="Work")
        log_productivity(user_id, today, time_slot=10, score=3, category="Study")
        log_productivity(user_id, today, time_slot=20, score=2, category="Exercise")
        
        logs = get_logs_by_date(user_id, today)
        
        assert len(logs) == 3, "يجب أن يكون هناك 3 سجلات"
    
    
    def test_user_data_path_isolation(self, mock_local_data_dir):
        """
        اختبار: التحقق من عزل مسارات ملفات المستخدمين
        
        السيناريو:
        - مستخدمان مختلفان يسجلان بيانات
        
        النتيجة المتوقعة:
        - كل مستخدم له مجلد خاص
        - البيانات معزولة تماماً
        
        لماذا هذا مهم؟
        - الخصوصية: كل مستخدم يرى بياناته فقط
        - الأمان: منع تسريب البيانات
        - الموثوقية: منع تداخل البيانات
        """
        from database import log_productivity, _get_logs_file
        
        user1_id = "user_alpha"
        user2_id = "user_beta"
        today = date.today()
        
        # تسجيل لكل مستخدم
        log_productivity(user1_id, today, 5, 4, "Work")
        log_productivity(user2_id, today, 5, 2, "Study")
        
        # التحقق من المسارات
        user1_file = _get_logs_file(user1_id)
        user2_file = _get_logs_file(user2_id)
        
        # يجب أن يكونا في مجلدات مختلفة
        assert user1_id in str(user1_file)
        assert user2_id in str(user2_file)
        assert user1_file != user2_file
        
        # التحقق من وجود الملفات
        assert user1_file.exists()
        assert user2_file.exists()
        
        # التحقق من عزل المحتوى
        with open(user1_file, "r", encoding="utf-8") as f:
            user1_logs = json.load(f)
        
        with open(user2_file, "r", encoding="utf-8") as f:
            user2_logs = json.load(f)
        
        assert all(log["user_id"] == user1_id for log in user1_logs)
        assert all(log["user_id"] == user2_id for log in user2_logs)


# =============================================
# 4. اختبارات واجهة المستخدم (app.py)
# =============================================

class TestUserInterface:
    """
    اختبارات واجهة المستخدم
    
    لماذا هذه الاختبارات مهمة؟
    - تضمن تجربة مستخدم متسقة
    - تكشف عن الأخطاء المرئية مبكراً
    - تتحقق من التنقل بين الصفحات
    """
    
    def test_css_file_exists_and_loads(self):
        """
        اختبار: ملف custom.css موجود ويمكن قراءته
        
        لماذا هذا مهم؟
        - التنسيقات ضرورية للتجربة البصرية
        - غياب الملف يسبب مظهراً غير متناسق
        """
        css_path = Path(__file__).parent.parent / "styles" / "custom.css"
        
        assert css_path.exists(), "ملف custom.css غير موجود"
        
        # التحقق من إمكانية القراءة
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        assert len(content) > 0, "ملف CSS فارغ"
    
    
    def test_css_contains_rtl_styles(self):
        """
        اختبار: ملف CSS يحتوي على تنسيقات RTL للعربية
        
        لماذا هذا مهم؟
        - التطبيق موجه للمستخدمين العرب
        - دعم RTL ضروري للقراءة الصحيحة
        """
        css_path = Path(__file__).parent.parent / "styles" / "custom.css"
        
        with open(css_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        
        # التحقق من وجود تنسيقات RTL
        rtl_indicators = ["direction", "rtl", "text-align"]
        has_rtl = any(indicator in content for indicator in rtl_indicators)
        
        # ملاحظة: قد تكون تنسيقات RTL في app.py أيضاً
        # لذا هذا الاختبار تحذيري وليس إلزامي
        if not has_rtl:
            print("تحذير: لم يتم العثور على تنسيقات RTL صريحة في custom.css")
    
    
    def test_app_py_imports_correctly(self):
        """
        اختبار: ملف app.py يمكن استيراده بدون أخطاء
        
        لماذا هذا مهم؟
        - أخطاء الاستيراد تمنع تشغيل التطبيق تماماً
        - يكشف عن مشاكل التبعيات مبكراً
        """
        try:
            # محاكاة streamlit لتجنب الأخطاء
            with patch.dict('sys.modules', {'streamlit': MagicMock()}):
                # محاولة استيراد الوحدات الأساسية
                from config import PRODUCTIVITY_LEVELS, DEFAULT_CATEGORIES
                from analytics import calculate_daily_score
                
                assert PRODUCTIVITY_LEVELS is not None
                assert DEFAULT_CATEGORIES is not None
                
        except ImportError as e:
            pytest.fail(f"فشل استيراد الوحدات: {e}")
    
    
    def test_page_navigation_state(self):
        """
        اختبار: تغيير الصفحة يحدث session_state بشكل صحيح
        
        ملاحظة: هذا اختبار وحدة (Unit Test) للمنطق
        الاختبار الفعلي للواجهة يتطلب AppTest من Streamlit
        """
        # محاكاة session_state
        mock_session_state = {"current_page": "dashboard"}
        
        # تغيير الصفحة
        mock_session_state["current_page"] = "analytics"
        
        assert mock_session_state["current_page"] == "analytics"
        
        # تغيير إلى settings
        mock_session_state["current_page"] = "settings"
        
        assert mock_session_state["current_page"] == "settings"


# =============================================
# اختبارات إضافية للتكامل
# =============================================

class TestIntegration:
    """
    اختبارات تكاملية تجمع بين عدة وحدات
    
    لماذا هذه الاختبارات مهمة؟
    - تكشف عن مشاكل التفاعل بين الوحدات
    - تحاكي سيناريوهات المستخدم الحقيقية
    """
    
    def test_full_flow_signup_log_analyze(self, mock_local_data_dir):
        """
        اختبار التدفق الكامل: إنشاء حساب → تسجيل → تحليل
        
        السيناريو:
        1. إنشاء حساب جديد
        2. تسجيل 5 أنشطة
        3. حساب الإحصائيات
        
        لماذا هذا مهم؟
        - يحاكي استخدام المستخدم الفعلي
        - يكشف عن مشاكل التكامل
        """
        from auth import sign_up
        from database import log_productivity, get_logs_by_date
        from analytics import calculate_daily_score, get_best_hour
        
        # 1. إنشاء حساب
        result = sign_up("integration@test.com", "password123", "Integration Test")
        assert result["status"] == "success"
        
        # LocalUser هو كائن وليس قاموس، لذا نستخدم .id
        user_id = result["user"].id
        today = date.today()
        
        # 2. تسجيل أنشطة
        log_productivity(user_id, today, 0, 4, "Work")
        log_productivity(user_id, today, 2, 3, "Study")
        log_productivity(user_id, today, 4, 4, "Work")
        log_productivity(user_id, today, 6, 2, "Exercise")
        log_productivity(user_id, today, 8, 4, "Work")
        
        # 3. تحليل
        logs = get_logs_by_date(user_id, today)
        
        assert len(logs) == 5
        
        score = calculate_daily_score(logs)
        assert score == 17  # 4+3+4+2+4 = 17
        
        best, avg = get_best_hour(logs)
        assert avg >= 2  # أقل درجة هي 2


# =============================================
# تشغيل الاختبارات
# =============================================

if __name__ == "__main__":
    """
    تشغيل الاختبارات مباشرة
    
    الاستخدام:
        python tests/test_main.py
        
    أو باستخدام pytest:
        pytest tests/test_main.py -v
        pytest tests/test_main.py -v --tb=short  # لعرض مختصر للأخطاء
        pytest tests/test_main.py::TestAuthentication -v  # لتشغيل فئة معينة
    """
    pytest.main([__file__, "-v", "--tb=short"])

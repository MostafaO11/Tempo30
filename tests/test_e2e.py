
import re
import time
import shutil
from pathlib import Path
from playwright.sync_api import Page, expect
import pytest
import uuid
import json
import hashlib

# Paths
LOCAL_DATA_DIR = Path(__file__).parent.parent / "local_data"

@pytest.fixture
def test_user_data():
    """Fixture to create and cleanup test user data."""
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_{unique_id}@example.com"
    password = "password123"
    name = f"User {unique_id}"
    
    yield {"email": email, "password": password, "name": name, "unique_id": unique_id}
    
    # Cleanup
    users_file = LOCAL_DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, "r", encoding="utf-8") as f:
                users = json.load(f)
            if email in users:
                del users[email]
                with open(users_file, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error cleaning up user: {e}")

    user_id_hash = hashlib.md5(email.encode()).hexdigest()
    logs_file = LOCAL_DATA_DIR / f"productivity_logs_{user_id_hash}.json"
    if logs_file.exists():
        try:
            logs_file.unlink()
        except Exception as e:
            print(f"Error cleaning up logs: {e}")


def save_debug_artifacts(page, name):
    """Save content for debugging."""
    try:
        with open(f"debug_{name}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
    except Exception as e:
        print(f"Failed to save debug artifacts: {e}")

def test_app_loads(page: Page):
    """Verify the app loads and shows the title."""
    try:
        page.goto("/")
        page.wait_for_timeout(2000)
        
        title = page.title()
        assert "متتبع" in title or "Productivity" in title
        
    except Exception as e:
        save_debug_artifacts(page, "app_loads")
        raise e

def test_full_user_flow(page: Page, test_user_data):
    """
    Test the full user flow using the test_user_data fixture.
    """
    email = test_user_data["email"]
    password = test_user_data["password"]
    name = test_user_data["name"]
    unique_id = test_user_data["unique_id"]

    try:
        page.goto("/")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        # 1. Sign Up
        page.get_by_role("tab", name=re.compile(".*إنشاء حساب.*")).click()
        page.wait_for_timeout(500)
        
        signup_panel = page.get_by_role("tabpanel").filter(has=page.get_by_role("button", name="إنشاء حساب", exact=True))
        
        signup_panel.get_by_label("👤 الاسم").fill(name)
        signup_panel.get_by_label("📧 البريد الإلكتروني").fill(email) 
        signup_panel.get_by_label("🔒 كلمة المرور").fill(password)
        signup_panel.get_by_label("🔒 تأكيد كلمة المرور").fill(password)
        
        signup_panel.get_by_role("button", name="إنشاء حساب", exact=True).click()
        
        expect(page.get_by_text("تم إنشاء الحساب بنجاح")).to_be_visible(timeout=10000)
        
        # 2. Log In
        page.get_by_role("tab", name=re.compile(".*تسجيل الدخول.*")).click()
        page.wait_for_timeout(500)
        
        login_panel = page.get_by_role("tabpanel").filter(has=page.get_by_role("button", name="تسجيل الدخول", exact=True))
        
        login_panel.get_by_label("📧 البريد الإلكتروني").fill(email)
        login_panel.get_by_label("🔒 كلمة المرور").fill(password)
        
        login_panel.get_by_role("button", name="تسجيل الدخول", exact=True).click()
        
        expect(page.get_by_text(f"مرحباً")).to_be_visible(timeout=15000)
        expect(page.get_by_text(name)).to_be_visible()

        # 3. Navigation to Tasks
        page.get_by_role("button", name=re.compile(".*المهام.*")).click()
        expect(page.get_by_text("قائمة المهام")).to_be_visible()
        
        # 4. Add Task
        summary = page.locator("summary").filter(has_text="إضافة مهمة جديدة")
        if summary.count() > 0:
            if not page.get_by_label("عنوان المهمة").is_visible():
                summary.click()
        elif not page.get_by_label("عنوان المهمة").is_visible():
             page.get_by_text("إضافة مهمة جديدة").first.click()
        
        task_title = f"Task {unique_id}"
        page.get_by_label("عنوان المهمة").fill(task_title)
        
        page.get_by_role("button", name="✅ إضافة", exact=True).click()
        
        # Check for persistence
        page.wait_for_timeout(1000)
        expect(page.get_by_text(task_title)).to_be_visible(timeout=10000)
        
        # 5. Log Productivity on Dashboard
        page.get_by_role("button", name=re.compile(".*لوحة التحكم.*")).first.click()
        page.wait_for_timeout(1000)
        expect(page.get_by_text("لوحة التحكم").first).to_be_visible()
        
        # Select slot
        page.get_by_role("button", name="📝", exact=True).first.click()
        page.wait_for_timeout(1000)
        
        # Log productivity - Button text is "medium" (متوسطة) but celebration is "Good!" (جيد!)
        page.get_by_role("button").filter(has_text="متوسطة").first.click()
        
        expect(page.get_by_text("جيد! أنت على الطريق الصحيح!")).to_be_visible(timeout=10000)
        
    except Exception as e:
        save_debug_artifacts(page, "full_flow")
        raise e

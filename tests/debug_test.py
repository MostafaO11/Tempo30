
from playwright.sync_api import Page
import time

def test_debug_content(page: Page):
    print(f"\n DEBUG: Navigating to base URL...")
    page.goto("/")
    page.wait_for_timeout(5000) # Wait for 5s for things to load
    
    print(f"DEBUG: Page Title: {page.title()}")
    print(f"DEBUG: Page Content Snippet: {page.content()[:2000]}")
    
    # Check for specific elements
    print(f"DEBUG: Has 'متتبع الإنتاجية'? {'متتبع الإنتاجية' in page.content()}")
    print(f"DEBUG: Has 'Streamlit'? {'Streamlit' in page.content()}")

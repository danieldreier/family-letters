import pytest
from playwright.sync_api import expect
import os
import time

BASE_URL = "http://localhost:8502"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test-results')

@pytest.fixture(autouse=True)
def setup_screenshots():
    """Ensure screenshot directory exists."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def take_debug_screenshot(page, name, print_elements=False):
    """Take a screenshot and optionally print debug info about elements."""
    timestamp = time.strftime("%H%M%S")
    filename = f"{timestamp}_{name}.png"
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, filename))
    
    if print_elements:
        print(f"\nDebug info for {name}:")
        # Get all input elements
        inputs = page.locator("input").all()
        print(f"Found {len(inputs)} input elements")
        for i, input_el in enumerate(inputs):
            try:
                placeholder = input_el.get_attribute("placeholder")
                type_attr = input_el.get_attribute("type")
                label = page.locator(f"label[for='{input_el.get_attribute('id')}']").text_content() if input_el.get_attribute('id') else None
                print(f"Input {i}: placeholder='{placeholder}', type='{type_attr}', label='{label}'")
            except Exception as e:
                print(f"Error getting input {i} attributes: {e}")
        
        # Print text content for debugging
        text_content = page.locator("body").text_content()
        print(f"Page text content: {text_content[:200]}...")  # First 200 chars

def authenticate(page):
    """Handle authentication for tests."""
    # Wait for password input
    password_input = page.get_by_placeholder("Enter password")
    take_debug_screenshot(page, "password_screen", print_elements=True)
    
    # Enter password and submit
    password_input.fill("test123")  # Use test password
    password_input.press("Enter")
    page.wait_for_load_state("networkidle")
    take_debug_screenshot(page, "post_auth", print_elements=True)

@pytest.mark.ui
def test_letters_list_and_expand(page, test_db):
    """Test that letters are listed and can be expanded/collapsed."""
    # Navigate to the page
    print("\nStarting test_letters_list_and_expand")
    page.goto(f"{BASE_URL}/")
    take_debug_screenshot(page, "initial_load", print_elements=True)
    
    try:
        # Handle authentication
        authenticate(page)
        
        # Wait for the content to load
        page.wait_for_selector("text=Sample letter 1", timeout=60000)  # Increased timeout for Streamlit
        take_debug_screenshot(page, "letters_loaded", print_elements=True)
        
        # Verify both letters are visible
        expect(page.locator("text=Sample letter 1")).to_be_visible()
        expect(page.locator("text=Sample letter 2")).to_be_visible()
        
        # Click the first letter's expander
        first_letter = page.locator("text=Sample letter 1").first
        first_letter.click()
        take_debug_screenshot(page, "letter_expanded", print_elements=True)
        
        # Verify expanded content is visible
        expect(page.locator("text=John Doe")).to_be_visible()
        expect(page.locator("text=Jane Doe")).to_be_visible()
        expect(page.locator("text=1943-01-15")).to_be_visible()
        
        # Click again to collapse
        first_letter.click()
        take_debug_screenshot(page, "letter_collapsed", print_elements=True)
        
        # Verify the content is no longer visible
        expect(page.locator("text=1943-01-15")).not_to_be_visible()
    except Exception as e:
        take_debug_screenshot(page, "error_state", print_elements=True)
        print(f"Test failed with error: {str(e)}")
        raise e

@pytest.mark.ui
@pytest.mark.smoke
def test_basic_page_load(page):
    """Smoke test to verify the page loads successfully."""
    try:
        print("\nStarting test_basic_page_load")
        
        # Navigate to the page
        page.goto(f"{BASE_URL}/")
        print("Page loaded")
        
        # Take screenshot
        take_debug_screenshot(page, "1_initial_load", print_elements=True)
        
        # Print page content
        print("\nPage content:")
        print(page.content())
        
        # Wait for password input
        print("\nWaiting for password input")
        page.wait_for_selector("input[type='password']", state="visible", timeout=10000)
        print("Found password input")
        
        take_debug_screenshot(page, "2_with_password", print_elements=True)
        
    except Exception as e:
        take_debug_screenshot(page, "error_state", print_elements=True)
        print(f"Test failed with error: {str(e)}")
        raise e

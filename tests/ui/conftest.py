import os
import pytest
import sqlite3
from pathlib import Path
import toml
import subprocess
import time
import requests
from urllib.error import URLError

# Set up test environment variables
TEST_PASSWORD = 'test123'

def setup_streamlit_secrets():
    """Set up Streamlit secrets for testing."""
    secrets_dir = Path.home() / '.streamlit'
    secrets_dir.mkdir(exist_ok=True)
    secrets_file = secrets_dir / 'secrets.toml'
    
    secrets = {
        'password': TEST_PASSWORD,
        'gcs_bucket_name': 'test-bucket'
    }
    
    with open(secrets_file, 'w') as f:
        toml.dump(secrets, f)

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment including Streamlit secrets."""
    setup_streamlit_secrets()
    os.environ['LETTERS_DB'] = str(Path(__file__).parent.parent / "test_letters.db")

@pytest.fixture(scope="session")
def browser(playwright):
    """Create browser with custom launch arguments."""
    browser = playwright.chromium.launch(
        headless=False,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ]
    )
    yield browser
    browser.close()

@pytest.fixture
def context(browser):
    """Create browser context."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        java_script_enabled=True
    )
    yield context
    context.close()

@pytest.fixture
def page(context):
    """Create page."""
    page = context.new_page()
    yield page
    page.close()

@pytest.fixture(scope="session", autouse=True)
def streamlit_app():
    """Ensure Streamlit app is running."""
    process = None
    port = 8502  # Update port to match running instance
    
    # Check if app is already running
    try:
        response = requests.get(f"http://localhost:{port}")
        if response.status_code == 200:
            print("Streamlit app is already running")
            yield None
            return
    except requests.exceptions.ConnectionError:
        print("Starting Streamlit app")
        
        # Start Streamlit app
        process = subprocess.Popen(
            ["streamlit", "run", "app.py"],
            cwd=str(Path(__file__).parent.parent.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for app to start
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{port}")
                if response.status_code == 200:
                    print("Streamlit app started successfully")
                    break
            except requests.exceptions.ConnectionError:
                if i == max_retries - 1:
                    raise Exception("Failed to start Streamlit app")
                time.sleep(1)
        
        yield process
        
        # Cleanup
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

@pytest.fixture(scope="session")
def test_db():
    """Create a test database with sample data."""
    db_path = Path(__file__).parent.parent / "test_letters.db"
    
    # Create a new test database
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS letters
                 (id INTEGER PRIMARY KEY,
                  date TEXT,
                  sender TEXT,
                  recipient TEXT,
                  description TEXT,
                  image_path TEXT)''')
    
    # Insert sample data
    sample_data = [
        (1, "1943-01-15", "John Doe", "Jane Doe", "Sample letter 1", "letter1.jpg"),
        (2, "1943-02-20", "Jane Doe", "John Doe", "Sample letter 2", "letter2.jpg"),
    ]
    c.executemany('INSERT INTO letters VALUES (?,?,?,?,?,?)', sample_data)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup after tests
    if db_path.exists():
        os.remove(db_path)

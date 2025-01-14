import os
import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import streamlit as st

# Get the path to the test database
TEST_DB_PATH = Path(__file__).parent / "test_letters.db"

@pytest.fixture(scope="session")
def test_db():
    """Create a test database with sample data."""
    # Create a new test database
    conn = sqlite3.connect(TEST_DB_PATH)
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
    
    yield TEST_DB_PATH
    
    # Cleanup after tests
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)

def mock_get_image(*args, **kwargs):
    """Mock function to replace get_image_from_gcs."""
    return None

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch('streamlit.expander') as mock_expander, \
         patch('streamlit.image') as mock_image, \
         patch('streamlit.text') as mock_text, \
         patch('app.get_image_from_gcs', side_effect=mock_get_image):
        
        # Create a MagicMock for the expander context
        expander_context = MagicMock()
        mock_expander.return_value.__enter__ = MagicMock(return_value=expander_context)
        mock_expander.return_value.__exit__ = MagicMock(return_value=None)
        
        yield {
            'expander': mock_expander,
            'image': mock_image,
            'text': mock_text,
            'expander_context': expander_context
        }

def test_letters_display(test_db, mock_streamlit):
    """Test that letters are displayed correctly."""
    import app
    
    # Set up environment variables
    os.environ['LETTERS_DB'] = str(test_db)
    os.environ['GCS_BUCKET_NAME'] = 'test-bucket'
    
    # Mock st.session_state
    with patch('streamlit.session_state', {'authenticated': True}):
        # Run the main function
        app.main()
        
        # Verify expanders were created for both letters
        assert mock_streamlit['expander'].call_count >= 2, "Expected at least 2 expanders"
        
        # Verify text was displayed
        text_calls = [call[0][0] for call in mock_streamlit['text'].call_args_list]
        assert any('Sample letter 1' in str(call) for call in text_calls)
        assert any('Sample letter 2' in str(call) for call in text_calls)
        
        # Verify dates were displayed
        assert any('1943-01-15' in str(call) for call in text_calls)
        assert any('1943-02-20' in str(call) for call in text_calls)

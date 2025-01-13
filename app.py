import streamlit as st
import sqlite3
from datetime import datetime
import os
from PIL import Image
import pandas as pd
import json
import time
import functools
import logging
import re

# Configure Streamlit page
st.set_page_config(
    page_title="Family Letters Archive",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern interface with vintage letter aesthetic
st.markdown("""
    <style>
    /* Global theme override */
    .stApp {
        background-color: #f5f5f0;
    }
    
    /* Header bar removal */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* Main content area */
    .main {
        padding: 2rem;
        background-color: #f5f5f0;
        color: #2c2c2c;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        width: 20rem !important;
        min-width: 20rem !important;
        background-color: #e8e8e0;
        border-right: 1px solid #d0d0c8;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Input fields styling */
    .stTextInput input, .stDateInput input {
        background-color: white !important;
        border: 1px solid #d0d0c8 !important;
        border-radius: 4px !important;
        color: #2c2c2c !important;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #f5f5f0 !important;
        color: #2c2c2c !important;
        border: 1px solid #d0d0c8 !important;
        border-radius: 4px !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        background-color: #e8e8e0 !important;
        border-color: #b0b0a8 !important;
    }
    
    /* Letter styling */
    .letter-content {
        background-color: #fff9f0;
        padding: 3rem;
        border-radius: 8px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        color: #2c2c2c;
        font-family: "Courier New", Courier, monospace;
        font-size: 1.1rem;
        line-height: 1.6;
        max-width: 100%;
        margin: 1.5rem 0;
        border: 1px solid #e0e0d8;
        white-space: pre-wrap;
    }
    
    /* Letter header styling */
    .letter-header {
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2c2c2c;
        margin-bottom: 2rem;
        border-bottom: 1px solid #d0d0c8;
        padding-bottom: 1rem;
    }
    
    .letter-date {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #fff !important;
        border: 1px solid #e0e0d8 !important;
        border-radius: 8px !important;
        color: #2c2c2c !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
        margin-bottom: 1rem !important;
        padding: 1rem !important;
    }
    
    /* Override Streamlit's default text colors */
    .stMarkdown, p, h1, h2, h3 {
        color: #2c2c2c !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Style the title */
    h1 {
        font-weight: 600 !important;
        font-size: 2rem !important;
        margin-bottom: 2rem !important;
        color: #1a1a1a !important;
    }
    
    /* Remove emoji icons */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Hide streamlit branding */
    #MainMenu, footer {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Add debug mode toggle to sidebar
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=False)

# Create a placeholder for debug logs in sidebar
if debug_mode:
    debug_log = st.sidebar.empty()
    
# Store timing information
timing_logs = []

def log_timing(message):
    if debug_mode:
        timing_logs.append(message)
        debug_log.write("\n".join(timing_logs))

def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        log_timing(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

@timer_decorator
def get_db_connection():
    conn = sqlite3.connect('letters.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_cached_image(path):
    """Get image from cache or load it"""
    # Initialize image cache in session state if it doesn't exist
    if 'image_cache' not in st.session_state:
        st.session_state.image_cache = {}
    
    if path not in st.session_state.image_cache:
        start_time = time.time()
        try:
            if not os.path.exists(path):
                st.error(f"Image file not found: {path}")
                return None
            image = Image.open(path)
            load_time = time.time() - start_time
            log_timing(f"Loading and caching image {os.path.basename(path)} took {load_time:.2f} seconds")
            st.session_state.image_cache[path] = image
        except Exception as e:
            st.error(f"Could not load scan: {path}\nError: {str(e)}")
            return None
    else:
        log_timing(f"Retrieved image {os.path.basename(path)} from cache")
    
    return st.session_state.image_cache[path]

@timer_decorator
def display_images(scan_paths_str):
    """Display images in a two-column layout"""
    if not scan_paths_str:
        return
        
    try:
        # Handle Python list string format instead of JSON
        scan_paths = eval(scan_paths_str)  # Safe here since we control the database content
        if scan_paths:
            st.markdown("### Original Scans")
            cols = st.columns(min(len(scan_paths), 2))
            for idx, scan_path in enumerate(scan_paths):
                col = cols[idx % 2]
                with col:
                    image = get_cached_image(scan_path)
                    if image:
                        st.image(image, caption=os.path.basename(scan_path), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading images: {e}")

@timer_decorator
def fetch_letters(query, params):
    """Fetch letters from database with timing"""
    start_time = time.time()
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    query_time = time.time() - start_time
    log_timing(f"SQL Query took {query_time:.2f} seconds, returned {len(df)} rows")
    conn.close()
    return df

@timer_decorator
def main():
    # Title without emoji
    st.title("Family Letters Archive")
    
    # Initialize database connection
    conn = get_db_connection()
    
    # Sidebar styling
    st.sidebar.markdown("""
        <style>
        .sidebar .sidebar-content {
            padding: 2rem 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.sidebar.title("Search and Filter")
    
    # Get min and max dates from database
    date_range = pd.read_sql_query(
        "SELECT MIN(date) as min_date, MAX(date) as max_date FROM letters",
        conn
    ).iloc[0]
    
    min_date = datetime.strptime(date_range['min_date'], '%Y-%m-%d')
    max_date = datetime.strptime(date_range['max_date'], '%Y-%m-%d')
    
    # Add search field without icon
    search_query = st.sidebar.text_input("Search letters", key="search_input")

    # Date range selection with better layout
    st.sidebar.markdown("### Date Range")
    start_date = st.sidebar.date_input("From", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.sidebar.date_input("To", min_value=min_date, max_value=max_date, value=max_date)

    try:
        # Validate date range
        if start_date > end_date:
            st.sidebar.error("Start date must be before end date")
            return

        # Modify query to include search
        query = """
            SELECT id, date, description, content, scan_paths
            FROM letters 
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        
        if search_query:
            query += " AND (content LIKE ? OR description LIKE ?)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])
            
        query += " ORDER BY date DESC"
        
        # Execute query and fetch results
        df = fetch_letters(query, params)
        
        # Display result count without emoji
        result_count = len(df)
        if search_query:
            st.markdown(f"### Found {result_count} {'letter' if result_count == 1 else 'letters'} matching '{search_query}'")
        else:
            st.markdown(f"### Showing {result_count} {'letter' if result_count == 1 else 'letters'}")

        # Helper function to highlight matching text
        def highlight_matches(text, search):
            if not search or not text:
                return text
            
            import re
            pattern = re.compile(f'({re.escape(search)})', re.IGNORECASE)
            return pattern.sub(r'**\1**', text)

        # Helper function to clean text content
        def clean_text_content(text):
            # Replace special quotes and dashes with standard characters
            text = text.replace('"', '"').replace('"', '"')
            text = text.replace(''', "'").replace(''', "'")
            text = text.replace('–', '-').replace('—', '-')
            # Fix common OCR issues with spaces
            text = re.sub(r'(\d+),(\d+)', r'\1,\2', text)  # Fix number formatting
            text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)  # Add space between letter and number
            # Remove any non-ASCII characters
            text = ''.join(char if ord(char) < 128 else ' ' for char in text)
            # Fix multiple spaces
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        # Display letter content with vintage styling
        for idx, row in df.iterrows():
            expander_key = f"show_images_{idx}"
            if expander_key not in st.session_state:
                st.session_state[expander_key] = False

            expander = st.expander(row['description'], expanded=True)
            
            with expander:
                start_time = time.time()
                
                # Clean the content
                cleaned_content = clean_text_content(row['content'])
                
                st.markdown(f"""
                    <div class="letter-content">
                        <div style="text-align: right; margin-bottom: 2rem; font-family: 'Courier New', Courier, monospace; color: #444;">
                            {row['date']}
                        </div>
                        <div style="margin-bottom: 2rem; font-family: 'Courier New', Courier, monospace;">
                            {highlight_matches(cleaned_content, search_query) if search_query else cleaned_content}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Original Letter button
                if not st.session_state[expander_key] and row['scan_paths']:
                    if st.button("Original Letter", key=f"load_btn_{idx}"):
                        st.session_state[expander_key] = True
                        st.rerun()
                
                # Only show images if they've been explicitly loaded
                if st.session_state[expander_key] and row['scan_paths']:
                    display_images(row['scan_paths'])
                
                render_time = time.time() - start_time
                log_timing(f"Rendering letter {idx} took {render_time:.2f} seconds")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

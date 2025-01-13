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

# Configure Streamlit page
st.set_page_config(
    page_title="Family Letters Archive",
    page_icon="📝",
    layout="wide"
)

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
    st.title("Family Letters Archive")
    
    # Sidebar filters
    st.sidebar.header("Search and Filter")
    
    # Get min and max dates from database
    conn = get_db_connection()
    date_range = pd.read_sql_query(
        "SELECT MIN(date) as min_date, MAX(date) as max_date FROM letters",
        conn
    ).iloc[0]
    
    min_date = datetime.strptime(date_range['min_date'], '%Y-%m-%d')
    max_date = datetime.strptime(date_range['max_date'], '%Y-%m-%d')
    
    # Add search field
    search_query = st.sidebar.text_input("Search letters", key="search_input")

    # Date range selection
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
    with col2:
        end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

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
        
        # Display result count
        result_count = len(df)
        if search_query:
            st.write(f"Found {result_count} {'letter' if result_count == 1 else 'letters'} matching '{search_query}'")
        else:
            st.write(f"Showing {result_count} {'letter' if result_count == 1 else 'letters'}")

        # Helper function to highlight matching text
        def highlight_matches(text, search):
            if not search or not text:
                return text
            
            import re
            pattern = re.compile(f'({re.escape(search)})', re.IGNORECASE)
            return pattern.sub(r'**\1**', text)

        # Display letters with timing
        for idx, row in df.iterrows():
            expander_key = f"letter_{idx}"
            
            # Initialize expander state if not exists
            if expander_key not in st.session_state:
                st.session_state[expander_key] = False
            
            # Create expander
            expander = st.expander(f"{row['date']} - {row['description']}", expanded=False)
            
            with expander:
                start_time = time.time()
                
                # Display letter content with highlighting
                st.markdown("### Letter Content")
                if search_query:
                    highlighted_content = highlight_matches(row['content'], search_query)
                    st.markdown(highlighted_content)
                else:
                    st.write(row['content'])
                
                # Add a button to trigger image loading
                if not st.session_state[expander_key] and row['scan_paths']:
                    if st.button("Load Images", key=f"load_btn_{idx}"):
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

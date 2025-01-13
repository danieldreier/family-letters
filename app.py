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
def fetch_letters(conn, query, params):
    """Fetch letters from database with timing"""
    start_time = time.time()
    df = pd.read_sql_query(query, conn, params=params)
    query_time = time.time() - start_time
    log_timing(f"SQL Query took {query_time:.2f} seconds, returned {len(df)} rows")
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
    
    # Date range filter with database min/max dates
    try:
        start_date = st.sidebar.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="start_date"
        )
        
        end_date = st.sidebar.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="end_date"
        )
            
        # Ensure start_date is not after end_date
        if start_date > end_date:
            st.sidebar.error("Start date must be before end date")
            date_min = min_date
            date_max = max_date
        else:
            date_min = start_date
            date_max = end_date
            
    except Exception as e:
        st.sidebar.error(f"Date selection error: {e}")
        date_min = min_date
        date_max = max_date
    
    # Text search
    search_query = st.sidebar.text_input("Search in letters:", "")
    
    try:
        # Build query based on filters
        query = """
        SELECT * FROM letters 
        WHERE strftime('%Y-%m-%d', date) >= ? 
        AND strftime('%Y-%m-%d', date) <= ?
        """
        params = [date_min.strftime('%Y-%m-%d'), date_max.strftime('%Y-%m-%d')]
        
        if search_query:
            query += " AND (content LIKE ? OR description LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
            
        query += " ORDER BY date DESC"
        
        # Debug information
        st.sidebar.write("Debug Info:")
        st.sidebar.write(f"Date range: {date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}")
        
        # Execute query with timing
        df = fetch_letters(conn, query, params)
        
        # Display results count
        st.write(f"Found {len(df)} letters")
        
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
                
                # Display letter content
                st.markdown("### Letter Content")
                st.write(row['content'])
                
                # Add a button to trigger image loading
                if not st.session_state[expander_key] and row['scan_paths']:
                    if st.button("Load Images", key=f"load_btn_{idx}"):
                        st.session_state[expander_key] = True
                        st.rerun()
                
                # Only show images if they've been explicitly loaded
                if st.session_state[expander_key] and row['scan_paths']:
                    st.markdown("### Original Scans")
                    display_images(row['scan_paths'])
                
                render_time = time.time() - start_time
                log_timing(f"Rendering letter {idx} took {render_time:.2f} seconds")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

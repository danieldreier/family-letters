import streamlit as st
import sqlite3
from datetime import datetime
import os
from PIL import Image
import pandas as pd
import json

# Configure Streamlit page
st.set_page_config(
    page_title="Family Letters Archive",
    page_icon="📝",
    layout="wide"
)

def get_db_connection():
    conn = sqlite3.connect('letters.db')
    conn.row_factory = sqlite3.Row
    return conn

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
                    try:
                        if not os.path.exists(scan_path):
                            st.error(f"Image file not found: {scan_path}")
                            continue
                            
                        image = Image.open(scan_path)
                        st.image(image, caption=os.path.basename(scan_path), use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not load scan: {scan_path}\nError: {str(e)}")
    except Exception as e:
        st.error(f"Error loading images: {e}")

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
        dates = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range"
        )
        
        # Handle both single date and date range selections
        if isinstance(dates, tuple):
            date_min, date_max = dates
        else:
            date_min = date_max = dates
            
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
        
        df = pd.read_sql_query(query, conn, params=params)
        
        if len(df) == 0:
            st.info("No letters found matching your criteria.")
        else:
            st.write(f"Found {len(df)} letters")
            
            # Display letters
            for _, letter in df.iterrows():
                with st.expander(f"{letter['date']} - {letter['description']}", expanded=False):
                    # Display letter content
                    st.markdown("### Letter Content")
                    st.write(letter['content'])
                    
                    # Display images
                    if letter['scan_paths']:
                        display_images(letter['scan_paths'])
    
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

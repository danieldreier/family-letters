import sqlite3
import os
from datetime import datetime
import re
from pathlib import Path
import json

def init_db():
    # Create database and tables
    conn = sqlite3.connect('letters.db')
    c = conn.cursor()
    
    # Create letters table
    c.execute('''
        CREATE TABLE IF NOT EXISTS letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            description TEXT NOT NULL,
            content TEXT NOT NULL,
            scan_paths TEXT,  -- JSON array of image paths
            text_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create full-text search index
    c.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS letters_fts USING fts5(
            content,
            description,
            date,
            content='letters',
            content_rowid='id'
        )
    ''')
    
    conn.commit()
    conn.close()

def get_base_filename(filename):
    """Extract the base part of the filename without page numbers and extension."""
    # Remove page numbers like "- Page 1 of 2" or "- Pg 1 of 2"
    base = re.sub(r'\s*-\s*(?:Page|Pg)\s*\d+\s*of\s*\d+.*$', '', filename)
    # Remove extension
    base = os.path.splitext(base)[0]
    return base

def find_matching_images(base_name, scan_dir):
    """Find all image files that match the base name of the text file."""
    matching_images = []
    for image_file in os.listdir(scan_dir):
        if image_file.lower().endswith('.png'):
            image_base = get_base_filename(image_file)
            if image_base.startswith(base_name):
                matching_images.append(os.path.join(scan_dir, image_file))
    return sorted(matching_images)  # Sort to maintain page order

def parse_date(filename):
    """Extract date from filename, handling both YYYY-MM-DD and YYYY-MM formats."""
    date_match = re.match(r'^(\d{4}-\d{2}(?:-\d{2})?)', filename)
    if not date_match:
        return None
    
    date_str = date_match.group(1)
    if len(date_str) == 7:  # YYYY-MM format
        date_str += "-01"  # Default to first day of month
    return date_str

def extract_description(filename):
    """Extract description from filename, cleaning up common patterns."""
    # Remove date pattern from start
    desc = re.sub(r'^\d{4}-\d{2}(?:-\d{2})?\s*', '', filename)
    # Remove extension
    desc = os.path.splitext(desc)[0]
    # Remove page numbers if present
    desc = re.sub(r'\s*-\s*(?:Page|Pg)\s*\d+\s*of\s*\d+.*$', '', desc)
    return desc.strip()

def import_letters(text_dir, scan_dir):
    conn = sqlite3.connect('letters.db')
    c = conn.cursor()
    
    imported_count = 0
    error_count = 0
    
    for filename in os.listdir(text_dir):
        if not filename.endswith('.txt'):
            continue
            
        try:
            # Parse date
            letter_date = parse_date(filename)
            if not letter_date:
                print(f"Warning: Could not parse date from {filename}")
                error_count += 1
                continue
            
            # Get description
            description = extract_description(filename)
            
            # Find matching image files
            base_name = get_base_filename(filename)
            matching_images = find_matching_images(base_name, scan_dir)
            
            # Read letter content
            with open(os.path.join(text_dir, filename), 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Store image paths as proper JSON
            scan_paths = json.dumps(matching_images) if matching_images else None
            
            # Insert into database
            c.execute('''
                INSERT INTO letters (date, description, content, scan_paths, text_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (letter_date, description, content, scan_paths, os.path.join(text_dir, filename)))
            
            # Update FTS index
            c.execute('''
                INSERT INTO letters_fts(rowid, content, description, date)
                VALUES (last_insert_rowid(), ?, ?, ?)
            ''', (content, description, letter_date))
            
            imported_count += 1
            print(f"Imported: {filename}")
            
        except Exception as e:
            print(f"Error importing {filename}: {str(e)}")
            error_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\nImport completed:")
    print(f"Successfully imported: {imported_count} letters")
    print(f"Errors: {error_count}")

if __name__ == "__main__":
    init_db()
    # Default paths based on repository structure
    text_dir = os.path.join(os.path.dirname(__file__), "dataset/text/final")
    scan_dir = os.path.join(os.path.dirname(__file__), "dataset/originals")
    
    if os.path.exists(text_dir) and os.path.exists(scan_dir):
        print(f"Importing letters from {text_dir}")
        import_letters(text_dir, scan_dir)
    else:
        print("Please specify valid paths to text and scan directories")

# Family Letters Archive

A Streamlit-based web application for viewing and searching family letters dating back to the 1950s. The application provides a searchable interface for both OCR'd text and original scanned documents.

## Features

- Date range filtering
- Full-text search capabilities
- Authentication system for family members
- View both OCR text and original scanned documents
- SQLite database for efficient storage and retrieval

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python init_db.py
```

3. Set up environment variables:
Create a `.env` file with:
```
APP_PASSWORD=your_chosen_password
```

4. Run the application:
```bash
streamlit run app.py
```

## Project Structure

- `app.py`: Main Streamlit application
- `init_db.py`: Database initialization and data import scripts
- `requirements.txt`: Python dependencies
- `letters.db`: SQLite database (created after initialization)

## Data Import

To import your letters, modify the paths in `init_db.py` to point to your text and scan directories, then run the script.

## Deployment

This application can be deployed to Vercel using their Python runtime. Follow Vercel's documentation for Streamlit deployment.

## Future Enhancements

- LLM-powered natural language querying of the letter dataset
- Enhanced search capabilities
- Additional metadata and filtering options

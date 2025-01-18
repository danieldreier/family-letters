# Family Letters Archive

A Streamlit-based web application for viewing and searching family letters. The application provides a searchable interface for both OCR'd text and original scanned documents.

## Currently Implemented

- Date range filtering
- Full-text search capabilities using SQLite FTS
- Rudimentary authentication (just a password for now)
- View both OCR text and original scanned documents
- SQLite database

## Development Setup

1. **Prerequisites**
   - Python 3.12 or higher
   - pip
   - virtualenv

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Install main dependencies
   venv/bin/pip install -r requirements.txt
   
   # Install test dependencies (if you plan to run tests)
   venv/bin/pip install -r requirements-test.txt
   ```

4. **Initialize the database**:
   Put data files in the `dataset/` directory. 
    - Text files must be in `dataset/text/final/`
    - Image files must be in `dataset/originals/`
    - Filenames should start with a date in `YYYY-MM-DD` or `YYYY-MM` format
    - For multi-page scans, use ` - Page X of Y` suffix
    - Text and image files should have matching base names (excluding page numbers)
    - For the Google Drive dataset we're using, just put the whole thing in `dataset/`

   ```bash
   python init_db.py #import data into sqlite
   ```

3. Set up environment variables:
   Create a `.env` file with:
   ```
   APP_PASSWORD=your_chosen_password
   LETTERS_DB=letters.db
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```
   The app will be available at http://localhost:8501

## Project Structure

```
family-letters-archive/
├── app.py                 # Main Streamlit application
├── init_db.py            # Database initialization
├── letters.db            # SQLite database
├── requirements.txt      # Production dependencies
├── requirements-test.txt # Test dependencies
├── streamlit_theme.toml  # Streamlit theme configuration
├── .streamlit/          # Streamlit configuration
├── dataset/            # Sample data directory
├── tests/             # Test suite
│   ├── ui/           # UI/Integration tests
│   ├── test-results/ # Test screenshots
│   └── test_letters.db  # Test database
└── deploy/           # Deployment configuration
```

## Testing

1. **Run the test suite**:
   ```bash
   venv/bin/pytest
   ```

2. **UI Tests**:
   The project uses Playwright for UI testing. Tests will run in headless mode by default.
   ```bash
   venv/bin/pytest tests/ui/
   ```
   
   Test results and screenshots are saved in `tests/test-results/`.

## Local Development Workflow

1. Make your changes in a new branch
2. Run the test suite to ensure nothing is broken
3. Update or add tests for new features
4. Submit a pull request

## Deployment

See [BUILD.md](BUILD.md) for detailed deployment instructions to Google Cloud Platform.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (`venv/bin/pytest`)
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Database Initialization Fails**
   - Ensure you have write permissions in the project directory
   - Check that the sample data exists in the dataset directory

2. **Tests Fail**
   - Verify all test dependencies are installed
   - Check test screenshots in tests/test-results/
   - Ensure Streamlit is running on port 8502 for UI tests

3. **Streamlit App Issues**
   - Check .env file exists with correct variables
   - Verify database path is correct
   - Ensure all dependencies are installed in the virtualenv

For deployment issues, see the troubleshooting section in [BUILD.md](BUILD.md).

## Future Enhancements

- LLM-powered natural language querying of the letter dataset
- Enhanced search capabilities
- Additional metadata and filtering options

# Testing Documentation

This directory contains the test suite for the Family Letters Archive application.

## Structure

```
tests/
├── ui/                    # UI tests using Playwright
│   ├── conftest.py       # Test fixtures and configuration
│   └── test_letters.py   # Letter-related UI tests
└── README.md             # This file
```

## Setup

1. Install test dependencies:
```bash
pip install -r requirements-test.txt
playwright install  # Install browser binaries
```

2. Run the tests:
```bash
# Run all tests
pytest

# Run only UI tests
pytest tests/ui

# Run smoke tests
pytest -m smoke

# Run tests in parallel (4 workers)
pytest -n 4

# Run with video recording
pytest --video=on
```

## Writing Tests

- Use the `@pytest.mark.ui` decorator for UI tests
- Use the `@pytest.mark.smoke` decorator for smoke tests
- Use the `@pytest.mark.slow` decorator for slow tests

## CI/CD

Tests are automatically run on GitHub Actions:
- On every push to main
- On every pull request
- Test artifacts (screenshots, videos) are uploaded automatically

## Debugging

- Add `--headed` to run tests in visible browser
- Add `--slowmo 1000` to slow down test execution
- Add `--video=on` to record test videos
- Screenshots are automatically captured on test failures

## Best Practices

1. Keep tests independent
2. Use appropriate markers
3. Write descriptive test names
4. Use page fixtures for common operations
5. Handle authentication in fixtures
6. Use explicit waits instead of sleep

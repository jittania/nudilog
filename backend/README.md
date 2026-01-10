```
    # Navigate to backend directory
    cd /Users/jittaniasmith/Developer/Personal_Projects/nudilog/backend

    # Create virtual environment
    python3 -m venv .venv

    # Activate virtual environment
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt

    # Run uvicorn
    uvicorn app.main:app --reload

    # Open http://localhost:8000/docs in your browser.
```
---

## Implementation Overview

- Uses SQLModel with SQLite (nudilog.db in the backend directory)
- Creates tables on startup
- Includes SightingCreate (no id) and SightingRead (with id) schemas
- Implements all three endpoints with proper error handling
- The database file will be created automatically when you start the server.
# Running Backend Locally

Create virtual environment
`python3 -m venv .venv`
`source .venv/bin/activate`

Install dependencies
`pip install -r requirements.txt`

Run uvicorn
`uvicorn app.main:app --reload`
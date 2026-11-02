# BlogSpace — Blogging Platform with Flask

A beginner-friendly internship project with registration, login, blog post CRUD, comments, search and category filtering.

## Run on Windows

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Open Terminal in VS Code and run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

4. Open http://127.0.0.1:5000 in your browser.

If PowerShell blocks activation, run this once in the same terminal:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
Then activate the environment again.

## Features
- User registration and login with hashed passwords
- Create, read, update and delete your own posts
- Comments for signed-in users
- Search by title/content and filter by category
- SQLite database created automatically

## Important before public deployment
Change `SECRET_KEY` in `app.py` to a long random secret. Turn off `debug=True`. Add CSRF protection, rate limiting, production hosting configuration and review security before using real user data. This starter is intended for learning and internship demonstration.

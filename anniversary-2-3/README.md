# Our Story ♡ — Anniversary Website

## How to run

1. Make sure Python 3.8+ is installed
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Start the server:
   ```
   python app.py
   ```
   Or just double-click / run: `./run.sh`

4. Open **http://localhost:5555** in your browser

## What's inside

| File | Purpose |
|------|---------|
| `app.py` | Flask backend — REST API + SQLite DB |
| `templates/index.html` | The full frontend |
| `anniversary.db` | SQLite database (auto-created) |
| `static/uploads/` | Uploaded photos (auto-created) |

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/hugs | List all hugs |
| POST | /api/hugs | Add a hug (multipart: date, memory, image?) |
| DELETE | /api/hugs/:id | Remove a hug |
| GET | /api/memories | List all memories |
| POST | /api/memories | Add a memory (multipart: date, tag, text, image?) |
| DELETE | /api/memories/:id | Remove a memory |
| GET | /api/milestones | List all milestones |
| POST | /api/milestones | Add a milestone (JSON: date, label, note, emoji, type) |
| DELETE | /api/milestones/:id | Remove a milestone |

## Features
- Upload real photos — stored on disk, auto-resized to max 1200px
- Data persists forever in SQLite (survives restarts)
- Works on any machine with Python

Made with ♡

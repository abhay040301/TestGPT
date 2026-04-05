# TestGPT v2.0 — Setup & Integration Guide

## Project Structure
```
your-project/
├── App.py               ← Main application
├── requirements.txt     ← Python dependencies
└── assets/
    ├── styles.css       ← Design system (auto-loaded by Dash)
    └── Logo.png         ← Your logo (copy from uploads)
```

## 1. Local Setup

### Prerequisites
- Python 3.10+
- OpenAI API Key

### Install dependencies
```bash
pip install -r requirements.txt
```

### Set your OpenAI key
```bash
# Linux / Mac
export OPENAI_API_KEY="sk-..."

# Windows CMD
set OPENAI_API_KEY=sk-...

# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."
```

### Run the app
```bash
python App.py
# Open http://localhost:8051
```

---

## 2. Deploy to Production

### Option A — Render.com (free tier)
1. Push your project folder to GitHub
2. Go to https://render.com → New Web Service
3. Connect your repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn App:server -b 0.0.0.0:8051`
   - **Environment Variable:** `OPENAI_API_KEY = sk-...`

### Option B — Railway.app
1. `railway login` then `railway init`
2. Add env var: `OPENAI_API_KEY`
3. `railway up`

### Option C — Heroku
```bash
echo "web: gunicorn App:server" > Procfile
heroku create testgpt-app
heroku config:set OPENAI_API_KEY=sk-...
git push heroku main
```

---

## 3. Integrate into VS Code / Cursor Editor

### a) Open as workspace
```bash
code your-project/
```

### b) Install the Python extension
Extensions → search "Python" → install Microsoft Python Extension

### c) Select interpreter
`Ctrl+Shift+P` → "Python: Select Interpreter" → pick your venv

### d) Run & Debug
- Open `App.py`
- Press `F5` → select "Python File"
- App starts at `http://localhost:8051`
- The Dash debug toolbar appears at bottom-right for hot-reload

### e) Auto-reload during development
Change `debug=False` → `debug=True` in `App.py`:
```python
app.run(debug=True, port=8051)
```
Now every file save auto-reloads the app.

---

## 4. App Flow

```
Page 1 (Home)       → Overview & stats
Page 2 (/generate)  → Upload PRD → Generate test cases → Download Excel/CSV
Page 3 (/execute)   → Enter URL or upload APK → Generate Scripts → Execute → View progress  
Page 4 (/report)    → Full pass/fail report → Download PDF
```

## 5. Notes

- **Real Selenium/Appium**: The app currently uses AI-simulated execution.
  To run real tests, install `selenium` / `appium-python-client` and replace
  `simulate_execution()` with actual `pytest` subprocess calls.
- **Session state**: Uses `dcc.Store(storage_type="session")` — data persists
  within a browser tab but resets on refresh. For multi-user production,
  replace with Redis + Flask sessions.
- **PDF export** uses ReportLab — no external services needed.

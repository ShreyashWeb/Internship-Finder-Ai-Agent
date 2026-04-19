# Auto Internship Hunter Agent

A functional internship agent that:
- Takes your skills/profile
- Pulls internships from API + RSS sources
- Filters and ranks relevant opportunities
- Explains fit with score breakdown, priority labels, and missing skill gaps
- Builds a practical 7-day action plan from your top opportunities
- Creates a daily application calendar with status tracking (planned, in progress, applied, skipped)
- Generates tailored artifacts:
  - Resume bullet points
  - Cover letters
  - Outreach emails
  - Interview prep notes

## Stack
- Python
- SQLite
- Typer CLI
- Streamlit UI
- OpenAI API (with fallback mode if key is missing)
- APScheduler for daily automation

## Quick Start

1. Create virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure environment:

```powershell
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env` for AI generation.

3. Save your profile:

```powershell
python -m src.interfaces.cli profile
```

4. Run a fetch + rank cycle:

```powershell
python -m src.interfaces.cli run
```

5. Start web app:

```powershell
streamlit run src/interfaces/web_app.py
```

## CLI Commands
- `python -m src.interfaces.cli profile`
- `python -m src.interfaces.cli run`
- `python -m src.interfaces.cli list-jobs --limit 10`
- `python -m src.interfaces.cli insights --limit 20`
- `python -m src.interfaces.cli generate --job-url "<url>" --artifact-type cover_letter`
- `python -m src.interfaces.cli plan-build --days 7 --per-day 3`
- `python -m src.interfaces.cli plan-today`
- `python -m src.interfaces.cli plan-update --item-id 1 --status applied --notes "Submitted via careers page"`
- `python -m src.interfaces.cli schedule`

## Notes
- The app is legal-first by default (API/RSS only).
- If OpenAI key is not set, generation falls back to structured template output.
- Scheduler uses `SCHEDULE_TIME` from `.env` (format: `HH:MM`).

## Run Tests

```powershell
pytest -q
```

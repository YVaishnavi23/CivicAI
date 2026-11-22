# CivicFlow AI

Civic-issue triage prototype. A citizen reports a problem, the app structures it (LLM if configured, labelled rules otherwise), flags possibly related reports, explains a priority score, suggests a first action, and lets the citizen track status by reference ID. Nothing is sent to any government body. See `spec.md` for the full product and technical specification.

## Run locally

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate      # optional
pip install -r requirements.txt
python app.py                                            # http://127.0.0.1:8000
# or: uvicorn app:app --reload --port 8000
```

Open <http://127.0.0.1:8000>. The database (`civicflow.db`) and `uploads/` are created on first start.

**Quick demo:** Authority desk, then Load demo scenario. Two differently worded school-gate pothole reports are grouped, one garbage report stays separate. Copy a pothole ID, open Track report, change its status on the desk, then look it up again.

### Optional: live AI assessment

```bash
export AI_API_KEY=sk-...                # or OPENAI_API_KEY
export AI_MODEL=gpt-4o-mini             # optional
export AI_BASE_URL=https://api.openai.com/v1/chat/completions   # any OpenAI-compatible endpoint
python app.py
```

Without a key, or if the call fails or returns an unusable answer, the record is stored as `rules_fallback` and the UI says so. The model never sets the score; priority is always computed locally.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q                                # 21 API/pipeline tests, no network or key needed

# optional browser end-to-end run (starts its own server on port 8011)
pip install playwright && playwright install chromium
python tests/e2e_browser.py
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AI_API_KEY` / `OPENAI_API_KEY` | none | Enables LLM assessment |
| `AI_BASE_URL` | `https://api.openai.com/v1/chat/completions` | Chat Completions endpoint |
| `AI_MODEL` | `gpt-4o-mini` | Model name |
| `DATABASE_PATH` | `./civicflow.db` | SQLite file |
| `UPLOAD_DIR` | `./uploads` | Photo folder (added beyond the spec) |
| `PORT` | `8000` | Used by `python app.py`; hosts like Render pass `$PORT` to uvicorn |

`.env.example` is documentation only; `.env` files are not loaded.

## Deployment (Render)

1. Push this folder to a Git repository.
2. Create a Web Service (or use `render.yaml` as a Blueprint). Build: `pip install -r requirements.txt`. Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
3. Attach a persistent disk at `/var/data` and set `DATABASE_PATH=/var/data/civicflow.db` and `UPLOAD_DIR=/var/data/uploads`. Without a disk, data is lost on restart or redeploy.
4. Optionally set `AI_API_KEY` in the dashboard.
5. Smoke test from an outside browser: `/health`, submit a report, track it, change status on the desk, track again.

`render.yaml` and these steps have **not** been run from the development environment; deployment still needs to be done and smoke-tested by you. Do not expose this build publicly with real citizen data: the desk and demo routes have no authentication.

## Project layout

```
civicflow/
├── app.py               FastAPI app, routes, pipeline orchestration, serializers
├── ai.py                LLM call, response validation, rules fallback, evidence detection
├── scoring.py           Transparent priority heuristic and department mapping
├── matching.py          Unicode tokenising and Jaccard related-report matching
├── db.py                SQLite schema and connections
├── static/
│   ├── index.html       Three views: report, track, authority desk
│   ├── style.css
│   ├── app.js           UI logic (DOM built with textContent, no innerHTML)
│   └── i18n.js          English, Telugu, Hindi interface strings
├── tests/
│   ├── conftest.py
│   ├── test_api.py      pytest suite
│   └── e2e_browser.py   Playwright end-to-end script (optional)
├── spec.md              Product and technical specification (+ implementation notes, section 25)
├── requirements.txt / requirements-dev.txt
├── .env.example  .gitignore  render.yaml
└── uploads/             Stored photos (git-ignored)
```
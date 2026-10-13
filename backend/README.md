# VanMitra Module 4: backend (slice 1)

FastAPI service for the livelihood report. Same stack as the host (`vanMitraAI/vanmitra_backend`):
Python 3.12, FastAPI, Pydantic v2, Shapely + pyproj; MongoDB arrives in slice 2.

**Slice 1 has no database and no login.** It contains the pure rules, the geo maths and a
stateless demo route that builds a report from a bundled **SAMPLE** dataset (synthetic data, labelled).

```bash
py -3.12 -m venv venv
./venv/Scripts/python -m pip install -r requirements-dev.txt

./venv/Scripts/python -m pytest                       # 60 tests
./venv/Scripts/ruff check app tests scripts
./venv/Scripts/mypy app scripts

./venv/Scripts/python -m uvicorn app.main:app --port 8010
# http://localhost:8010/docs
```

| Route | What |
|---|---|
| `GET /api/v1/health` | liveness |
| `GET /api/v1/livelihood/meta` | form vocabularies, radius limits, which dataset is loaded |
| `POST /api/v1/livelihood/demo/report` | full report for the details given, from the SAMPLE dataset; stores nothing |

Try it: `POST /demo/report` with `{}` gives a village report; with a `profile` (land, `livestock`, `assets`, a `location` pin near `19.7805, 73.2210`) it gives a plot report.

Layout: `app/livelihood/{schemas,service,geo,router}.py`, `domain/` (pure rules), `seed/` (ideas, sample data).
Regenerate the sample data: `python scripts/make_sample_dataset.py`. Export a report for the app: `python scripts/export_sample_report.py <out.json>`.

Plan and contract: `../docs/BACKEND_PLAN.md` (§6 is the report shape the app builds against).

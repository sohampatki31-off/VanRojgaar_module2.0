# VanMitra Module 4: backend

FastAPI service for the livelihood report. Same stack as the host (`vanMitraAI/vanmitra_backend`):
Python 3.12, FastAPI, Pydantic v2, Shapely + pyproj, pymongo, host-compatible JWT login.

What exists now (modules 1 to 3):

| Module | What |
|---|---|
| 1 | The pure rules (labels, gates, ranking, wildlife badge, analysis), exact geo distance, `build_report`, the draft idea library, a labelled **SAMPLE** dataset |
| 2 | Login (host token format), owner-only profile storage: `PUT/GET/DELETE /profile` |
| 3 | `POST /report`, `GET /report/latest`, `POST /resources/nearby`, saved reports (deleted with his answers), the resource-file validator and the load scripts |

Storage is `memory` by default (nothing persists; serves the bundled SAMPLE dataset), or `mongo`.
**Claude has not run anything against a real database**: the Mongo code is tested only for its pure
parts. Run `scripts/smoke_mongo.py` against a throwaway database before trusting it.

```bash
py -3.12 -m venv venv
./venv/Scripts/python -m pip install -r requirements-dev.txt
copy .env.example .env

./venv/Scripts/python -m pytest                      # 141 tests, no database needed
./venv/Scripts/ruff check app tests scripts
./venv/Scripts/mypy app scripts

./venv/Scripts/python -m uvicorn app.main:app --port 8010      # http://localhost:8010/docs
./venv/Scripts/python scripts/dev_token.py                      # a dev login token (dev users on)
```

Try it (dev users on, memory store): send `Authorization: Bearer <token from dev_token.py>`.

| Route | What |
|---|---|
| `GET /api/v1/health` | liveness |
| `GET /api/v1/livelihood/meta` | form vocabularies, radius limits, dataset in use |
| `PUT /livelihood/profile` | save his details (replaces, never merges). His village comes from his login |
| `GET /livelihood/profile` | his saved details (404 `livelihood.no_profile`) |
| `DELETE /livelihood/profile` | delete his answers **and his saved reports** |
| `POST /livelihood/report` | build his report now from his saved details, keep it, return it |
| `GET /livelihood/report/latest` | his latest report as made; flags `newer_version_available` |
| `POST /livelihood/resources/nearby` | labelled resources near any point, no ideas, nothing saved |
| `POST /livelihood/demo/report` | stateless SAMPLE report, **no login**; off unless `VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS=true` |

## Scripts

| Script | Writes to a database? | What |
|---|---|---|
| `dev_token.py` | no | mint a dev login token |
| `make_sample_dataset.py`, `export_sample_report.py` | no (files only) | regenerate the SAMPLE data; export a report for the app |
| `load_livelihood_resources.py FILE` | **only with `--apply`** | validate a resource GeoJSON (default), then load it. Never deletes |
| `setup_livelihood_indexes.py` | **only with `--apply`** | create the `lv_*` indexes |
| `seed_livelihood.py` | **only with `--apply`** | upsert the draft ideas, the demo village and the SAMPLE scheme rows |
| `eval_ask_ai.py` | no (writes `eval_out/`) | the gate for the AI step: 30 questions x 3 languages. **`--run` calls the real model and spends money**; without it, a dry run |
| `smoke_mongo.py` | **only with `--apply`**, and only for a database named `*_test` | profile round trip through `MongoStore` |

`[USER RUNS]`: every script that writes defaults to a dry run. Plan and contract: `../docs/BACKEND_PLAN.md`.

## Ask about your report, and the AI step

`POST /api/v1/livelihood/ask`, `GET/DELETE /ask/history`. The safety check, the report-only answer and the number check are plain code (`app/livelihood/domain/ask_*.py`) and need no model.

The AI step is **off by default**. To use it: `pip install -r requirements-ai.txt`, then in `.env` set `VANMITRA_ANTHROPIC_API_KEY`, optionally `VANMITRA_LIVELIHOOD_AI_MODEL` (default `claude-opus-5-5`), `..._AI_EFFORT` (`low`), `..._AI_DAILY_LIMIT` (20 per person per day), and run `python scripts/eval_ask_ai.py --run` **before** setting `VANMITRA_LIVELIHOOD_AI_ENABLED=true`. How it is built and what it is not allowed to do: `../docs/to_do.md` (the AI agent) and the module notes in `app/livelihood/ai.py`.

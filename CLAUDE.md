# CLAUDE.md — VanMitra Module 4 (VanRozgar)

Working rules for AI-assisted sessions in this folder. Humans: start at [README.md](README.md).

## What this project is
Module 4 of VanMitra: a personal **livelihood report** for one landowner (land, livestock, owned resources → resources within **5 km** → analysis and ranked ideas). Plan: `docs/`. Scope source: `VanMitra Module 4 Implementation Plan (1).pdf`. Host app (same stack, **read it before coding**): `C:\Soham\college work\vanMitraAI`.

## Stack (follow the host, not the PDF, where they differ)
- Flutter + **Riverpod** + **Hive**; **named routes** via `AppRouter`; strings via `AppLocalizations` / `context.tr`; theme via `AppColors` / `context.colors`. No `go_router`, no ARB.
- **FastAPI** + Pydantic v2; DB is **MongoDB** (`app/mongo.py` `Store`, `2dsphere`), **not PostgreSQL**; Shapely + pyproj for geo; JWT phone+PIN auth.
- Code goes in isolated folders: `lib/features/livelihood/` and `app/livelihood/`. Do not edit unrelated host files. See `docs/INTEGRATION.md`.

## Rules that must never break (full list: `docs/PROJECT_PLAN.md` §3)
1. No false data: every result has source, source date, check status; demo data is labelled **Sample**.
2. Suggestion only; community forest → "Use only through the Gram Sabha".
3. Never suggest anything that harms wildlife; the four legal gates run first; wildlife-risk badge on every idea.
4. **No numeric scores in the UI** (labels only). 0.5 for missing data, shown as "Not yet checked on the ground".
5. User data is private: no caste, no income, no ID numbers; deletable; never used for claims.
6. Read-only on claims, titles, boundaries.
7. Three languages, nothing hard-coded, no clipped Devanagari. Marathi/Hindi text is a **draft until a native speaker reviews it**.
8. Logic and keys live on the server; reasons travel as `{key, params}`, not finished text.

## Operating rules for Claude (organisation policy)
- **Do not run any create/update/delete or schema operations against a database.** That includes seeding, loading, `setup_mongo`, index creation, migrations. Write the script or command, label it `[USER RUNS]`, and hand it to the user. `SELECT`/read-only queries are allowed.
- **Do not ssh or log in to any other machine/server** from Claude Code.
- **Do not run commands that change network settings.**
- Do not commit, push, or open PRs unless asked. Never commit `.env`, keys, `google-services.json`, or personal data.

## Conventions
- Domain rules are **pure functions** in `domain/` (no DB, no HTTP) with unit tests; DB tests only against a throwaway database.
- Weights, bands, radius live in config (`domain/config.py` / `lv_config`), not scattered constants.
- Radius default **5000 m**, server cap 10000 m. Exact distance computed in a local azimuthal-equidistant projection; the database only finds candidates (`$geoIntersects` with a circumscribed circle polygon).
- Commands: Flutter `flutter analyze`, `flutter test`; backend `ruff check`, `ruff format --check`, `mypy app scripts`, `pytest -q`.

## Working prompt (how to run a session here)

> You are building VanMitra Module 4. Work branch by branch: **`backend`** → **`frontend`** → **`integration`**. Finish **one slice of backend** (tests green), commit and push it, then build **the matching slice of frontend** against the same report contract (`docs/BACKEND_PLAN.md` §6), commit and push, then **stop and report**. Never push to `main`; never merge `integration` without being asked. Before each slice, re-read the rules above and `docs/OPEN_QUESTIONS.md`. Use the skills below at the step named; skip a skill that does not fit the stack and say why.

| Step | Skill | Use it for |
|---|---|---|
| Plan a slice | `claude-mem:make-plan`, `claude-mem:mem-search` | Break the slice into phases; check earlier decisions first |
| Read the host app | `claude-mem:smart-explore`, `claude-mem:learn-codebase` | Structure of `vanMitraAI` without reading every file |
| Backend design | `claude-api` *(only for the Phase 4 Ask box)* | Claude API usage, model ids, caching, number-check design |
| Backend review | `code-review`, `simplify`, `security-review` | After each backend slice: correctness, reuse, privacy (L8) |
| Frontend look and feel | `ui-ux-pro-max:ui-ux-pro-max`, `frontend-design:frontend-design`, `ui-ux-pro-max:design-system`, `ui-ux-pro-max:ui-styling` | Layout, hierarchy, typography, spacing, tokens that match the host theme |
| Frontend copy | `design:ux-copy` | Marathi/English microcopy, empty states, errors (suggestion wording, L2) |
| Frontend QA | `design:accessibility-review`, `design:design-critique` | 48 dp targets, contrast in light and dark, Devanagari clipping |
| Handoff | `design:design-handoff`, `design:design-system` | Spec sheets and token notes for the merge |
| Charts (later) | `dataviz` | Weather month-by-month chart |
| Session continuity | `claude-mem:handoff` | `HANDOFF.md` when stopping mid-way |
| Docs and decks | `anthropic-skills:docx` / `pdf` / `pptx` / `xlsx` | Only if a document, PDF, deck or spreadsheet is requested |

**Not applicable to this stack:** the `vercel:*` skills (Next.js / Vercel hosting) and the other `claude-mem:*` admin skills. This project is Flutter + FastAPI + MongoDB; do not pull Vercel patterns in.

## If something is unclear
Check `docs/OPEN_QUESTIONS.md` first; it has a default for every question. If a needed decision is not there, add it with a default rather than guessing silently.

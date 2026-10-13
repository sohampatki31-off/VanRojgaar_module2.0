# VanMitra Module 4 — VanRozgar (Livelihood Report for Landowners)

An additional module for the VanMitra-AI app. A villager enters his **land, livestock and what he already owns**; the app lists the **resources within 5 km** of his land and gives him a plain **analysis of where he is heading**, with five ranked, legal and wildlife-safe work ideas.

> **Status:** planning complete (v0.1 drafts); no code yet. **First milestone (M0): tomorrow 06:00.**
> **Source documents in this folder:** `VanMitra Module 4 Implementation Plan (1).pdf` (scope) · `VanMitra-AI_Theme_UI_Style_Guide.docx` (look and feel) · `previous/` (the host project's plans) · the WhatsApp screenshot (host app screens).
> **Host app (same tech stack):** `C:\Soham\college work\vanMitraAI` — Flutter + Riverpod + Hive · FastAPI · **MongoDB**.

## Read in this order

| # | Document | What it answers |
|---|---|---|
| 1 | [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | What are we building, for whom, rules we never break, scope for tomorrow, phases |
| 2 | [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) | **What I need you to decide** (Q1–Q4 tonight), with defaults |
| 3 | [docs/MVP_SPRINT.md](docs/MVP_SPRINT.md) | The overnight plan, work packages, fallback ladder, acceptance walkthrough |
| 4 | [docs/BACKEND_PLAN.md](docs/BACKEND_PLAN.md) | Collections, API, the 5 km query, scoring formulas, report JSON contract |
| 5 | [docs/FRONTEND_PLAN.md](docs/FRONTEND_PLAN.md) | Screens, intake form spec, report layout, offline, trilingual strings |
| 6 | [docs/DATA_PLAN.md](docs/DATA_PLAN.md) | What data exists (little), where it could come from, seed format, Sample set |
| 7 | [docs/IDEA_LIBRARY.md](docs/IDEA_LIBRARY.md) | 13 draft work ideas + gate demos (**not expert-reviewed**) |
| 8 | [docs/INTEGRATION.md](docs/INTEGRATION.md) | Exact connection points with the host app; differences from the PDF |

Also: [CLAUDE.md](CLAUDE.md) (working rules for AI-assisted sessions).

## The 30-second version

```
Villager's details ──┐
(land, animals,      │      ┌── resources within 5 km (labelled Useful / Partly / Not, with reasons)
 what he owns,       ├──►  server ── 4 legal gates ── fit ranking ── top-5 ideas + why-not list
 GPS pin)            │      └── "where you are heading" summary
Resource data ───────┘
(MRSAC / team files / Sample)        every result carries: source · date · check status
```

Key points
- **Suggestion only.** The landowner decides; community forest is decided by the **Gram Sabha**.
- **Labels, never numeric scores.** **Never** harm wildlife. **Never** hide missing data.
- The real backend is **MongoDB**, not the PostgreSQL/PostGIS the PDF and `previous/BACKEND_PLAN.md` mention; this plan follows the host.
- **The biggest unknown is the resource data**: none exists in these folders. A clearly labelled Sample set is the fallback ([DATA_PLAN](docs/DATA_PLAN.md) §4).

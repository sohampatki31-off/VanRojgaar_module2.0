# VanMitra Module 4 — M0 Sprint (target: tomorrow 06:00)

> **Goal:** a villager can enter his land, animals and what he owns, and **see the resources within 5 km and an analysis of where he is heading**, on a phone. See [PROJECT_PLAN](PROJECT_PLAN.md) §1.1.
> **Method:** four tracks run in parallel against a **frozen report contract** ([BACKEND_PLAN](BACKEND_PLAN.md) §6). The UI can run on **seed data with no server**, so no track waits for another.

Times are **relative hours (T+0 = start)** because the start time is not fixed. Adjust to the clock.

---

## 0. Ground rules for the night

- **Contract first.** The report JSON in BACKEND_PLAN §6 is the interface. Freeze it by **T+1h**. A change after that needs both owners to agree.
- **Never cut** (PROJECT_PLAN §2.1): trust labels · the "Suggestion only…" footer · the four gates · the wildlife badge · "Told by you, not verified".
- **Cut order:** Hindi → dark theme → scheme links → Profile details → weather/disaster sample section → "Why not others?" → idea detail screen.
- **Database actions are run by a person.** Anything marked `[USER RUNS]` (index creation, seeding, loading) is never run automatically. Always `--dry-run` first.
- **Sample data is labelled Sample.** Always.
- Commit small and often **on a feature branch** of the host repo; no commits to `main`; no secrets (`.env`, keys).

---

## 1. Tracks and owners

Assign a person per track. One person can take more than one.

| Track | Owner | Goal |
|---|---|---|
| **BE** Backend | | Profile + report endpoints, domain rules with tests |
| **FE** Frontend | | Intake, report, resources screens on the contract |
| **DATA** Data & GIS | | Sample set (and real files if available), loader, demo village geo |
| **CONTENT** Content & review | | Idea library, Marathi strings, policy text, final walkthrough |

---

## 2. Work packages (in order)

Legend: **P0** must be in the 06:00 demo · **P1** should be · **P2** nice.

### T+0h to T+1h — Decide and freeze

| # | Task | Track | Pri | Done when |
|---|---|---|---|---|
| 1 | Answer [OPEN_QUESTIONS](OPEN_QUESTIONS.md) **Q1 (data), Q2 (demo village), Q3 (where code lives)**; the rest keep their defaults | all | P0 | Written answers or "use default" |
| 2 | Create a feature branch in the host repo; create the empty folders from [INTEGRATION](INTEGRATION.md) §2 | BE+FE | P0 | `lib/features/livelihood/` and `app/livelihood/` exist |
| 3 | Freeze the report JSON (BACKEND_PLAN §6) and copy a **sample report file** into the app assets | BE+FE | P0 | `assets/livelihood/sample_report.json` loads in the app |

### T+1h to T+4h — Build in parallel

| # | Task | Track | Pri |
|---|---|---|---|
| 4 | `domain/units.py`, `labels.py`, `gates.py`, `fit.py`, `wildlife.py`, `analysis.py` + unit tests ([BACKEND_PLAN](BACKEND_PLAN.md) §5) | BE | P0 |
| 5 | Sample resource set per DATA_PLAN §4.1; `lv_village_geo` for the demo village | DATA | P0 |
| 6 | Draft idea library JSON from [IDEA_LIBRARY](IDEA_LIBRARY.md) (13 ideas) | CONTENT | P0 |
| 7 | `LivelihoodRepository` + **Seed** implementation; models + parsing; widgets (trust label, badges, cards, footer) | FE | P0 |
| 8 | Strings file en + mr ([FRONTEND_PLAN](FRONTEND_PLAN.md) §7) | CONTENT/FE | P0 |
| 9 | If real data exists: convert to the seed format, run the loader `--dry-run`, review rejects | DATA | P1 |

### T+4h to T+7h — Wire it up

| # | Task | Track | Pri |
|---|---|---|---|
| 10 | `models.py`, `schemas.py`, indexes entry; `service.py` (`centre_for`, `$geoIntersects` candidates, exact distance, tags) | BE | P0 |
| 11 | `router.py`: `PUT/GET/DELETE /profile`, `POST /report`, `GET /report/latest`, `POST /resources/nearby` | BE | P0 |
| 12 | `[USER RUNS]` `setup_mongo.py` (indexes), `seed_livelihood.py`, loader on the sample set | USER | P0 |
| 13 | Screens: S1 home, S2 intake (5 steps), S3 location picker | FE | P0 |
| 14 | Screens: S4 report, S5 resources; dashboard card + routes | FE | P0 |
| 15 | Report "Where you are heading" section from `analysis` | FE | P0 |

### T+7h to T+9h — Connect and harden

| # | Task | Track | Pri |
|---|---|---|---|
| 16 | `Remote` repository on the host `ApiClient`; switch between Remote and Seed | FE | P0 |
| 17 | Hive cache of the last report ("Showing your last saved report") | FE | P1 |
| 18 | Idea detail screen; weather/disaster **Sample** sections; policy screen | FE | P1 |
| 19 | `/ideas/{code}`, `/meta` | BE | P1 |
| 20 | Fix overflow in Marathi on a small viewport; dark theme check | FE | P1 |

### T+9h to T+10h — Walkthrough and freeze

| # | Task | Track | Pri |
|---|---|---|---|
| 21 | Run the acceptance walkthrough (§5) on a **real phone** | CONTENT/all | P0 |
| 22 | `flutter analyze`, `flutter test`, `ruff`, `mypy`, `pytest` all green | BE+FE | P0 |
| 23 | Record a **backup screen recording** of the walkthrough | CONTENT | P0 |
| 24 | Write down what was Sample vs real, for the presenter ([PROJECT_PLAN](PROJECT_PLAN.md) §2) | CONTENT | P0 |

---

## 3. The fallback ladder

If something is not ready, drop to the next rung **without changing the story**:

1. Full path: app → backend → Mongo → real/sample data.
2. Backend not up → app switches to the **Seed repository** (bundled sample report + the same screens).
3. Intake not finished → the app generates the report from a **pre-filled demo profile** (land, animals, assets) and the form is shown read-only.
4. Location picker not finished → use the **village centre** and say so in the header ("from your village centre").

Whichever rung is used, the **Sample** chip and the footer stay on screen.

---

## 4. Demo data for the walkthrough

| Item | Value |
|---|---|
| Login | The demo **villager** from the host docs (`frontend_backend.md` §A2) |
| Village | Ozhar (host demo) unless Q2 says Nashik |
| Land | e.g. **1.2 ha**, irrigated, open well (realistic range from the Ozar CSV `Area_sqm`; no names) |
| Animals | 2 cows, 5 goats, 10 poultry |
| Owns | well, pump, shed |
| Past work | millets, dairy |
| Money | medium |
| Location | A pin inside the Sample set's 5 km radius |

Expected result: nearby water, grazing and forest resources with mixed labels; **Dairy** and **Goat rearing** rank high (animals + fodder + water); **Mushroom** appears as a low-risk option; community ideas (fish pond, MFP) show **"through the Gram Sabha"**; every idea shows "Ask the Forest Department first" only when a protected layer is within 2 km (not in the default demo; move the pin about 1 km north-north-east to show it).

---

## 5. Acceptance walkthrough (the 06:00 test)

Tick each on a real phone. A step that crashes or shows a numeric score **fails the whole run**.

- [ ] Log in as the demo villager; the dashboard shows the **My Livelihood** card
- [ ] Open it; sees "no details yet"; taps **Add your details**
- [ ] Enters **land** (try acres, then guntha; the hectare value updates), **animals**, **what he owns**, **past work & money**
- [ ] Drops a pin (or uses current location); saves
- [ ] Taps **Show my report**; the report opens with the **header** and a "from your plot" (or village centre) line
- [ ] **Resources within 5 km** lists items sorted by distance; every card has a **distance, a label, a one-line reason and a trust label**; no numbers like 0.72 anywhere
- [ ] A resource with missing data says **"Not yet checked on the ground"**
- [ ] A community-forest resource says **"Use only through the Gram Sabha"**
- [ ] **Your own resources** lists the animals and assets with **"Told by you, not verified"**
- [ ] **Where you are heading** shows a headline, strengths, constraints and next steps
- [ ] **Ideas** shows up to five, each with fit label, reason, cost, season, **wildlife risk**; fewer than five says why
- [ ] **Why not others?** lists removed ideas with the gate (if enabled)
- [ ] Changes the land to 0.05 ha and regenerates; farm ideas drop or show the "needs about X ha" note
- [ ] Switches language **Marathi ↔ English**; nothing clipped; the report re-renders
- [ ] Airplane mode → reopen → **"Showing your last saved report"**
- [ ] **Sample** chip and the **"Suggestion only…"** footer are visible
- [ ] **Delete my answers** works and clears the report

---

## 6. After 06:00

Capture what was learned and feed it back into: the report contract, the idea library, [OPEN_QUESTIONS](OPEN_QUESTIONS.md), and the Phase 2 plan (connect to Modules 1–2). Then plan Phase 3 (real data) around the written data permission, which is the slowest item.

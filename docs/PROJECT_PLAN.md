# VanMitra Module 4 (VanRozgar) — Project Plan

> **Status:** v0.1 draft · **Source of truth for scope:** `VanMitra Module 4 Implementation Plan (1).pdf` (the "Module 4 PDF")
> **Host app:** `C:\Soham\college work\vanMitraAI` (Flutter + FastAPI + MongoDB), described in `previous/BACKEND.md`
> **Companion documents:** [BACKEND_PLAN](BACKEND_PLAN.md) · [FRONTEND_PLAN](FRONTEND_PLAN.md) · [DATA_PLAN](DATA_PLAN.md) · [IDEA_LIBRARY](IDEA_LIBRARY.md) · [MVP_SPRINT](MVP_SPRINT.md) · [INTEGRATION](INTEGRATION.md) · [OPEN_QUESTIONS](OPEN_QUESTIONS.md)

If this plan and the code disagree, change the plan first (or say why in a PR), then the code.

---

## 1. What we are building

VanMitra today helps a village **claim forest rights**. **Module 4 (VanRozgar)** starts where the claim ends: it helps one landowner see **what resources lie around his land and what work he can start from them**.

The landowner tells us about his own situation. We combine that with the resources near him and give him a **personal livelihood report**.

> **Naming:** the PDF calls this "Module 4" even though an earlier module was dropped. Keep calling it Module 4 / VanRozgar in files and screens so nobody is confused.

### 1.1 The target for the first deadline (tomorrow, 06:00)

The team does **not** need the whole PDF by then. The goal is one clear story a villager can walk through:

1. He opens **My Livelihood (माझा रोजगार)** from his dashboard.
2. He enters **his details**: how much **land** he has, what **livestock** he keeps, and what **resources he already owns** (well, pump, shed, …).
3. He fixes **where his land is** (GPS pin, or his village centre as a fallback).
4. The app lists the **resources available within 5 km** of that point (water bodies, wells, check dams, forest, grazing land, …). Each is marked **Useful / Partly useful / Not useful** with a one-line reason, its distance and a trust label.
5. The app gives him a plain **analysis of where he is heading**: what his land and animals can support, what the nearby resources allow, and the **top five work ideas** with the reasons behind them.

That five-step path is **milestone M0**. Everything else in the PDF is later (see §2).

### 1.2 What it is and is not

| Module 4 **is** | Module 4 **is not** |
|---|---|
| A personal, read-only suggestion report | A decision-maker. The landowner decides; for community forest, the **Gram Sabha** decides |
| Built on open or official data, each result labelled with source and date | A source of "true" facts. Everything is "to be verified on the ground" until someone checks it |
| For **one individual landowner** (Village / Gram Sabha User role) | A village-level or Gram Sabha tool |
| A guide that never suggests anything harming wildlife | A legal opinion. Ideas are reviewed by experts before launch |
| Separate from claims: it never changes a claim, title or boundary | A scheme portal. It only links to official scheme pages |

---

## 2. Scope

| # | Feature (Module 4 PDF §1) | M0: tomorrow 06:00 | Later phase |
|---|---|---|---|
| 1 | Personal livelihood report (one scrolling screen) | ✅ cut-down: header, resources, analysis, ideas, footer | Full 10 parts |
| 2 | **Resources near the land** (5 km) with Useful / Partly / Not useful | ✅ **core** | Real MRSAC data, field checks by the FRC |
| 3 | Weather and past disasters | ⚪ sample rows, labelled **Sample** | Real weather source and disaster records |
| 4 | **Ranked work ideas** (gates → fit → top 5) | ✅ with a 12-idea draft library | Expert-reviewed library of about 20 |
| 5 | **Add your details** (land, livestock, owned resources, past work, money…) | ✅ **core** | Delete-my-answers screen, richer questions |
| 6 | Ask about your report (chat) | ❌ | Phase 4 (rule-based first, then Claude API) |
| 7 | Safety, law, wildlife | ✅ gates + wildlife badge + footer. The policy page is a static screen | Forest Department advice by division |
| 8 | Schemes | ❌ (a link row at most) | Phase 3 |
| 9 | Trust labels | ✅ **never cut** | — |
| 10 | Languages and settings | ✅ Marathi + English; Hindi if time allows | Native-speaker review |

**Explicitly out of scope** (PDF §1, §4): voice input, medicinal plants (jadibuti), community or Gram Sabha tools, other roles (FRC field checks, DFO advice, admin editor), crop history read from the 7/12.

### 2.1 What gets cut first if time runs short

Cut in this order (PDF §17): **Hindi → dark theme → scheme filters → Profile details → weather/disaster sample section → "Why not others" list → idea detail screen**.

**Never cut:** trust labels · the "Suggestion only. Check on the ground. The Gram Sabha decides." footer · the four legal gates · the wildlife-risk badge · the "Told by you, not verified" tag on anything the user entered.

---

## 3. Rules we never break

Adapted from Module 4 PDF §2, §9, §12 and the host project's rules (`previous/PROJECT_PLAN.md` §2).

| # | Rule | What it means in code and UI |
|---|---|---|
| L1 | **No false data.** | Every result shows its **source**, **source date** and **check status**. Unknown date → "date not known". Demo data is labelled **Sample**, never passed off as real |
| L2 | **Suggestion only.** | Wording is "may help", "could suit", never "you qualify", "approved", "eligible". The landowner decides |
| L3 | **Community forest belongs to the Gram Sabha.** | Any resource tagged `inside_cfr` shows **"Use only through the Gram Sabha"**. Never tell one person to use it alone |
| L4 | **Never harm wildlife.** | The gates drop hunting, trapping, timber and wildlife-harm ideas. Every idea shows a wildlife-risk badge. Near a protected area: "Ask the Forest Department first". The word is "check with", never "safe" |
| L5 | **Labels, not scores.** | The 0–1 numbers are internal. The user sees **Useful / Partly useful / Not useful** and **Good / Fair / Weak fit**, never "0.72", never a percentage. (Matches host rule R2: no scores) |
| L6 | **Missing data is shown, not hidden.** | A check with no data starts at 0.5 and the card says "Not yet checked on the ground". No past work? The report skips that part, says so in one line, and still shows everything else |
| L7 | **Absence of a record is not absence of an event.** | Disasters: "No record found in our data. This does not mean there were none." Never "no floods" |
| L8 | **Private by default.** | The profile and report are visible only to that user. We collect only what the report needs: **no caste, no income, no ID numbers**. He can see and delete his answers |
| L9 | **Read-only on legal records.** | The module never writes to claims, titles or boundaries. "Forest candidate" plots are guesses and never shown as legal eligibility |
| L10 | **Three languages, no clipping.** | Marathi (host default), English, Hindi. Devanagari never clipped. No hard-coded strings |
| L11 | **Satellite tiles are never cached offline.** | Google satellite tiles are never cached or served offline (PDF §12) |
| L12 | **Server holds the logic and the keys.** | Gates, scoring and any AI call run on the server; no API key ships in the app |

---

## 4. Who it is for

- **Role:** the existing `villager` role (and a `gram_sabha` user acting as an individual). The module reads the signed-in user and his village from the host app.
- **Assumptions about him:** reads little; shared low-cost Android phone; weak network; prefers Marathi or Hindi. So: simple words, big buttons, icons, **text input only** (no voice).
- **His land versus community forest:** his plot and the village's CFR are different. Resources inside CFR are tagged `inside_cfr` and are **Gram Sabha-only** (rule L3).
- **Two levels of report** (PDF §6):
  - **Village report:** measured from the village centre. Always available.
  - **Plot report:** measured from his own pinned plot. M0 uses a **GPS pin** he sets himself, because the host app's claims do not store plot geometry or survey numbers (verified in `app/models/claims.py`: only a free-text `survey_compartment_numbers` list on Form C).

---

## 5. User journey (M0)

```
Dashboard ──► "My Livelihood" card
                  │
                  ▼
        Livelihood home ── no details yet ──► Add your details (5 short steps)
                  │                                   │ Land · Animals · What you own
                  │                                   │ · Past work & money · Location
                  ▼                                   ▼
            Show my report ◄───────────── Save (offline-safe)
                  │
                  ▼  server: nearby resources (5 km) → label each → gates → rank ideas
        ┌─────────────────────────────────────────────┐
        │ 1 Header card (name, village, date, trust)   │
        │ 2 Resources within 5 km (cards + See all)    │
        │ 3 Your own resources ("Told by you")         │
        │ 4 Where you are heading (analysis summary)   │
        │ 5 Ideas for you (top 5, each with reasons)   │
        │ 6 Why not others? (removed ideas + reason)   │
        │ 7 Footer: "Suggestion only…" + policy link   │
        └─────────────────────────────────────────────┘
```

A village that is **not CFR-recognised** still sees the report in M0 (the CFR status lookup comes from Module 2 later; see [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q9).

---

## 6. What the villager tells us (the intake)

All questions are **optional**, except the **location** (without it we fall back to the village centre) and **land area** (without it we cannot size ideas, so the report says so and still lists resources). Full field spec in [FRONTEND_PLAN](FRONTEND_PLAN.md) §4.

| Group | Fields | Why we ask |
|---|---|---|
| **Land** | Area (value + unit: hectare / acre / guntha → stored in hectares), land type (irrigated / rain-fed / mixed), water on the land (open well / borewell / none) | Sizes ideas; decides whether water-heavy ideas are possible |
| **Livestock** | Counts: cows, buffalo, bullocks, goats/sheep, poultry, other | Counts as resources (**"Told by you"**); raises dairy, goat and poultry ideas; fodder and water need |
| **What I already own** | Checklist: well, borewell, farm pond, shed, pump, drip kit, bullock cart, storage, vehicle, fodder land, other | Same: added to the resources list, marked "Told by you" |
| **Past work & money** | Last 3 years (pick from a short list), family members who can work, money you can invest (low / medium / high) | "Build on your work" ranking; size and cost of ideas |
| **Location** | GPS pin on a map (or "use my current location"); fallback: village centre | The centre of the 5 km search |

Everything he enters is labelled **"Told by you, not verified"** and is never presented as official data (L1, L8).

---

## 6b. How the analysis works, in one page

Details and formulas are in [BACKEND_PLAN](BACKEND_PLAN.md) §5. In short:

1. **Find** every known resource within **5 km** of the point (default; configurable up to a cap).
2. **Label** each one: `U = 0.35·A + 0.25·C + 0.25·S + 0.15·R`
   (A availability, C condition, S season span, R reach). **≥ 0.70 Useful · 0.40–0.69 Partly useful · < 0.40 Not useful.** Any check with no data = 0.5 + "Not yet checked on the ground".
3. **Add his own** resources (animals, assets) as "Told by you".
4. **Gate** the idea library: remove any idea that needs land sale or lease (Sec 4(4)), involves hunting or trapping (Sec 3(1)(l)), cuts timber or harms wildlife (Sec 5), or is not allowed in CFR. Record which gate removed it.
5. **Rank** the rest: `F = 0.35·M + 0.20·K + 0.15·P + 0.15·E + 0.15·G` (M resource usefulness, K market access, P people fit, E ease of start, G green fit). Weather/disaster tags nudge M.
6. **Show five**, each with rank, name (mr/en), fit label, one-line reason, resources used, cost level, best season, wildlife risk. Fewer than five pass → show fewer and say why.
7. **Write the analysis summary** ("where you are heading") from the facts, by code. No free-form AI text in M0.

All weights are **starting values** stored in config so they can be tuned after testing (PDF §7, §9).

---

## 7. Technology

The PDF says the stack "matches the rest of VanMitra". The **host app is built on MongoDB**, not PostgreSQL, so this plan follows the host. Differences from the PDF are marked ⚠️.

| Layer | We use | Notes |
|---|---|---|
| Mobile | **Flutter** (Dart), **Riverpod**, **Hive** (offline cache), `http`, `flutter_map`, `geolocator`, `fl_chart` | All already in the host `pubspec.yaml`: **no new packages needed for M0** |
| Navigation | ⚠️ Host **named routes** (`AppRouter` + `MaterialApp.routes`), not `go_router` | PDF mentions go_router for the standalone shell; we follow the host |
| Strings | ⚠️ Host `AppLocalizations` map + `context.tr('key')`, not ARB files | We add a separate strings file for the feature to avoid merge conflicts |
| Backend | **FastAPI**, Python 3.12, Pydantic v2 | Same as host |
| Database | ⚠️ **MongoDB** (Atlas) with `2dsphere` geo indexes; **not** PostgreSQL/PostGIS | Host `previous/BACKEND.md` §12. `previous/BACKEND_PLAN.md` still says PostGIS and is out of date |
| Geo maths | **Shapely 2** + **pyproj** | Already in host `requirements-core.txt` |
| Auth | Host JWT (phone + 6-digit PIN), `villager` role | No new auth |
| AI (later) | **Claude API**, called only from our backend, answers only from the user's own report, with a number check | Phase 4. See [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q10 for model and budget |
| Weather (later) | One free service, called from the backend, terms checked first | Not chosen. Sample numbers in M0 |
| Hosting | Host's Railway config for dev; India-region cloud or state data centre for production | Host `railway.toml` |
| Checks | `flutter analyze`, `flutter test`, `ruff`, `mypy`, `pytest` | Same as host CI |

---

## 8. Phases

Adapted from PDF §17. Each phase has a **gate**; the next starts when it is passed.

| Phase | Goal | Gate |
|---|---|---|
| **M0 (tomorrow 06:00)** | The five-step story in §1.1, on seed data | The walkthrough in [MVP_SPRINT](MVP_SPRINT.md) §5 runs end to end on a phone |
| 2: Connect | Signed-in user, village and plot come from Modules 1–2 | A signed-in user sees a report for his own village |
| 3: Real data | Resource database (MRSAC or other permitted source), weather, disaster history, expert-written idea library, verified scheme register | Data permission **in writing**; experts sign off the idea list |
| 4: AI and details | Ask box on the backend with the number check; full Add-details form; native-speaker Marathi/Hindi review | 30-question test set shows **zero** unsupported numbers |
| 5: Safety review | Forest-law expert + animal-welfare NGO + Forest Department review; officer-advice list | Written expert sign-off |
| 6: Pilot | Real landowners, FRC field checks, measure the targets below | Targets met |

**Targets** (PDF §2, to tune in the pilot): ≥ 80 % of resources confirmed on the ground by the FRC · ≥ 3 of 5 ideas rated sensible by landowners · **zero** ideas that break a legal or wildlife rule · screens respond within 1 s on a low-cost phone with weak network.

---

## 9. Work areas (no names, as in the PDF)

| Area | Covers | M0 |
|---|---|---|
| Frontend | Screens, report display, languages, themes | Intake form, report, resources, idea detail |
| Backend | Routes, database, scoring, (later) AI and refresh job | Profile + report endpoints, scoring domain, seed loader |
| Data & GIS | Loading and cleaning resource data, distances, source/date on every record | Seed file, validation, demo plots |
| Content | Idea library, translations, policy wording | 12 draft ideas, main Marathi strings |
| Review & testing | Walkthrough, legal and wildlife review | Phone walkthrough |

The previous host plan names Soham (backend), Kaushal (frontend) and Ishan (support/review). Assign people to areas at the start of the sprint; one person may cover several.

---

## 10. Risks (PDF §20, plus new ones)

| Risk | Response |
|---|---|
| **No resource data yet** (we hold none in this folder) | Source-neutral loader; M0 runs on a **clearly labelled Sample** or team-supplied seed. Biggest open item: [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q1 |
| Wrong or old map data | Trust labels, a date on everything, field checks later |
| An idea harms wildlife or breaks the law | Gates, wildlife-risk badge, expert and NGO review before launch. Ideas in M0 are **drafts, not expert-reviewed**: say so |
| The docs and the host disagree (DB, routing, i18n) | This plan follows the host; deviations from the PDF are listed in §7 |
| Landowner's land details exposed | Visible only to that user; collect only what is needed; DPDP Act 2023 review before launch |
| Low literacy, shared phones, weak network | Icons, simple words, 3 languages; last report cached offline (P1 in M0) |
| Overnight deadline | Keep the phase order and cut features, **never safety checks** (§2.1) |
| Translations wrong | Native-speaker review before any villager sees them; mark draft strings |

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **CFR** | Community Forest Resource: forest the village has the right to protect, manage and use [FRA 2006] |
| **Gram Sabha / FRC** | Village assembly / its Forest Rights Committee |
| **DFO** | Divisional Forest Officer |
| **7/12 (satbara)** | Land record for a survey number: holder, area, khata |
| **MRSAC** | Maharashtra Remote Sensing Applications Centre; state geographic data |
| **MFP** | Minor forest produce: honey, bamboo, lac, tendu |
| **Gate** | A rule that removes an idea before ranking |
| **Trust label** | Tag on every result: source, source date, check status |
| **Fit score** | Internal 0–1 number for how well an idea fits one landowner. Shown only as a label |
| **Told by you** | Data the landowner entered himself; never shown as official |
| **Guntha** | 1/40 acre (Maharashtra land unit). 1 acre ≈ 0.4047 ha |

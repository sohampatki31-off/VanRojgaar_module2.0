# VanMitra Module 4 — Open Questions and Decisions

> Every question has a **default** the team builds on unless someone objects, so nothing is blocked while waiting. Change a default by editing this table.
> **Status key:** ◐ proposed default (build on it) · ☐ open, needs an answer from the owner · ☑ decided

---

## A. Needed before the 06:00 build starts

| # | Question | Why it matters | Default (what I built the plan on) | Status |
|---|---|---|---|---|
| **Q1** | **Where does the resource data come from for tomorrow?** Do the team's **Nashik** files (PDF §14, §17) exist, in what format, and may they be shown in a pitch? Do their survey numbers carry a location? | There is **no resource data** in this folder or the host repo. Without it the "5 km" list is empty | Build a **labelled Sample set** (DATA_PLAN option D) as the guaranteed fallback and slot the real files in when they arrive | ☐ **Answer needed tonight** |
| **Q2** | **Which village/district is the demo?** The host demo is **Ozhar, Jawhar, Palghar**; the PDF pitch is **Nashik** | Decides the Sample set coordinates, `lv_village_geo`, and the story | Ozhar (it is already in the host's demo login and seed) | ☐ |
| **Q3** | **Where does the code live?** (a) a feature branch of the host repo `vanMitraAI` with isolated folders, or (b) a separate repo `vanmitra-rozgar` copied in later (the PDF's plan) | The PDF chose standalone because the host code was **not available**; it is available now. Standalone costs a throw-away shell (theme, routes, tabs) | (a) **host feature branch**, isolated folders ([INTEGRATION](INTEGRATION.md)) | ◐ |
| **Q4** | **Search radius and centre.** You asked for **5 km**; the PDF starts at **3 km** and calls it a tuning value. Measured from where? | Changes results and the R (reach) bands | **5 km**, configurable, server cap 10 km. Centre = **GPS pin of his land**, else village centre | ◐ |

## B. Resolved by what the code shows (please confirm)

| # | Question | Finding | Decision | Status |
|---|---|---|---|---|
| Q5 | Database: PDF says PostgreSQL + PostGIS | The real backend is **MongoDB Atlas** (`app/mongo.py`, `previous/BACKEND.md`); `previous/BACKEND_PLAN.md` is out of date | **MongoDB `2dsphere`** + Shapely | ☑ (evidence) |
| Q6 | Where does the villager's land come from? | Host claims have **no plot geometry or survey number** | He **enters area and drops a pin**. Later: prefill from a saved claim's extent | ◐ |
| Q17 | Who gets the module? | PDF §4: "Village / Gram Sabha User role" | `villager` and `gram_sabha` users, each for **their own** land | ◐ |

## C. Product and content

| # | Question | Default | Status |
|---|---|---|---|
| Q7 | Show the draft idea list to villagers while it is **not expert-reviewed**? Show gate-removed ideas in "Why not others?" | Yes for the demo, clearly **draft/prototype**, footer on. Show lease and timber in "Why not others?"; **never** show the hunting/trapping entry | ◐ |
| Q8 | Languages for tomorrow | **Marathi + English**; Hindi if time. Konkani (`kn`) out of scope for this module | ◐ |
| Q9 | CFR status of the village (Module 2) | Not available; header shows none. A not-yet-CFR village still gets the report in M0 (PDF says it stops at step 2 with a claim-help link: build when Module 2 exists) | ◐ |
| Q13 | Proposed numbers the PDF does not give: **fit label bands** (≥ 0.70 Good, 0.40–0.69 Fair, < 0.40 Weak), **R bands by distance** (1/3/5 km → 1.0/0.7/0.4), protected-area "near" = 2 km, flood "near" = 300 m, candidate margin 1.5 km | As written in [BACKEND_PLAN](BACKEND_PLAN.md) §5; stored in `lv_config`, tunable | ◐ |
| Q14 | Livestock analysis depth | **Facts only** ("fodder and water within 5 km: yes/no, distance"). No computed feed needs until an agriculture expert supplies numbers | ◐ |
| Q15 | Land-area unit handling | Hectare / acre / guntha, stored in hectares; show the conversion back | ◐ |
| Q16 | Colours | Use host `AppColors` tokens (code beats the style-guide doc's hex values). Status colours carry meaning only | ◐ |

## D. Later phases (not blocking M0)

| # | Question | Needed before | Owner |
|---|---|---|---|
| Q10 | **Question-box AI:** Claude API key, which model, monthly budget; the server-side route and number-check design are in the PDF §11 | Phase 4 | Product owner |
| Q11 | **Weather and disaster data:** which free weather service, under what terms; where to find village-level disaster records | Phase 3 | Data & GIS |
| Q12 | **Reviewers:** name the forest-law expert, agriculture expert, animal-welfare reviewer, NGO partner, Marathi and Hindi translators | Phase 5 | Product owner |
| Q18 | **Resource data permission:** which department sends the formal MRSAC request, under what licence may we copy and refresh? (Permission takes weeks; start now) | Phase 3 | Product owner |
| Q19 | **Forest officer's authority:** can the DFO advise on or remove livelihood ideas? Ask the District Tribal Welfare Officer, the NGO partner or an FRA lawyer. Until then, officer input is **advice only** | Phase 5 | Product owner |
| Q20 | **A resource map:** show a small map of the plot and resources inside the report? (No map view exists in Module 4 yet; the report is list-first) | Phase 2 | Product owner |
| Q21 | **Wording of CFR:** keep "CFR" in Latin letters with a Marathi term beside it; which term do officers use? | Phase 4 | Content |
| Q22 | **Crop history:** is there a permitted source for crop entries on the 7/12? Until then, past work is typed by the user | Phase 3 | Data & GIS |
| Q23 | **Schemes:** who fills and signs the scheme register (`SCHEMES.md`)? | Phase 3 | Content |
| Q24 | **Legal bases in the gates** (Sec 4(4), 3(1)(l), 5): have an FRA lawyer confirm before launch | Phase 5 | Legal review |
| Q25 | **Data protection:** DPDP Act 2023 review of profile storage, consent wording, retention | Before pilot | Legal review |

---

## E. Decisions log

| Date | Decision | By |
|---|---|---|
| 2026-10-14 | Plan follows the **host's real stack** (MongoDB, named routes, `AppLocalizations`) where it differs from the Module 4 PDF | Proposed (Claude), awaiting confirmation |
| 2026-10-14 | Radius **5 km** (requested) instead of the PDF's 3 km starting value | User request |
| 2026-10-14 | M0 scope = intake + 5 km resources + analysis + top-5 ideas; Ask box, schemes, real weather are later | User request, scoped by Claude |

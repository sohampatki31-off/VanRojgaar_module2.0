# VanMitra Module 4: to-do and status

> Updated 2026-10-14 (evening: stages 1, 2 and 3 done). Companion: [to_do_deferred_items.md](to_do_deferred_items.md) (the four things we
> chose not to build first, explained in full). Rules that never break: [../CLAUDE.md](../CLAUDE.md).
> Legend: ✅ done · 🔄 in progress · ⬜ not started · ⛔ blocked on a person or a decision outside the code

---

## 1. Where we are

A villager can open **My Livelihood**, add his details (land with acre/guntha/hectare conversion,
animals, what he owns, past work and money, location by GPS or typed coordinates or village centre),
and see a report: the **resources within 5 km** (Useful / Partly useful / Not useful, each with a
reason, distance and source), a **"where you are heading"** summary, **five ranked ideas** with law
and wildlife checks, and **why other ideas were removed**. Everything works offline-first with an
encrypted cache, and "Delete my answers" is guaranteed to reach the server.

| Area | Status |
|---|---|
| Backend modules 1-3 and the Ask chat (rules, profile, reports, nearby, loader, host-style auth seam, Ask) | ✅ 440 tests, ruff and strict mypy clean |
| Frontend modules 1-3 and the Ask screen (report, intake form, live API, offline cache, Ask) | ✅ 120 tests (+5 live-contract, run against a real server), analyzer clean |
| Integration into the host app `vanMitraAI` | ✅ local branch `feature/module4-livelihood`, not pushed (host: 245 backend, 95 Flutter tests) |
| Running on a real phone (A059P, Android 16, USB) | 🔄 app installs and runs; end-to-end check is stage 1 below |
| Real MongoDB | ⛔ nothing run against a database yet; needs a person (see below) |
| Real resource data | ⛔ only the labelled **Sample** set exists |

---

## 2. The stages to a complete prototype

### Stage 1: finish the phone check ✅ (headless) / 🔄 (on the phone by hand)
Proved by the live contract test (the real Dart client against a real backend: save, a second phone reads it, report parses in Marathi, offline fallback, delete). Still to tick by hand on the phone:
- [ ] Save details on the phone and watch them reach the server (the "waiting to send" message clears)
- [ ] Show my report: resources, summary, ideas, why-not, footer, **Sample** chip
- [ ] Switch language Marathi ↔ English; dark theme
- [ ] Change land to a tiny area: farm ideas show "needs about X ha"
- [ ] Airplane mode: last saved report appears with the "last saved" banner
- [ ] Delete my answers: gone from the phone and from the server
- [ ] NEW: open "Ask about your report" at the bottom of the report; tap a suggestion; type a question

### Stage 2: "Ask about your report" chat ✅ (deterministic; no AI model)
Backend `POST /ask`, `GET/DELETE /ask/history`; app screen `/livelihood/ask` reached from the end of the report. 270 new backend tests, 19 new app tests.
- [x] Safety check **first**, in code: harmful questions get the **red** policy message and no answer (en/mr/hi word lists, tested with about 100 harmful and look-alike phrasings; an independent review found gaps and they were fixed). **The word lists are a draft: the forest-law and animal-welfare reviewers and Marathi/Hindi speakers must check them (Q12)**
- [x] Off-topic questions get the **grey** "I can only answer questions about your report"
- [x] On-topic answers come only from his own saved report, ending "From: <report part>"; the report is rebuilt first if he changed his details or newer data was loaded
- [x] Not in the report (prices, loans, schemes, animal attacks, an idea we have not checked): grey "This is not in your report. Ask the agriculture officer or the Forest Department"
- [x] **Number check** on every answer: a number not in the report replaces the answer with the grey note
- [x] Question suggestions built from the facts in his report (each user sees different ones)
- [x] "Trying another idea": answered from what the report found (rank, removed by which law, held back), or an honest "not checked for your land" with no numbers
- [x] The report is data, not instructions ("ignore your rules" changes nothing; tested)
- [x] History he can see and delete; deleted with his answers; a refused question is **not kept** and long digit runs are masked (L8)
- [x] Language switch re-renders earlier answers (answers are `{key, params}`)
- [ ] Marathi and Hindi wording of every `ask.*` string is a machine draft (Hindi falls back to English for now)
- [ ] Real MongoDB: `lv_chat_log` index (a person runs `setup_livelihood_indexes.py`); the Mongo chat code is unit-tested only

### Stage 3: idea detail and Schemes tab ✅
Backend `GET /ideas/{code}`, `GET /schemes`; app screens `/livelihood/idea` (tap any idea card or a row in "Why not others?") and `/livelihood/schemes` (from the end of the report). 24 new backend tests, 24 new app tests.
- [x] Idea detail screen: why suggested, what it needs (near you / yours / not found), the checks that ran (law, wildlife, needs, land, community forest, each with a word and a reason), a weather note, the resources it would use, warnings, matching schemes
- [x] Backend `GET /ideas/{code}` built from his current report (rebuilt if his details changed); an idea removed by law shows the law and no schemes; an idea the report knows nothing about is a 404, never invented
- [x] Schemes tab: Government and NGO tabs, filters (farming, fishing, livestock, small business, forest produce; women, tribal, farmers, groups)
- [x] Scheme cards: what it is, who runs it, who can apply (as the official page says), papers usually asked for, last checked, and **Open official page** (https only). There is **no field for an amount** and the wording never says "you qualify"
- [x] All 8 scheme rows are labelled **Sample** (they are examples, not real schemes); 3 link to the national scheme search portal and say so
- [x] Idea cards show how many register rows may relate; "Ask" answers questions about schemes from those counts
- [ ] ⛔ A real, hand-checked scheme register: who fills and signs it (Q23). Until then the Schemes tab is a demo of the layout
- [ ] Marathi wording of every new string is a machine draft
- [ ] Real MongoDB: `lv_scheme` index and `seed_livelihood.py --apply` (a person runs them)

### Stage 4: map of the plot and resources ⬜ (open decision Q20)
- [ ] A small map of his plot and the resources around it, replacing typed coordinates with a pin picker
- [ ] Google satellite tiles are **never** cached or served offline (rule L11)

### Stage 5: polish for the show ⬜
- [ ] Hindi strings; a native-speaker review of every Marathi string (all current Marathi is a machine draft)
- [ ] Rehearse the 5-minute pitch path from the PDF (§17); record a backup screen recording
- [ ] State out loud what is Sample and what is real

### The AI agent (real AI chat) ⬜ next, after stage 3
Stage 2 is the safe foundation. This adds Claude behind the **same** checks.
- [ ] A pluggable "answerer": the deterministic one (stage 2) or Claude
- [ ] Claude called **only from the backend**; the key lives in `backend/.env`, never in the app
- [ ] Only report facts go to the model (never his name); report treated as data, not instructions
- [ ] The number check and the safety check run **around** the model, so it cannot bypass them
- [ ] A fixed test set in three languages with **zero unsupported numbers** before it is switched on
- [ ] ⛔ Needs from you: an API key, a model choice, a monthly budget (PDF open decision Q10)
- [ ] ⛔ Needs from you: consent wording for sending his facts to an outside service (DPDP Act 2023)

---

## 3. Things that depend on a person, not on code

| Blocker | Who | Why it matters |
|---|---|---|
| **Real resource data** (Q1): the team's Nashik files, or another permitted source | you / the data owner | Today every resource is synthetic and labelled Sample. The biggest gap in credibility |
| **Data permission in writing** (Q18): which department asks MRSAC, under what licence | you / the department running the Forest Rights process | Takes weeks; the slowest part. Start now |
| **Forest officer's authority** (Q19) | District Tribal Welfare Officer, the NGO partner or an FRA lawyer | Decides whether Forest Department advice can be built at all |
| **Reviewers** (Q12): forest-law expert, agriculture expert, animal-welfare reviewer, Marathi and Hindi translators | you | The idea library is a draft; the Marathi is a machine draft |
| **A real MongoDB**: indexes, seed, a loaded resource file, the smoke test on a throwaway `*_test` database | you (the author may not touch databases) | Mongo code has only been unit-tested, never run against a database |
| **API key and budget** for the AI agent (Q10) | you | The real AI cannot be switched on without them |

---

## 4. Not for the prototype (see [to_do_deferred_items.md](to_do_deferred_items.md))

1. **Field checks by the Forest Rights Committee**: confirm / correct / reject a resource with photo and GPS
2. **Forest Department advice by division**: officers review ideas per forest division
3. **The data refresh job**: re-copy MRSAC data every 4-5 days
4. *(The real AI chat is **not** skipped: it is built right after stage 3, in two steps.)*

## 5. Housekeeping

- [ ] Sync the `backend` and `frontend` branches with `integration` (the host-readiness refactor and everything after it is only on `integration`)
- [ ] Decide whether to push the host branch `feature/module4-livelihood` or open a pull request for the team
- [ ] Add Marathi/English copy review notes to `docs/FRONTEND_PLAN.md` §7 as strings are confirmed

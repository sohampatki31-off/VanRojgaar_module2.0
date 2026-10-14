# VanMitra Module 4: to-do and status

> Updated 2026-10-14. Companion: [to_do_deferred_items.md](to_do_deferred_items.md) (the four things we
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
| Backend modules 1-3 (rules, profile, reports, nearby, loader, host-style auth seam) | ✅ 151 tests, ruff and strict mypy clean |
| Frontend modules 1-3 (report, intake form, live API, offline cache) | ✅ 77 tests, analyzer clean |
| Integration into the host app `vanMitraAI` | ✅ local branch `feature/module4-livelihood`, not pushed (host: 245 backend, 95 Flutter tests) |
| Running on a real phone (A059P, Android 16, USB) | 🔄 app installs and runs; end-to-end check is stage 1 below |
| Real MongoDB | ⛔ nothing run against a database yet; needs a person (see below) |
| Real resource data | ⛔ only the labelled **Sample** set exists |

---

## 2. The stages to a complete prototype

### Stage 1: finish the phone check 🔄
- [ ] Save details on the phone and watch them reach the server (the "waiting to send" message clears)
- [ ] Show my report: resources, summary, ideas, why-not, footer, **Sample** chip
- [ ] Switch language Marathi ↔ English; dark theme
- [ ] Change land to a tiny area: farm ideas show "needs about X ha"
- [ ] Airplane mode: last saved report appears with the "last saved" banner
- [ ] Delete my answers: gone from the phone and from the server

### Stage 2: "Ask about your report" chat ⬜ (deterministic first)
Backend module then frontend module. No AI model yet; this is the safe foundation the real AI plugs into.
- [ ] Safety check **first**, in code, before anything else: harmful questions (hunting, trapping, wildlife trade) get the **red** policy message and no answer
- [ ] Off-topic questions get the **grey** "I can only answer questions about your report"
- [ ] On-topic answers come only from his own report, in his language, ending "From: <report part>"
- [ ] Not in the report: grey "This is not in your report. Ask the agriculture officer or the Forest Department"
- [ ] **Number check**: every number in an answer must exist in the report, or the answer is replaced
- [ ] Question chips built from the facts in his report (each user sees different ones)
- [ ] "Trying another idea" (for example fishing): run the same law/wildlife/resource checks in code
- [ ] The report is data, not instructions ("ignore your rules" changes nothing)
- [ ] Chat history he can see and delete (L8)
- [ ] Language switch re-renders earlier answers

### Stage 3: idea detail and Schemes tab ⬜
- [ ] Idea detail screen: why suggested, what it needs, the checks that ran, a weather note, matching schemes, warnings
- [ ] Backend `GET /ideas/{code}` for the current report
- [ ] Schemes tab: Government and NGO tabs, filters (farming, fishing, livestock, small business, forest produce; women, tribal, farmers, groups)
- [ ] Scheme cards: what it is, who runs it, who can apply, documents, last checked, and **Open official page** (we never take applications, never say "you qualify", never show an amount unless the official page does)
- [ ] All scheme rows labelled **Sample** until a real, hand-checked register exists

### Stage 4: map of the plot and resources ⬜ (open decision Q20)
- [ ] A small map of his plot and the resources around it, replacing typed coordinates with a pin picker
- [ ] Google satellite tiles are **never** cached or served offline (rule L11)

### Stage 5: polish for the show ⬜
- [ ] Hindi strings; a native-speaker review of every Marathi string (all current Marathi is a machine draft)
- [ ] Rehearse the 5-minute pitch path from the PDF (§17); record a backup screen recording
- [ ] State out loud what is Sample and what is real

### The AI agent (real AI chat) 🔄 started after stage 3
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

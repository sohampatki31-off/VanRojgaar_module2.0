# The four deferred items, in detail

> Written 2026-10-14 so we can decide what to build now and what to leave. Source: the Module 4 PDF
> (§7 resources, §11 Ask, §12 safety, §14 data, §17 phases, §21 open decisions) plus how each would
> fit the code we have. "From the PDF" and "my proposal" are marked.
> Status: the **AI chat is being built** (see [to_do.md](to_do.md)); the other three are open for decision.

---

## 1. Field checks by the Forest Rights Committee (FRC)

**What it is (from the PDF §7).** The map data is only a first guess: an official map can show a
well that is dry or gone. The FRC, the village's elected forest-rights committee, confirms what is
really there. For each resource a member **confirms, changes, or rejects** it, with a **photo and a
GPS point**. The checked value then replaces the map value, and every change is logged. A resource
marked wrong stops counting towards scores but stays in the history. This is how a card changes from
"To be verified on the ground" to "Confirmed by the committee", and how the PDF's target
(**at least 80% of resources confirmed**) is measured.

**What it needs in our code (my proposal).**
- A second kind of user. In the host app the closest role is `gram_sabha`, one committee member per village.
- A screen: the village's resources with Confirm / Change / Not right, plus photo and GPS capture.
- Backend: an append-only check record per action (who, when, photo, old and new values). The host
  already has a tamper-evident ledger pattern that could be reused. Collection planned: `lv_resource_check`.
- A rule for shared data: resources are shared, so one person's correction changes everyone's
  report. We need to decide who may edit, how a mistake is undone, and what happens when two members disagree.
- Offline capture with a queue, like the rest of the app (committee members work in the field).

**Why it was skipped first.** It is the biggest of the four, and its governance questions (who may
mark a village resource wrong) belong to the PDF's Phase 6 pilot. The data it would improve is also
only a Sample set right now.

**A light version for the prototype (my proposal).** One committee login that can tap **Confirmed**
or **Not right** on a resource, with an optional photo, saved as a record. The report then shows
"Confirmed by the committee" on that card. No offline queue and no dispute handling yet. Medium size,
and a strong demo: you can show a card change from "to verify" to "confirmed".

**Decisions needed.** Do we want the light version? Who is the demo committee member?

---

## 2. Forest Department advice by division

**What it is (from the PDF §12).** Forest officers work by division, not for all of Maharashtra. The
plan is one list per division of every idea suggested there, sent to the Divisional Forest Officer
(DFO), who can raise a question or advise against an idea. Landowners in that division then see a
warning with the reason, and people who saw the idea earlier get a note. **Until the officer's
authority is confirmed, this is advice, not a silent removal.** Only clearly illegal ideas (hunting,
trapping, protected plants) are removed outright.

**What it needs (my proposal).**
- A DFO account type. The host app treats officers as a separate website with no logins in the app.
- A mapping from each village to its forest division. We do not have this data.
- A review screen or page for officers, and an advice record per idea per division.
- Notifications. The host already has push messaging that could be reused.

**The real blocker is not code.** The PDF's open decision **Q19** asks whether a DFO can legally
advise on or remove livelihood ideas, and says to ask the District Tribal Welfare Officer, the NGO
partner or an FRA lawyer. Building a workflow before that answer risks building the wrong thing. It is
the only item that needs someone outside the team to take part.

**What exists today.** Every idea shows a wildlife badge, and "Ask the Forest Department first"
appears near a protected area. **Missing: the contact**, which the PDF says that flag should carry.

**A light version (my proposal).** Add the contact line to that flag now; optionally a clearly
labelled **Sample** advice banner to show how a division's warning would look. Leave the officer
workflow until Q19 is answered.

---

## 3. The real AI chat (being built)

**What the PDF requires (§11, §12).** A chat that is **not** an open chatbot:
1. **Safety check first, in plain code, before any AI.** Harmful questions (hurting animals, anything
   illegal) get a **red** message ("This is not allowed under our policy. VanMitra does not support any
   harm to wildlife.") with a "Read our policy" link, and **no answer**. Red is used only for this.
2. **Off-topic** questions get a **grey** note: "I can only answer questions about your report."
3. **On-topic** questions are answered **only from his own report**, in his chosen language, ending
   with "From: <the report part used>".
4. **Not in the report?** A grey note: "This is not in your report. Please ask the agriculture officer
   or the Forest Department." The AI never fills the gap from the internet.
5. **Number check:** before an answer is shown, code checks that every number in it exists in the
   report. If one does not, the answer is replaced by the note in point 4.
6. **Language switch** (Marathi, Hindi, English) re-writes earlier answers.
7. **The report is data, not instructions.** Typing "ignore your rules" changes nothing.
8. **Trying another idea** (for example fishing): the same checks run **in code** (law, wildlife,
   resources near him, weather, cost) and the AI only explains the result. If the idea is not in our
   library, the answer is general, labelled "not checked for your land", has no numbers, and points to an expert.
9. The key lives **only on our server**. Questions and answers are kept for testing and audit (not
   voice); he can see and delete his history. **Voice input is on hold.**
10. Gate for this phase (PDF §17): a **30-question test set in three languages with zero unsupported numbers**.

**How we build it (two steps).**
- **Step 1, deterministic (stage 2 in the to-do):** the safety check, off-topic detection, the number
  check, question chips built from his report, and templated answers. No AI model. This is the PDF's
  own prototype approach and it can be tested exhaustively.
- **Step 2, the real AI (started right after stage 3):** Claude behind the **same** checks, for
  free-form questions. The checks run around the model, so it cannot bypass them.

**Needs from you.**
- An **API key** (kept in `backend/.env`, never in the app), a **model choice**, and a **monthly
  budget** (PDF open decision **Q10**). Prices and model options change: check them before committing.
- Consent wording for sending his report facts to an outside service (DPDP Act 2023). We send only
  report facts, never his name.

**Risks.**
- A wrong answer to a farmer can cost real money. The number check and "answer only from the report"
  exist for this.
- It needs the internet; the app must say so when offline.
- Marathi and Hindi answers need a native-speaker review before villagers see them.

---

## 4. The data refresh job

**What it is (from the PDF §7, §14, Phase 3).** Copy the state remote-sensing centre's (MRSAC) map
data into our own database and refresh it every **4-5 days** with a scheduled job. When it refreshes,
a report shows "A newer version of your report is available".

**What already exists.** The loader that validates and loads a file, the dataset **versioning**, and
the `newer_version_available` flag on reports. All built and tested.

**What is missing, and why building it now would be pointless.**
- **The source.** A job needs a real, permitted data source. The PDF says permission takes **weeks**
  and is the slowest part; loading one district once the data is in hand takes about 1-2 days.
- The scheduler itself (the host has a small background-job pattern that could be reused) would have nothing to refresh.
- **A known trap:** Vidarbha districts 08-13 (including Nagpur) have portal data about 6° west of the
  true position. The correction used by the earlier prototype is not in our files; **do not guess it**.

**Recommendation (my proposal).** Do not build the scheduler yet. The thing to do now is start the
formal data request (Q18), because that is the real critical path. Our load command already covers a manual refresh.

---

## Summary

| Item | Value for the pitch | Size | Blocker | Recommendation |
|---|---|---|---|---|
| AI chat | Highest: helps farmers directly | 2 backend + 2 frontend modules | API key, model, budget | **Build** (step 1 deterministic, step 2 Claude) |
| FRC field checks | Strong trust story | Medium (light) / large (full) | Who may edit shared data | **Light version** |
| Forest Dept advice | Safety story | Small (contact) / large (workflow) | **Q19**: officer's authority | **Contact line now, workflow later** |
| Refresh job | None until real data exists | Small | **Q18**: data permission | **Skip the scheduler; start the data request** |

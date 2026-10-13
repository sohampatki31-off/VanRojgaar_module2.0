# VanMitra Module 4 — Frontend Plan

> **Status:** v0.1 draft · Read [PROJECT_PLAN](PROJECT_PLAN.md) first; it wins on scope and rules.
> **Host:** `vanMitraAI/vanmitra_tem` (Flutter, Riverpod, Hive, named routes, custom `AppLocalizations`).

The user is a landowner on a shared low-cost Android phone, often with weak network, who may read little. The screens must be **simple enough for a first-time smartphone user** and **honest enough that nobody mistakes a suggestion for a fact.**

---

## 1. Where the code lives and how it plugs in

All feature code lives in **one folder**, `lib/features/livelihood/`. The host's `features/form_b/` is flat (`form_b_api.dart`, `form_b_models.dart`, `form_b_screen.dart`, …); we use a few sub-folders because this feature is bigger.

```
lib/features/livelihood/
├── livelihood_routes.dart         # route-name constants + registration helper
├── livelihood_strings.dart        # en / mr / hi strings for this feature only (see §7)
├── data/
│   ├── livelihood_repository.dart         # abstract interface
│   ├── remote_livelihood_repository.dart  # uses the host ApiClient -> /api/v1/livelihood
│   ├── seed_livelihood_repository.dart    # reads bundled JSON; no server needed (fallback / demo)
│   └── livelihood_cache.dart              # Hive box: last profile + last report (offline)
├── models/                        # LivelihoodProfile, Report, ResourceItem, IdeaCard, TrustLabel…
├── providers/                     # Riverpod: profileProvider, reportProvider, filtersProvider
├── screens/
│   ├── livelihood_home_screen.dart
│   ├── add_details_screen.dart            # 5-step form
│   ├── location_picker_screen.dart
│   ├── report_screen.dart
│   ├── resources_screen.dart
│   ├── idea_detail_screen.dart            # P1
│   └── policy_screen.dart                 # static wildlife policy
└── widgets/
    ├── trust_label.dart  fit_badge.dart  useful_badge.dart  distance_chip.dart
    ├── told_by_you_tag.dart  suggestion_footer.dart  wildlife_badge.dart
    ├── resource_card.dart  idea_card.dart  section_header.dart  empty_state_lv.dart
```

**One repository interface** (`LivelihoodRepository`) with two implementations, so the screens never know where data comes from (PDF §16). `Remote…` is the real path; `Seed…` lets the UI run with no server and is the **fallback if the backend is not up by morning**.

### 1.1 Connection points with the host (see [INTEGRATION](INTEGRATION.md))

| Host piece | Used for | Change needed |
|---|---|---|
| `AppRouter` (`core/routes/app_router.dart`) | Named routes | Add route constants (`/livelihood`, `/livelihood/details`, …) |
| `app.dart` → `MaterialApp.routes` / `onGenerateRoute` | Register screens | Add entries; idea detail takes an argument → `onGenerateRoute` |
| `VillagerHomeScreen` dashboard (`ActionListItem` / `ClaimActionCard`) | Entry point | Add one card **"My Livelihood / माझा रोजगार"** |
| `ApiClient` (`core/api/api_client.dart`) | HTTP + JWT + `ApiException` | None. Use `get/put/post/delete` |
| `ApiEndpoints` | Paths | Add a `livelihood…` group |
| `AuthProvider` / `User.backendVillageId` | Current user and village | Read only |
| `AppColors` / `context.colors` / `AppTypography` / `AppSpacing` | Theme | Read only. No new colours except status tones from the existing tokens |
| `AppLocalizations` + `context.tr()` | Strings | Optional: feature strings stay in their own file (§7) |
| `localeProvider` | Language | Read only. Host default is **Marathi**; supported `en`, `hi`, `mr`, `kn` |
| `hive_database.dart` | Offline storage | Open one extra Hive box for the cache |
| `geolocator`, `flutter_map`, `latlong2`, `url_launcher`, `fl_chart` | GPS, pin picker, charts, links | **Already in pubspec: no new packages for M0** |

**Navigation entry: a dashboard card, not a sixth tab.** The visual style guide asks to keep the compact **5-item bottom navigation** (Dashboard, Claims, Profile, Gram Sabha, Atlas Map). The PDF's five-tab bar (Dashboard, Resources, Schemes, Report, Profile) was for the standalone shell and is **thrown away** at merge (PDF §3).

---

## 2. Screens

### 2.1 M0 (tomorrow)

| # | Screen | Purpose | Main button |
|---|---|---|---|
| S1 | **Livelihood home** | One screen that shows the state: no details yet → explains in two lines + **"Add your details"**; details saved → **"Show my report"**; report exists → summary + **"Open report"** | Orange, full width, bottom |
| S2 | **Add your details** | 5 short steps: Land → Animals → What I own → Past work & money → Location | **Next / Save my details** |
| S3 | **Location picker** | Map with a draggable pin; **Use my current location** (GPS); fallback "use my village centre" | **Use this place** |
| S4 | **Report** | One scrolling screen (§3) | *(no single main button; sections have their own links)* |
| S5 | **Resources** ("See all") | Filter chips by kind and by tag, counts of Useful / Partly useful / Not useful, resource cards, detail bottom sheet | Tap a card |
| S6 | **Idea detail** *(P1)* | Why suggested, what it needs, checks run, wildlife and law notes, matching schemes (later) | Back |
| S7 | **Policy** | The wildlife policy, static text | None |

Hard layout rules (PDF §15, host style guide): icon on every main action; **touch targets ≥ 48 dp** (the PDF says 44 px; the host's own plan uses 48 dp, so use 48); body text ≥ 16 sp; extra line height for Devanagari so nothing is clipped; **dark theme must work** via `context.colors` (no `Colors.white` / `Colors.black` in widgets).

### 2.2 Later

Ask-about-your-report chat · Schemes tab · Weather chart (`fl_chart`) with real data · Delete-my-answers screen · Forest Department advice banner · FRC "confirm resource" flow.

---

## 3. The report screen, top to bottom

```
┌──────────────────────────────────────────────┐
│ ‹  माझा रोजगार अहवाल        [mr ▾]            │  header (forest green, host style)
├──────────────────────────────────────────────┤
│ 1  HEADER CARD                                │
│    Name · Village · date · "from your plot"   │
│    [Sample data] [To be verified] chips        │
├──────────────────────────────────────────────┤
│ 2  RESOURCES WITHIN 5 KM        See all ›      │
│    ┌───────────────────────────────────────┐ │
│    │ 💧 Check dam · 420 m · near            │ │  4 cards, then "See all"
│    │ [Useful]  Water 4 months; silt high    │ │
│    │ Source: MRSAC · Feb 2018 · To verify   │ │  trust label — never cut
│    └───────────────────────────────────────┘ │
│    chips: 5 Useful · 7 Partly · 2 Not useful   │
├──────────────────────────────────────────────┤
│ 3  YOUR OWN RESOURCES  (Told by you)           │
│    🐄 Cow ×2 · 🐐 Goat ×5 · ⚙ Pump             │
├──────────────────────────────────────────────┤
│ 4  WHERE YOU ARE HEADING                       │
│    headline + strengths + constraints + next   │
├──────────────────────────────────────────────┤
│ 5  IDEAS FOR YOU                               │
│    Build on your work │ Other options          │
│    #1 Dairy · [Good fit] · reason · wildlife   │
├──────────────────────────────────────────────┤
│ 6  WHY NOT OTHERS?   (removed + the gate)      │
├──────────────────────────────────────────────┤
│ 7  Weather & past disasters  [Sample]          │  M0: sample only, clearly labelled
├──────────────────────────────────────────────┤
│ Suggestion only. Check on the ground.          │  footer — never cut
│ The Gram Sabha decides.   Read our policy      │
└──────────────────────────────────────────────┘
```

Order note: the PDF's order is Header → Resources → Weather → Disasters → Ideas → Why-not → Schemes → Ask → Add details → Footer. M0 moves **"Where you are heading"** up front because it is what the villager asked for. Restore the PDF order when weather and disasters are real.

**Rendering rules**
- **No numbers for scores.** Only badges: Useful (green) / Partly useful (amber) / Not useful (red); Good / Fair / Weak fit. Colour carries meaning only (style guide).
- `inside_cfr` resources show **"Use only through the Gram Sabha"** and no "start this yourself" wording.
- Every resource and idea shows a **trust label**: source · source date · check status ("To be verified on the ground" / "Confirmed by committee"). Unknown date → "date not known". Never render a card without it.
- Anything from `told_by_you` carries the **"Told by you, not verified"** tag.
- Sample datasets show a visible **Sample** chip (L1).
- A report snapshot is **stable**; if the server says `newer_version_available`, show "A newer version of your report is available" with a refresh button.
- Reasons arrive as `{key, params}`; look the key up in `LivelihoodStrings` and substitute params (§7).

---

## 4. The intake form (S2): field spec

All optional except where stated. Save **to Hive first**, then sync (host is offline-first); a failed upload never loses what he typed.

| Step | Field | Control | Validation / notes |
|---|---|---|---|
| **1 Land** | Land area | Number + unit toggle: **hectare / acre / guntha** | Required for ideas, not for the resource list. `> 0`. Warn above 100 ha ("please check"). Convert to **hectares** on save: `ha = acre × 0.404686` · `guntha × 0.0101171` (40 guntha = 1 acre). Show the converted value back ("≈ 1.2 ha") |
| | Land type | 3 big chips: irrigated / rain-fed / mixed | |
| | Water on my land | Chips: open well / borewell / none | Decides if water-heavy ideas are possible |
| **2 Animals** | Counts for cows, buffalo, bullocks, goats/sheep, poultry, other | Steppers (− 0 +) with an animal icon each | Integers 0–999. These become **resources**, marked "Told by you" |
| **3 What I own** | Checklist with icons: well, borewell, farm pond, shed, pump, drip kit, bullock cart, storage room, vehicle, fodder land, other | Multi-select tiles | Also resources, "Told by you" |
| **4 Past work & money** | Last 3 years (short list: paddy, millets, pulses, vegetables, fruit, dairy, goat rearing, poultry, forest produce, labour, other) | Multi-select chips | Builds "Build on your work" |
| | Family members who can work | Stepper 0–15 | Sets how large an idea he can run |
| | Money I can invest | 3 chips: low / medium / high | Matches idea `cost_level`. **Never ask for income** (L8) |
| **5 Location** | Where is your land? | Map pin picker + "Use my current location" | Required for a **plot** report. Skip → **village report** from the village centre, and the report says so |

Footer on every step: *"Optional. Only you can see this. You can delete it any time."* After the last step: **"Show my report"**.

**Delete my answers:** a visible link on S1 → confirm dialog → `DELETE /profile` + clear the Hive cache (L8).

---

## 5. State, offline and errors

- **Riverpod** providers: `livelihoodRepositoryProvider` (switches Remote/Seed), `profileProvider` (AsyncNotifier), `reportProvider` (AsyncNotifier; `generate()`), `resourceFiltersProvider`.
- **Hive box `lv_cache`:** last saved profile, last report JSON, `cached_at`. Opening the report with no network shows the cached report plus a quiet **"Showing your last saved report"** line, never a blocking dialog.
- **Sync:** use the host's offline-first approach: write locally, send when connected, retry. Do not invent a second queue; reuse the host's pattern if it exposes one, otherwise a single `PUT /profile` retry on next open is enough for M0.
- **Errors:** `ApiClient` throws `ApiException(error, messageKey, details)`. Map `messageKey` → a plain-language string in the user's language. Never show a raw code. 409s do not occur here (no statutory blocks).
- **Empty states:** "No resources found within 5 km in our data. This does not mean there are none." (same spirit as L7) and a link to widen the radius if the server allows.
- Loading: shimmer (host has `shimmer`); the report call should feel instant on seed data.

---

## 6. UX rules for this module

1. **One thing per screen**, one main button at the bottom.
2. **Plain words, icons everywhere**, text input only, no voice.
3. **Suggestion wording**: "may help", "could suit", never "you qualify", "approved", "best", "guaranteed".
4. **Trust first**: source, date and check status are visible without tapping.
5. **Honest gaps**: show "Not yet checked on the ground", "date not known", "market access not checked". Never fill a gap silently.
6. **Red is rare.** Not-useful badge and (Phase 4) the harmful-question message; never for "incomplete".
7. **Safety is visible**: wildlife badge on every idea; "Ask the Forest Department first" when flagged.
8. Marathi is the default (host); language and theme switch from the host settings, and the report re-renders from keys, so no re-fetch is needed.
9. Test on a **small Android viewport**; nothing clipped in Marathi.

### Visual style

Follow the host tokens in `core/theme/app_colors.dart`: forest green `AppColors.forestCanopy` (`#1B4332`) for header and identity, saffron `AppColors.saffron` (`#FF7A00`) for main buttons, `context.colors` for surfaces/text so light and dark both work. The style-guide document quotes slightly different hex values (`#1A4331` / `#FF8D20`); **the code is the source of truth**, so use the tokens, never literal hex.

---

## 7. Strings (trilingual)

The host uses a hand-written `AppLocalizations` map (`services/localization_service.dart`, ~700 lines, `context.tr('key')`) rather than ARB files. To avoid merge conflicts and keep the feature portable:

- `livelihood_strings.dart` holds `const Map<String, Map<String, String>>` for `en`, `mr`, `hi`, and a tiny helper `lv(context, 'key', {params})` that falls back **mr → en**.
- Keys use the prefix `lv_`. Server `message_key`s (e.g. `reason.low_water_months`) map to `lv_reason_low_water_months`.
- **All Marathi/Hindi below is a machine-written draft and must be reviewed by a native speaker before any villager sees it.**

| Key | English | मराठी (draft) |
|---|---|---|
| `lv_title` | My Livelihood Report | माझा रोजगार अहवाल |
| `lv_card_title` | My Livelihood | माझा रोजगार |
| `lv_add_details` | Add your details | तुमची माहिती भरा |
| `lv_show_report` | Show my report | माझा अहवाल दाखवा |
| `lv_land_area` | How much land do you have? | तुमच्याकडे किती जमीन आहे? |
| `lv_animals` | Animals you own | तुमच्याकडील जनावरे |
| `lv_own_resources` | What you already have | तुमच्याकडे आधीच काय आहे |
| `lv_location` | Where is your land? | तुमची जमीन कुठे आहे? |
| `lv_use_my_location` | Use my current location | माझे सध्याचे ठिकाण वापरा |
| `lv_resources_near` | Resources within 5 km | ५ किमी परिसरातील साधने |
| `lv_useful` | Useful | उपयुक्त |
| `lv_partly_useful` | Partly useful | अंशतः उपयुक्त |
| `lv_not_useful` | Not useful | उपयुक्त नाही |
| `lv_heading` | Where you are heading | तुम्ही कोणत्या दिशेने जात आहात |
| `lv_ideas_for_you` | Ideas for you | तुमच्यासाठी कल्पना |
| `lv_why_not` | Why not others? | इतर का नाहीत? |
| `lv_told_by_you` | Told by you, not verified | तुम्ही सांगितले, पडताळलेले नाही |
| `lv_to_verify` | To be verified on the ground | प्रत्यक्ष जागेवर पडताळणी बाकी |
| `lv_not_checked` | Not yet checked on the ground | अजून प्रत्यक्ष तपासलेले नाही |
| `lv_gram_sabha_only` | Use only through the Gram Sabha | फक्त ग्रामसभेमार्फत वापरा |
| `lv_ask_forest` | Ask the Forest Department first | आधी वन विभागाला विचारा |
| `lv_sample` | Sample | नमुना |
| `lv_footer` | Suggestion only. Check on the ground. The Gram Sabha decides. | फक्त सूचना. प्रत्यक्ष जागेवर तपासा. निर्णय ग्रामसभा घेते. |
| `lv_no_record` | No record found in our data. This does not mean there were none. | आमच्या माहितीत नोंद आढळली नाही. याचा अर्थ घटना झाली नाही असा नाही. |
| `lv_delete_answers` | Delete my answers | माझी उत्तरे हटवा |

(Hindi: add after the English and Marathi screens work. It is first in the cut list.)

---

## 8. Testing

| Kind | What |
|---|---|
| `flutter analyze`, `flutter test` | Every commit |
| Unit | Unit conversion (acre/guntha/hectare), report JSON parsing, `message_key` → text with params, fallback mr → en |
| Widget | Report in each state: empty, partial profile, sample data, `inside_cfr` card, flagged idea (Forest Department), fewer than five ideas; Marathi + English; **dark theme** |
| Golden | The report in Marathi (catches clipped Devanagari) |
| Walkthrough | The M0 checklist in [MVP_SPRINT](MVP_SPRINT.md) §5, on a **real phone** and on the smallest emulator |
| Offline | Open the report in airplane mode → last report shown with the "last saved" line |

---

## 9. Frontend checklists

**M0**
- [ ] `LivelihoodRepository` + `Seed…` implementation (UI works with no server)
- [ ] Models + JSON parsing for the report contract ([BACKEND_PLAN](BACKEND_PLAN.md) §6)
- [ ] `livelihood_strings.dart` (en + mr)
- [ ] Widgets: trust label, badges, resource card, idea card, footer
- [ ] S1 home, S2 intake (5 steps), S3 location picker, S4 report, S5 resources
- [ ] Dashboard card + route registration in the host
- [ ] `Remote…` repository wired to the backend once it is up
- [ ] Hive cache of the last report

**Later**
- [ ] Idea detail, weather chart, schemes, Ask screen, policy page, Hindi, delete-my-answers screen, FRC confirm flow, offline refresh banner

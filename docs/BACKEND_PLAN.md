# VanMitra Module 4 — Backend Plan

> **Status:** v0.1 draft · Read [PROJECT_PLAN](PROJECT_PLAN.md) first; it wins on scope and rules.
> **Host:** `vanMitraAI/vanmitra_backend` (FastAPI + **MongoDB**). Conventions below are taken from the host code (`app/mongo.py`, `app/models/base.py`, `app/auth/deps.py`, `app/errors.py`).

The backend owns the **logic** (gates, labels, ranking, wording keys) and the **geo query**. The app never decides anything the server could get wrong.

> **Operating rule for this project:** nothing in this plan is run against the database by Claude. Index creation, seeding and imports are scripts **a person runs** (marked `[USER RUNS]`).

---

## 1. Where the code lives

Self-contained package, so merging is a copy plus a few one-line registrations ([INTEGRATION](INTEGRATION.md)):

```
vanmitra_backend/app/livelihood/
├── __init__.py
├── models.py          # Doc / TimestampedDoc classes (collections lv_*)
├── schemas.py         # Pydantic request/response shapes
├── router.py          # FastAPI router, mounted at /api/v1/livelihood
├── service.py         # use-cases: build_report(), save_profile(), nearby()
├── geo.py             # distance maths (Shapely + pyproj), centre-point logic
├── domain/            # PURE rules: no DB, no HTTP. The most tests live here
│   ├── units.py       #   acre / guntha / hectare conversion
│   ├── labels.py      #   U formula, Useful / Partly / Not useful, reasons
│   ├── gates.py       #   the 4 legal gates
│   ├── fit.py         #   F formula (M, K, P, E, G) and fit label
│   ├── wildlife.py    #   wildlife-risk badge
│   ├── analysis.py    #   "where you are heading" summary facts
│   └── config.py      #   weights, bands, radius, caps (defaults; DB overrides)
└── seed/              # idea library JSON, sample resources GeoJSON, schemes
vanmitra_backend/scripts/
├── load_livelihood_resources.py   # [USER RUNS] GeoJSON -> lv_resource
└── seed_livelihood.py             # [USER RUNS] ideas, config, demo geo
vanmitra_backend/tests/livelihood/ # unit (domain) + db tests (throwaway DB only)
```

**Rule of thumb** (host `BACKEND.md` §7): legal/scoring rule → `domain/`, table → `models.py`, shape → `schemas.py`, URL → `router.py`, plus a test.

---

## 2. Data model (MongoDB collections, prefix `lv_`)

Follow the host pattern: Pydantic `Doc`/`TimestampedDoc` with `COLLECTION`; ids are UUIDv7 (`new_id()`); dates stored as `YYYY-MM-DD`; times in UTC milliseconds; geometry as **GeoJSON** (WGS 84, `[lng, lat]`). Nothing here is `APPEND_ONLY`, because the landowner must be able to delete his answers (L8); the **report** is an immutable snapshot by convention, regenerated rather than edited.

| Collection | Key fields | Notes |
|---|---|---|
| `lv_profile` | `user_id` (unique), `village_id`, `land{area_ha, entered{value,unit}, land_type, water_on_land}`, `location{point, source: gps\|village_centre\|manual, accuracy_m}`, `livestock{cow,buffalo,bullock,goat_sheep,poultry,other}`, `assets[]` (codes), `past_work[]` (codes), `family_workers`, `money_level`, `created_at`, `updated_at` | **One per user.** Visible only to that user. `DELETE` clears answers (keeps the user) |
| `lv_resource` | `kind` (see §2.1), `name_mr`, `name_en`, `geom` (GeoJSON, any type), `centroid` (Point), `attrs{perennial, months_available, condition, silted, working, area_ha, road_access…}`, `district`, `taluka?`, `village_hint?`, `tag_hint` (cfr/village/none), `sensitive` (bool), `status` (active\|wrong), `source`, `source_date`, `confidence` (high\|medium\|low), `check_status` (to_verify\|confirmed), `dataset` (e.g. `sample_ozhar`, `nashik_team_v1`), `data_version` | Source data. `centroid` is what the 2dsphere search runs on |
| `lv_village_geo` | `village_id` (unique), `centroid` (Point), `boundary?` (Polygon), `cfr_polygons[]?`, `source`, `source_date` | **Needed because the host `Village` model has no coordinates** (verified in `app/models/people.py`) |
| `lv_idea` | `code`, `name_mr/en/hi`, `family`, `needs[]` (resource kinds or asset codes), `gate_flags{needs_sale_or_lease, hunting_trapping, timber_or_harm, not_in_cfr}`, `cost_level`, `best_season`, `wildlife_risk` (low\|medium\|needs_permission), `min_land_ha?`, `group_only`, `through_gram_sabha`, `E`, `G`, `tags[]` (water_hungry, heat_sensitive, flood_sensitive…), `p_hints{past_work[], animals[]}`, `status` (draft\|reviewed), `enabled` | **Editable table**; see [IDEA_LIBRARY](IDEA_LIBRARY.md) |
| `lv_config` | `key`, `value`, `updated_at` | Weights, bands, radius, caps. Code defaults in `domain/config.py`; DB values override |
| `lv_report` | `user_id`, `profile_snapshot`, `centre`, `radius_m`, `resources[]`, `told_by_you[]`, `analysis`, `ideas[]`, `removed[]`, `data_version`, `generated_at`, `lang_hint` | One **snapshot** per generation. Keep the latest few per user |
| `lv_weather_normal` *(later; sample in M0)* | `area_key`, `month` 1–12, `rain_mm`, `tmax_c`, `source`, `source_date`, `is_sample` | "Typical, from past years. Not a forecast." |
| `lv_disaster` *(later; sample in M0)* | `village_id?`, `district`, `kind`, `year`, `source`, `is_sample` | See L7 for the empty-case wording |
| `lv_scheme` *(Phase 3)* | `name`, `class` (govt\|ngo), `who_can_apply`, `documents[]`, `help_type[]`, `audience[]`, `official_url`, `last_checked_on`, `checked_by`, `is_sample` | Links only, never applications |
| `lv_chat_log` *(Phase 4)* | `user_id`, `q`, `a`, `lang`, `at` | User can see and delete. No voice |
| `lv_resource_check` *(Phase 6)* | FRC confirm/change/reject with photo + GPS; **append-only** | The checked value replaces the map value; every change logged |

### 2.1 Resource kinds (first release, PDF §7)

`water_body`, `well`, `water_structure` (check dam, farm pond…), `river`, `drainage_line`, `forest_compartment`, `conservation_reserve`, `wildlife_compartment`, `grazing_land` (from recognised CFR approvals whose purpose names grazing).
**Not sourced yet** (show "needs data" on ideas that depend on them): canal, borewell, farm field, road, market, minor forest produce area.

**User-told resources** are not stored in `lv_resource`; they come from `lv_profile` (`livestock`, `assets`) and are merged into the report as `told_by_you` with the tag "Told by you, not verified".

### 2.2 Indexes (add to `INDEXES` in `app/mongo.py`; created by `scripts/setup_mongo.py` `[USER RUNS]`)

```python
from pymongo import ASCENDING, GEOSPHERE, IndexModel

LIVELIHOOD_INDEXES = {
    "lv_profile":      [IndexModel([("user_id", ASCENDING)], name="user_unique", unique=True)],
    "lv_resource":     [
        IndexModel([("centroid", GEOSPHERE)], name="centroid_2dsphere"),
        IndexModel([("geom", GEOSPHERE)], name="geom_2dsphere"),
        IndexModel([("district", ASCENDING), ("kind", ASCENDING)], name="district_kind"),
        IndexModel([("dataset", ASCENDING), ("data_version", ASCENDING)], name="dataset_version"),
    ],
    "lv_village_geo":  [IndexModel([("village_id", ASCENDING)], name="village_unique", unique=True)],
    "lv_idea":         [IndexModel([("code", ASCENDING)], name="code_unique", unique=True)],
    "lv_config":       [IndexModel([("key", ASCENDING)], name="key_unique", unique=True)],
    "lv_report":       [IndexModel([("user_id", ASCENDING), ("generated_at", -1)], name="user_latest")],
}
```

> The host's `INDEXES` dict is merged by `ensure_indexes()`: add the entries there, not in a second place.

---

## 3. API (`/api/v1/livelihood`, JWT required)

Uniform errors from the host (`ApiError` / `RuleViolation`): `{error, message_key, details}`. Use `ApiError` for bad input and `403/404`; livelihood has **no statutory blocks**, so `RuleViolation` is not used.
**Scoping:** every route works only on the **current user's own** profile and reports; there is no `user_id` in the URL, so one user cannot ask for another's data.

| Priority | Method | Path | Purpose |
|---|---|---|---|
| **M0** | `GET` | `/profile` | The user's saved details (404 `livelihood.no_profile` if none) |
| **M0** | `PUT` | `/profile` | Save/replace details. Server converts land to hectares, validates ranges, derives `village_id` from the user's village role |
| **M0** | `DELETE` | `/profile` | Delete his answers (L8). Reports are deleted with them |
| **M0** | `POST` | `/report` | **Generate** a report from the current profile (+ optional `radius_m`). Returns the full report |
| **M0** | `GET` | `/report/latest` | The latest snapshot (also what the app caches for offline) |
| **M0** | `POST` | `/resources/nearby` | Body `{lat, lng, radius_m?, kinds?[]}` → labelled resources only. For the Resources screen and for quick demos without a saved profile |
| P1 | `GET` | `/ideas/{code}` | Idea detail for the current report: why suggested, needs, checks run, weather note |
| P1 | `GET` | `/meta` | Data version, radius default/cap, languages, dataset labels (is it Sample?) |
| Later | `POST` | `/ask` | Phase 4. Safety check → on-topic check → answer from the report only → number check |
| Later | `GET` | `/schemes` | Phase 3 |
| Admin | `POST` | `/admin/resources/import` | GeoJSON import. Prefer the script (§7); an endpoint is optional |

**Contract note:** reasons and wording are returned as **`message_key` + `params`**, never as finished Marathi text. The app renders the text from its strings (same approach as the host's error `message_key`s). This keeps three languages consistent and lets the app work from a cached report.

### 3.1 Error / message keys (draft)

`livelihood.no_profile` · `livelihood.invalid_land_area` · `livelihood.radius_too_large` (details: `max_m`) · `livelihood.no_location` · `livelihood.no_village` · `livelihood.no_resources_found` (not an error: an empty list plus this key in `analysis.notes`) · `livelihood.dataset_is_sample` (flag, not an error).

---

## 4. Nearby-resource query

Goal: **every resource within `radius_m` (default 5000) of the centre point, with an exact distance, in under ~1 s.**

1. **Centre point** (`geo.centre_for(profile, village)`):
   `profile.location.point` (source `gps`/`manual`) → else `lv_village_geo.centroid` (source `village_centre`) → else error `livelihood.no_location`. The report records which one was used so the header can say *"measured from your plot"* or *"from your village centre"*.
2. **Candidate search (Mongo):** `$geoIntersects` on `lv_resource.geom` with a **circle polygon** around the centre (`geo.circle_polygon`, a 64-sided polygon **circumscribed** around the true circle so it never loses a resource), plus `{status: "active", sensitive: false}` and optional `district`/`kind` filters. Index: `geom_2dsphere`. *(Built and tested in slice 1 as `circle_polygon`; the Mongo call itself arrives in slice 2.)* A centroid-radius search with a fixed margin was rejected: a large polygon's centroid can be far further than its nearest edge (the sample set has one: edge 4.1 km, centroid 6.6 km).
3. **Exact distance (Python):** for each candidate, distance from the centre to the **nearest point of its geometry** (point, line or polygon edge; **0 m if the centre is inside a polygon**). Compute in a **local azimuthal-equidistant projection centred on the plot** (pyproj `Proj(proj="aeqd", lat_0=…, lon_0=…)`). This is accurate anywhere in Maharashtra and avoids picking a UTM zone (Vidarbha lies in zone 44, the west in zone 43). Keep only `distance_m ≤ radius_m`.
4. **Tag** each as `inside_cfr` (centre or resource lies within a `lv_village_geo.cfr_polygons` polygon, or `tag_hint == cfr`), `inside_village` (within `lv_village_geo.boundary`), else `near`.
5. **Sort** by distance; **label** each (§5.1); return.

> **Why the exact distance is computed in Python:** MongoDB's distance for non-point GeoJSON is not guaranteed to be edge distance, so the database only **finds candidates**. The exact distance is computed in step 3 (`geo.distance_to_geometry_m`, tested at 4,999 m / 5,001 m).
> **Protected-area layers** (`wildlife_compartment`, `conservation_reserve`) are found by the same query but are **not listed** as resources: they feed only the wildlife check ("Ask the Forest Department first" when within `PROTECTED_NEAR_M`, 2 km). **Community resources** (`inside_cfr`) **do** count towards an idea but flag it "Use only through the Gram Sabha" (rule L3); they are never excluded, because dairy and goat ideas depend on CFR-approved grazing land.
> **Ranking order** (built in slice 1): with details given, ideas that build on his own work (past work, animals) come first, best fit first, and a *Weak* fit never jumps the queue; with no details it is one list by fit. Ideas that pass the gates but miss the top five appear in "Why not others?" as **held back** (`gate: null`).
> **Nagpur trap (PDF §14):** Vidarbha districts 08–13 (incl. Nagpur 09) have portal map data shifted ~6° west of the true position. The earlier prototype corrects this; **keep that correction in the loader**, not in the query. See [DATA_PLAN](DATA_PLAN.md) §5.
> **Google satellite tiles are never cached or served offline** (L11).

Performance: seed data is small; real data needs the two 2dsphere indexes. Load-test the query (target < 1 s p95) before Phase 3.

---

## 5. Domain rules (pure Python in `domain/`)

All numbers below are **starting values** from the PDF unless marked *proposed*. They live in `domain/config.py` and `lv_config`, so the admin can tune them (PDF §9). Anything with no data = **0.5** (L6).

### 5.1 Resource label (`labels.py`)

```
U = 0.35·A + 0.25·C + 0.25·S + 0.15·R          # each term in [0, 1]
U ≥ 0.70  → USEFUL
0.40 ≤ U < 0.70 → PARTLY_USEFUL
U < 0.40  → NOT_USEFUL
```

| Check | Question | How we derive it from map data |
|---|---|---|
| **A** availability | Holds water / produces in the main season? | Water layers: perennial → 1.0, seasonal → 0.5, dry/none → 0.0. Forest/grazing: 0.5 until checked. Unknown → 0.5 |
| **C** condition | Working, not silted or broken? | `silted`/`working` flags → 1.0 good, 0.5 unknown, 0.2 poor. Unknown → 0.5 |
| **S** season span | Months per year usable | `months_available / 12`. Unknown → 0.5 |
| **R** reach | Can he get there; serves enough area? | *Proposed* distance bands: ≤ 1 km → 1.0; ≤ 3 km → 0.7; ≤ 5 km → 0.4; beyond → 0.2. If `road_access` is known, ×1.0 / ×0.8. Tune after field tests |

Each resource returns: `label`, `reason` as `{key, params}` (the weakest or most informative check, e.g. `reason.low_water_months {months: 4}`), `checked_on_ground` (bool), and `unknown_checks[]` so the card can say **"Not yet checked on the ground"**. The numeric `U` is stored in the snapshot for audit but **never sent to display** (L5; keep it under an internal `_u` field the app ignores, or omit it from the response and keep it in the snapshot only).

**Sensitive flag:** every resource has `sensitive`. Sensitive resources (sacred groves, rare species) are **not returned** in the user-facing response until a policy exists. No such layer is loaded in the first release.

### 5.2 Gates (`gates.py`)

An idea is dropped if it fails any gate; the report records **which** gate (the "Why not others?" list).

| Gate | Rule | Legal base (PDF §9, to be confirmed by an FRA lawyer) |
|---|---|---|
| `LAND_SALE_OR_LEASE` | Idea needs the land sold or leased | FRA Sec 4(4) |
| `HUNTING_OR_TRAPPING` | Involves hunting or trapping | Sec 3(1)(l) |
| `TIMBER_OR_HARM` | Cuts timber or harms wildlife or sensitive places | Sec 5 |
| `NOT_ALLOWED_IN_CFR` | Not allowed in community forest | CFR rules; forest-law expert |

Not dropped, but **flagged** on the idea card:
- village approval purposes do not cover the idea → "Check the approval purpose";
- plot is inside or near a protected area (`wildlife_compartment` / `conservation_reserve` within `PROTECTED_NEAR_M`, *proposed* 2000 m) → **"Ask the Forest Department first"** and wildlife risk = `needs_permission`;
- `group_only` ideas → "Works only as a group through the Gram Sabha";
- ideas needing data we lack (canal, farm field) → "needs data".

### 5.3 Fit and ranking (`fit.py`)

```
F = 0.35·M + 0.20·K + 0.15·P + 0.15·E + 0.15·G
```

| Part | Meaning | M0 implementation |
|---|---|---|
| **M** | How useful the resources the idea needs are | Mean `U` of the best-matching nearby resource per need (or the user's own asset). A need with **nothing within the radius → 0** and the card says what is missing. Weather/disaster tags raise or lower M (§5.5) |
| **K** | Market access (distance, road to a buyer) | **0.5 for everyone** until a market layer exists (markets are not sourced). Card says "market access not checked" |
| **P** | People fit: skills, past work, animals, family workers | From the profile: past-work match +, animals owned match +, family workers vs the idea's labour need. No profile → 0.5 |
| **E** | Ease of start (money, training) | Library `cost_level` vs the user's `money_level`: match 1.0, one step off 0.6, two steps 0.2. No money answer → library `E` |
| **G** | Green fit (forest, water, wildlife) | Straight from the library |

**Land area (the user's input) matters in two places:** (a) a hard feasibility note when `land.area_ha < idea.min_land_ha` ("needs about X ha; you entered Y") which lowers `E` and appears on the card, (b) farm-land ideas (millets, pulses, agroforestry) only appear when he has land. `min_land_ha` is a **library field to be set by the agriculture expert**; the draft values in [IDEA_LIBRARY](IDEA_LIBRARY.md) are placeholders.

**Livestock matters in three places:** animals owned are `told_by_you` resources (their own cards), they lift **P** for dairy / goat / poultry / fodder ideas, and the analysis checks **fodder and water within the radius** for the animals he keeps (a fact-based note, not a computed intake).

**Fit label** *(proposed; the PDF says "a fit label" but gives no bands)*: `F ≥ 0.70` **Good fit** · `0.40–0.69` **Fair fit** · `< 0.40` **Weak fit**.

**Show five:** sort by `F` descending, take 5. If fewer than five pass the gates, show fewer and attach `notes: ["fewer_than_five"]`. **Two states** (PDF §9): with no details → one ranked list plus a banner "add details"; with details → split into **Build on your work** (ideas matching `past_work`/animals/land) and **Other options**.

### 5.4 Wildlife risk (`wildlife.py`)

`low` · `medium` · `needs_permission`. Derived from the idea type (library field) and from nearby `wildlife_compartment` / `conservation_reserve` / forest layers. Ideas that bring people into the forest (collection, tourism, fire-line work) are at least `medium`. The label is "check with the Forest Department", never "safe".

### 5.5 Weather and disaster tags (M0: light)

Ideas carry tags (`water_hungry`, `heat_sensitive`, `flood_sensitive`). In M0 the weather/disaster section is **sample data labelled Sample** and only produces a simple multiplier on `M` plus a note ("possible flood risk" if the plot is within `FLOOD_NEAR_M` of a `river`/`drainage_line`, *proposed* 300 m). Real weather comes later. Weather copy: **"Typical, from past years. Not a forecast."**

### 5.6 "Where you are heading": the analysis block (`analysis.py`)

A structured summary built **by code from facts**, no free-form AI in M0:

```jsonc
"analysis": {
  "headline": {"key": "analysis.headline.dairy_and_vegetables", "params": {}},
  "strengths":   [{"key": "analysis.water_nearby", "params": {"count": 3, "nearest_m": 420}}],
  "constraints": [{"key": "analysis.low_water_months", "params": {"months": 4, "name_ref": "res_17"}}],
  "own_resources": [{"key": "analysis.you_have_animals", "params": {"cow": 2, "goat_sheep": 5}}],
  "next_steps":  [{"key": "analysis.verify_with_frc"}, {"key": "analysis.ask_forest_dept_if_near_protected"}],
  "notes":       ["profile_incomplete", "market_not_checked", "dataset_is_sample"]
}
```

`headline` is chosen from the **top idea family** and the biggest constraint. Every statement cites the part of the report it came from (the "From: …" pattern the Ask box will reuse in Phase 4).

---

## 6. Report snapshot (the contract the app builds against)

`POST /report` and `GET /report/latest` return this shape (trimmed). **No numeric scores in the display fields (L5).**

```jsonc
{
  "id": "…uuidv7…",
  "generated_at": "2026-10-15T01:30:00Z",
  "data_version": "sample_ozhar_v1",
  "is_sample_data": true,
  "newer_version_available": false,
  "header": {
    "name": "…", "village": {"id": "…", "name_mr": "ओझर", "name_en": "Ozhar"},
    "report_level": "plot",                       // "plot" | "village"
    "centre": {"lat": 19.78, "lng": 73.22, "source": "gps"},
    "radius_m": 5000,
    "cfr_status": null,                           // from Module 2 later
    "trust": {"source": "…", "source_date": "…", "check_status": "to_verify"}
  },
  "resources": [
    {
      "id": "…", "kind": "well", "name_mr": "…", "name_en": "…",
      "distance_m": 420, "tag": "near",           // inside_cfr | inside_village | near
      "label": "useful",                          // useful | partly_useful | not_useful
      "reason": {"key": "reason.perennial_good_condition", "params": {}},
      "checked_on_ground": false,
      "unknown_checks": ["condition"],
      "use_only_through_gram_sabha": false,       // true when tag == inside_cfr
      "trust": {"source": "MRSAC water layer", "source_date": "2018-02", "check_status": "to_verify", "confidence": "medium"}
    }
  ],
  "counts": {"useful": 5, "partly_useful": 7, "not_useful": 2, "total": 14},
  "told_by_you": [
    {"kind": "animal", "code": "cow", "count": 2, "tag": "told_by_you"},
    {"kind": "asset",  "code": "pump", "tag": "told_by_you"}
  ],
  "analysis": { "…see §5.6…" },
  "ideas": [
    {
      "rank": 1, "code": "dairy_small", "name_mr": "…", "name_en": "…",
      "group": "build_on_your_work",              // or "other_options"
      "fit": "good",                              // good | fair | weak
      "reason": {"key": "idea.reason.animals_and_water", "params": {"water_m": 420}},
      "resources_used": ["res_17", "told:cow"],
      "cost_level": "medium", "best_season": "year_round",
      "wildlife_risk": "low",
      "flags": ["group_only?", "ask_forest_dept?", "check_approval_purpose?", "needs_data?"],
      "schemes_count": 0
    }
  ],
  "removed": [
    {"code": "…", "name_mr": "…", "name_en": "…", "gate": "TIMBER_OR_HARM", "reason": {"key": "gate.timber_or_harm"}}
  ],
  "weather": {"is_sample": true, "months": [{"m": 1, "rain_mm": 0, "tmax_c": 31}]},
  "disasters": {"is_sample": true, "items": [], "none_found_notice": true},
  "footer_key": "footer.suggestion_only"
}
```

---

## 7. Data loading `[USER RUNS]`

- `scripts/load_livelihood_resources.py <file.geojson> --dataset <name> --version <v> [--district <d>] [--dry-run]`
  - Reads a GeoJSON FeatureCollection (shape in [DATA_PLAN](DATA_PLAN.md) §3), validates every feature, computes `centroid`, applies the Vidarbha correction **only if** `--apply-vidarbha-shift` is passed, writes in batches, prints a summary (counts by `kind`, rejects with reasons).
  - `--dry-run` writes nothing. Always run it first.
  - **Never** points at the production database without an explicit flag; follows the host's `VANMITRA_TEST_MONGODB_DB` convention for tests.
- `scripts/seed_livelihood.py`: idea library, config defaults, demo `lv_village_geo` for Ozhar, sample weather/disaster rows. Safe to run again (upsert by `code`/`key`).
- Both reuse the host's `get_database()` and respect `.env` (`VANMITRA_MONGODB_URI`). They are **not** run by Claude.

---

## 8. Security and privacy

- All routes need the host JWT; the current user comes from `CurrentUser`; **no route takes a `user_id`**.
- The village for a user is derived from his `villager` / `gram_sabha` role grant (`UserRole`), not from the request body.
- Profile and report documents are readable **only by their owner**. Admin back-office accounts do **not** bypass this (matches the host principle that admin does not read case content).
- No caste, income, ID numbers, or voice (L8). Rate-limit `/report` (it does geo work) when moving past M0.
- Future AI calls: server-side only; the key lives in `.env` (`VANMITRA_…`), never in the app (L12); log question and answer, not audio.

---

## 9. Testing

| Kind | Tool | What |
|---|---|---|
| Unit | `pytest` (+ `hypothesis` for the formulas) | `domain/`: unit conversion, `U`, bands, gates, `F`, fit label, wildlife flag, analysis keys. **Aim for full branch coverage of `domain/`** |
| Geo | `pytest` + Shapely | distance to point/line/polygon edge; centre inside polygon → 0; tag selection |
| DB | `pytest -m db` against a **throwaway** Mongo DB (`VANMITRA_TEST_MONGODB_URI`) | `$geoIntersects` candidate search, profile CRUD, owner-only access |
| Contract | OpenAPI at `/docs` | The report shape in §6 stays in step with the app |
| Safety (Phase 5) | fixed list | Zero shown ideas that break a gate; every idea has a wildlife-risk badge |

Host checks: `ruff check`, `ruff format --check`, `mypy app scripts`, `pytest -q`.

---

## 10. Backend checklists

**Slice 1: done (branch `backend`)** — 60 tests, ruff + strict mypy clean, no database
- [x] Scaffold (FastAPI, config, host-style errors), `/api/v1/health`
- [x] `schemas.py` (the report contract) and `domain/*` (`units`, `config`, `labels`, `gates`, `fit`, `wildlife`, `analysis`)
- [x] `geo.py`: centre, exact distance (point / line / polygon edge), tags, circle polygon
- [x] `service.build_report()` (pure: profile + records in, report out)
- [x] Draft idea library (13 + 3 gate demos), generated **Sample** dataset (12 features), demo village, sample weather
- [x] Stateless demo routes: `GET /livelihood/meta`, `POST /livelihood/demo/report` (no login, no database; switch `VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS`)

**Slice 2: next (needs a database and the host auth)** — a person runs the DB steps
- [ ] `models.py` (`lv_*` documents) and the host `Store` / auth wiring; `lv_*` indexes added to `INDEXES` (user runs `setup_mongo.py`)
- [ ] `PUT/GET/DELETE /profile` (owner-only)
- [ ] `$geoIntersects` candidate query replacing the in-memory list
- [ ] `POST /report`, `GET /report/latest`, `POST /resources/nearby`
- [ ] `seed_livelihood.py` + `load_livelihood_resources.py` (user runs, `--dry-run` first)
- [ ] Router registered in the host `api/v1/__init__.py`

**Later**
- [ ] `/ideas/{code}`, `/meta`
- [ ] Weather + disaster sources; `lv_scheme`
- [ ] `/ask` with safety check and number check
- [ ] Scheduled refresh of the resource copy every 4–5 days; "newer version available" flag
- [ ] FRC field-check endpoints (`lv_resource_check`)

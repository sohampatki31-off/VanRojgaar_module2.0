# VanMitra Module 4 — Data Plan

> **Status:** v0.1 draft · The report is **only as good as its data** (Module 4 PDF §14). This is the least certain part of the project, so read it before promising anything about accuracy.

---

## 1. What data the module needs

| Data | Used for | Where it comes from | Status today |
|---|---|---|---|
| **Resources**: water bodies, wells, water structures (check dams, farm ponds), rivers, drainage lines, forest compartments, conservation reserve, wildlife compartments | The "resources within 5 km" list and the labels | **MRSAC** (state remote-sensing centre) layers, copied into our own database after permission; refreshed every 4–5 days | **Permission not yet in writing.** No resource data exists in this folder or in the host repo |
| **Grazing land** | Fodder / goat / dairy ideas | Recognised **CFR approvals** whose purpose names grazing (district approval sheet; Nagpur: 705 approvals, as of Feb 2018) | Nagpur only; not loaded |
| **Village centre and boundary, CFR polygons** | Fallback centre point; `inside_village` / `inside_cfr` tags | Module 2 (Atlas) later; host stores CFR boundaries as GeoJSON polygons on `cfr_boundary` | Host backend `Village` has **no coordinates**. The Flutter app has Ozhar constants only (`VillageConstants`: 19.78, 73.22, *approximate*) |
| **The landowner's own details** | Profile, "Told by you" resources | The user, via the Add-details form | In design ([FRONTEND_PLAN](FRONTEND_PLAN.md) §4) |
| **Idea library** | Gates and ranking | Our experts; editable table | 13 **draft** ideas in [IDEA_LIBRARY](IDEA_LIBRARY.md), not expert-reviewed |
| **Weather normals** | Weather section, tags that move ranking | One free service, called from the backend; **terms to be checked first** | Not chosen. M0 uses **Sample** numbers |
| **Past disasters** | Disaster section | District and state records, collected by hand with source and year | Not found yet. M0 uses **Sample** |
| **Schemes** | Schemes tab | Official pages, myScheme; hand-checked register (`SCHEMES.md`) | Not started |

### Files that exist and what they can and cannot do

| File (in `vanMitraAI/`) | Contents | Useful for Module 4? |
|---|---|---|
| `Ozar_Village_Dataset_final_f.csv` | 147 claimant rows for **Ozar**: survey no., area (sq m), category, names. **No coordinates** (verified) | ✅ Only to make **realistic demo land areas** (the `Area_sqm` column) and survey-number examples. ⚠️ Contains **personal names**: never copy names into demo data or screenshots (DPDP Act 2023) |
| `documents/mh_cfr_potential_villages.xlsx` | ~17,000 Maharashtra villages: district, GP, village code, area (ha), ST population, forest-inside-boundary (ha), 2 km buffer potential. **No coordinates** | ⚠️ Not for the radius search (no geometry). Possibly for CFR "potential" status later (Module 2) |
| `vanmitra_backend/assets/seed_data/ozar_alerts.csv`, `siamese_change_model.pt` | Module B satellite alert seed | ❌ Not resources |
| Team's **Nashik** survey-number and resource files (PDF §14, §17) | Survey numbers + resources | ❓ **Not in this folder.** Needed. See [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q1 |

---

## 2. Rules for all data (PDF §14)

1. **Official sources only.** No scraping of web pages. Use formal data requests, published open-data portals with a clear licence, or the landowner's own words.
2. **Every record keeps `source`, `source_date` and `confidence`** (High if confirmed on the ground · Medium if from an official layer and not yet checked · Low if guessed, old or incomplete).
3. **Store maps in WGS 84** (EPSG:4326, GeoJSON `[lng, lat]`). Measure area and distance **on the earth's surface**, never on raw degrees (we use a local projection per query, see [BACKEND_PLAN](BACKEND_PLAN.md) §4).
4. **Confirm each source's terms of use in writing before any launch.**
5. **No source is perfect.** An official map can show a well that is dry or gone. We never say "true"; we say "official source, with date, **to be verified on the ground**". Field checks by the FRC improve it later (Phase 6).
6. **Demo data must say so.** Anything not from a real source is `is_sample: true`, and the app shows a visible **Sample** chip (rule L1). This applies to every demo dataset below.
7. **Candidate / "forest" plots are guesses** from land-record text and are never shown as legal eligibility (rule L9).
8. **Sensitive places** (sacred groves, rare species) carry `sensitive: true` and are not shown outside the owner's context. No such layer in the first release.

---

## 3. The seed file format (source-neutral)

The loader accepts **one GeoJSON FeatureCollection per dataset**, so any source (MRSAC export, team files, a sample) goes through the same door.

```jsonc
{
  "type": "FeatureCollection",
  "dataset": "sample_ozhar",          // required, becomes lv_resource.dataset
  "data_version": "v1",               // required
  "is_sample": true,                  // required: true for anything not from a real source
  "source": "VanMitra sample data (synthetic)",   // required, human-readable
  "source_date": "2026-10-14",        // required; "unknown" allowed → shows "date not known"
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [73.2203, 19.7811] },   // Point | LineString | Polygon
      "properties": {
        "kind": "well",                       // required: one of the kinds in BACKEND_PLAN §2.1
        "name_mr": "…", "name_en": "Village well",
        "district": "Palghar", "taluka": "Jawhar",
        "tag_hint": "none",                   // cfr | village | none
        "sensitive": false,
        "confidence": "low",                  // high | medium | low
        "check_status": "to_verify",          // to_verify | confirmed
        "attrs": {                            // all optional; missing = 0.5 ("not yet checked")
          "perennial": true,
          "months_available": 8,
          "condition": "good",                // good | fair | poor
          "silted": false,
          "working": true,
          "road_access": true,
          "area_ha": 0.02
        }
      }
    }
  ]
}
```

**Validation the loader enforces** (reject the feature, count it, print the reason): geometry valid (`shapely.is_valid`); coordinates inside Maharashtra's rough bounding box (lat 15.5–22.1, lng 72.5–80.95); `kind` in the allowed list; `source`, `source_date` present; polygons not absurdly large (> 50,000 ha flagged); duplicate `(kind, centroid)` within 5 m flagged.

---

## 4. Getting data for tomorrow (M0), in order of preference

| Option | What | Pros | Cons | Do it if… |
|---|---|---|---|---|
| **A. Team's Nashik files** | Convert the existing survey-number + resource files to the seed format | Real data, matches the PDF pitch story | Not in this folder; unknown format/location/permission to show; first check: *do survey numbers have a location?* (PDF §17: if not, list resources by village) | The team confirms the files and may show them |
| **B. Open government layers** (e.g. India-WRIS water data, NRSC Bhuvan) | Download with the licence recorded | Official, free | Licence/terms must be checked; download + clean time; unlikely to be done overnight | Licence is clear and time allows |
| **C. OpenStreetMap extract** | Water, wells, forest, landuse around the demo village from the open OSM database | Fast, free, open licence (ODbL, needs attribution) | Not "official"; patchy in rural India; **conflicts with PDF §14 "official sources only"**, so the decision is the owner's, not ours. Must be labelled "OpenStreetMap contributors" | The owner explicitly accepts it as a stopgap |
| **D. Synthetic Sample set** | ~15–25 hand-made features scattered within 5 km of the demo village, **every one `is_sample: true`** | Zero dependencies, deterministic, shows every label/state (Useful, Partly, Not, inside-CFR, near-protected-area, missing data) | **Not real**; the pitch must say so | Always; it is the **guaranteed fallback** |

**Default plan:** build **D** first (it is the test fixture anyway), slot **A** in the moment it is available. Never mix a sample dataset into a real one: they have different `dataset` names, and `lv_report.is_sample_data` is true if **any** resource shown is a sample.

### 4.1 The Sample set must cover these cases (so the UI and rules are exercised)

- a perennial well at < 500 m (Useful) and a seasonal check dam at ~2 km, silted (Partly useful)
- a dry pond (Not useful) and a river at ~3 km
- a resource **inside CFR** → "Use only through the Gram Sabha"
- a `wildlife_compartment` within `PROTECTED_NEAR_M` → idea flagged "Ask the Forest Department first"
- a resource with **all `attrs` missing** → "Not yet checked on the ground"
- a **large polygon** whose centroid is > 5 km but whose edge is < 5 km (tests exact-distance logic)
- one resource at **exactly the boundary** (4,999 m / 5,001 m)
- grazing land (so goat / dairy ideas have fodder)
- a village where **nothing** is within 5 km (empty state)

---

## 5. The Nagpur / Vidarbha coordinate trap

PDF §14: **Nagpur is district 09, one of six Vidarbha districts (08–13) whose portal map data sits about 6 degrees west of the true position.** The earlier prototype corrects this; **keep the correction.** Implement it in the **loader** (`--apply-vidarbha-shift`, off by default), never in queries. Add a test with a known Nagpur point. This is irrelevant for Nashik or Palghar data, so do **not** enable it for them.

> The exact correction used by the earlier prototype is not in this folder. Get it from the team before loading any Vidarbha data. Do not guess the offset.

---

## 6. Demo profile and village data

| Item | Value / source | Notes |
|---|---|---|
| Demo villager and village | Host demo seed: Ozhar, Jawhar, Palghar (see host `frontend_backend.md` §A2 for the demo login) | The PDF pitch is **Nashik**; see Q2 |
| Village centre | Ozhar ≈ **19.7800 N, 73.2200 E** from `VillageConstants` (**approximate**) | Put in `lv_village_geo` with `source: "approximate (VillageConstants)"` |
| CFR polygon for Ozhar | `VillageConstants.cfrBoundaryPolygon` (approximate, 10 points) | Use only as a demo `inside_cfr` polygon; label it |
| Demo land areas | Realistic values from the `Area_sqm` column of the Ozar CSV (convert sq m → ha) | **Areas only; no names** |

---

## 7. Refresh and versioning (Phase 3)

- A scheduled job re-copies the source into `lv_resource` every **4–5 days** (PDF §7). Each load has a `data_version`.
- A report stores the `data_version` it used. If the live version is newer, the app shows **"A newer version of your report is available"**.
- Resources the FRC marks wrong leave the scores but stay in the history (Phase 6, `lv_resource_check`).
- Estimates from the PDF: permission takes **weeks** (slowest part); loading one district takes **1–2 days**; the whole state **1–2 weeks**.

---

## 8. Data checklist

**M0**
- [ ] Decide the data option (A–D) for tomorrow: [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q1
- [ ] Sample set (D) in the seed format, covering §4.1
- [ ] Loader with `--dry-run` and the validations in §3
- [ ] `lv_village_geo` for the demo village
- [ ] Record, for **any** real dataset: where it came from, its date, and whether we may show it outside the team (PDF §14)

**Before any real launch**
- [ ] Written data permission (MRSAC or other source), with licence terms
- [ ] Which department sends the MRSAC request, and under what licence we may copy and refresh
- [ ] Disaster records source; weather source and terms
- [ ] DPDP Act 2023 review for profile data

# VanMitra Module 4 — Idea Library (DRAFT)

> **Status:** ⚠️ **DRAFT. NOT reviewed by a forest-law expert, an agriculture expert, an animal-welfare NGO or the Forest Department.** The Module 4 PDF (§9, §12) requires that review **before launch**. Until then, the app must treat these as pitch/prototype content and say so.
> Loaded into `lv_idea` by `scripts/seed_livelihood.py` `[USER RUNS]`. Stored as an **editable table**; the System Administrator edits it later.

The PDF asks for about 20 ideas, with 10–12 hand-written ideas for the pitch (§17). This draft has **13 ideas + 3 gate-demo entries**. Marathi names are draft and need a native-speaker review.

---

## 1. Fields

| Field | Meaning |
|---|---|
| `code` | Stable id, snake_case |
| `name_en` / `name_mr` | Display names (hi later) |
| `family` | Group from PDF §9: `forest_produce`, `pond_dam_tank`, `well`, `grazing`, `community_forest`, `mushroom`, `farm_land`, `livestock` |
| `needs` | What must be within reach: resource kinds (`water_body`, `well`, `water_structure`, `grazing_land`, `forest_compartment`) and/or user assets/animals (`cow`, `pump`, `shed`, `fodder_land`…). `OR` groups allowed |
| `gate_flags` | `needs_sale_or_lease`, `hunting_trapping`, `timber_or_harm`, `not_in_cfr` (all false for shown ideas) |
| `cost_level` | `low` / `medium` / `high` (matched against the user's money level) |
| `best_season` | `kharif`, `rabi`, `summer`, `year_round`, `post_monsoon` |
| `wildlife_risk` | `low`, `medium`, `needs_permission` (raised by nearby protected layers) |
| `min_land_ha` | **Placeholder**: minimum own land (ha) for the idea; to be set by the agriculture expert. `null` = no land needed |
| `group_only` | Works only as a group through the Gram Sabha → shows "Works only as a group through the Gram Sabha" |
| `through_gram_sabha` | Uses community forest/pond: "Use only through the Gram Sabha" |
| `tags` | Weather/disaster tags: `water_hungry`, `heat_sensitive`, `flood_sensitive` |
| `E`, `G` | Ease of start and green fit, each 0–1, **starting values** by the content owner |
| `p_hints` | Past-work and animal codes that raise people-fit (P) |

---

## 2. The draft ideas

| # | `code` | Idea (en / mr draft) | Family | Needs | Cost | Season | Wildlife | `min_land_ha` | Group / GS | Tags | E | G | `p_hints` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `dairy_small` | Small dairy / दुग्धव्यवसाय | livestock | water (well/pond/borewell) **and** fodder (grazing land or fodder land) | medium | year_round | low | 0.2 | — | water_hungry, heat_sensitive | 0.6 | 0.6 | cow, buffalo, dairy |
| 2 | `goat_rearing` | Goat rearing / शेळीपालन | livestock | grazing land **or** farm margin; water | low | year_round | low (↑ near forest edge) | 0.1 | group optional | — | 0.7 | 0.6 | goat_sheep, goat rearing |
| 3 | `backyard_poultry` | Backyard poultry / परसबागेतील कुक्कुटपालन | livestock | small shed/space; water | low | year_round | low | 0.0 | — | heat_sensitive | 0.8 | 0.7 | poultry |
| 4 | `vegetables_drip` | Drip vegetables / ठिबक भाजीपाला | well | well/borewell/pond water; own land | medium | rabi, summer | low | 0.1 | — | water_hungry, heat_sensitive | 0.5 | 0.6 | vegetables |
| 5 | `mushroom_shed` | Mushroom farming / अळिंबी शेती | mushroom | small shed, straw, little water; **no forest needed** | low | year_round | low | 0.0 | — | heat_sensitive (note: keep the shed cool) | 0.7 | 0.9 | — |
| 6 | `plant_nursery` | Plant nursery / रोपवाटिका | well | water; own land | medium | post_monsoon | low | 0.1 | — | water_hungry | 0.5 | 0.9 | vegetables, fruit |
| 7 | `millets_pulses` | Millets and pulses / नाचणी, कडधान्ये | farm_land | own land (rain-fed OK) | low | kharif | low | 0.25 | — | — | 0.7 | 0.9 | millets, pulses, paddy |
| 8 | `agroforestry_fruit` | Fruit trees on bunds / बांधावर फळझाडे | farm_land | own land; water for first 2 years | medium | kharif | low | 0.25 | — | water_hungry (early years) | 0.5 | 1.0 | fruit |
| 9 | `beekeeping_box` | Box beekeeping on own land / मधमाशीपालन | forest_produce | own land near flowering plants or forest edge | low | post_monsoon | low | 0.0 | — | — | 0.6 | 0.9 | — |
| 10 | `fodder_bank` | Fodder bank / चारा बँक | grazing | grazing land (community) | low | year_round | low | — | **group_only, through_gram_sabha** | flood_sensitive | 0.6 | 0.8 | cow, buffalo, goat_sheep |
| 11 | `fish_pond_group` | Fish culture in a village pond / तलावातील मत्स्यपालन | pond_dam_tank | pond/tank with water most of the year | medium | post_monsoon | low | — | **group_only, through_gram_sabha** | water_hungry, flood_sensitive | 0.4 | 0.7 | — |
| 12 | `mfp_collection_group` | Minor forest produce (honey, bamboo, lac) through the Gram Sabha / वनोपज | forest_produce | forest compartment / CFR | low | post_monsoon | **medium** (collection brings people into the forest) | — | **group_only, through_gram_sabha** | — | 0.5 | 0.7 | forest produce |
| 13 | `forest_watch_work` | Community forest work: fire-line, patrol, watershed, nature guide / वन संरक्षण कामे | community_forest | CFR forest | low | summer | **medium → needs_permission near protected areas** | — | **group_only, through_gram_sabha** | — | 0.4 | 1.0 | — |

Notes
- **Tendu leaves** are intentionally *not* listed: collection is regulated by the state and needs expert input before we suggest it (PDF lists tendu only as a family example).
- **Medicinal plants (jadibuti)** are **on hold** (PDF §1, §9): only an expert can identify them. Do not add until the expert exists.
- Ideas that depend on canals, farm fields, roads or markets (not sourced yet) show **"needs data"** rather than a made-up answer.
- `K` (market access) is **0.5 for every idea** until a market layer exists.

---

## 3. Gate-demo entries (for "Why not others?" and tests)

These exist so the gates are **visible and testable**. They are `enabled: true` for the gate check but are only shown in the "Why not others?" list if the content owner approves (see [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q7).

| `code` | Idea | Gate that removes it | Legal base (to confirm) |
|---|---|---|---|
| `lease_land_commercial` | Lease or sell your land to an outside party for income | `LAND_SALE_OR_LEASE` | FRA Sec 4(4) |
| `timber_sale` | Cut and sell timber from nearby forest | `TIMBER_OR_HARM` | Sec 5 |
| `wildlife_trapping` | Hunt or trap animals | `HUNTING_OR_TRAPPING` | Sec 3(1)(l) |

`wildlife_trapping` is **never shown as a suggestion**; it exists for the Phase 4 question box ("Can I trap …?" → red policy message) and for tests. Default: **not displayed** in the user-facing "Why not others?" list.

---

## 4. Review process before launch (PDF §12, §17 Phase 5)

1. **Forest-law expert:** gates, legal bases, Gram Sabha-only ideas.
2. **Agriculture expert:** `min_land_ha`, `cost_level`, season, tags.
3. **Animal-welfare NGO:** wildlife risk labels; ideas that bring people into the forest (collection, tourism, fire-line work) get stricter treatment.
4. **Forest Department officer:** near-protected-area rules; later, advice by division.
5. **Native speakers:** Marathi and Hindi names and wording.
6. **Written sign-off** recorded in the repo (`docs/REVIEW_LOG.md`) before `status` changes from `draft` to `reviewed`.

Until step 6, every idea card in the app should be treated as **prototype content**; the report footer ("Suggestion only. Check on the ground. The Gram Sabha decides.") stays on.

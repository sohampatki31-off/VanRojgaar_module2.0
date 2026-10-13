# VanMitra Module 4 — Integration Notes (merge notes)

> The Module 4 PDF (§3) promises a `docs/MERGE_NOTES.md` listing every connection point the host app must supply. This is that file, written against the **actual host code** in `C:\Soham\college work\vanMitraAI` (read on 2026-10-14). Re-check each item when you start; the host moves fast.

**Principle:** all new code lives in two isolated folders. The host changes are a handful of **one-line registrations**.

| Side | New code | Host registration points |
|---|---|---|
| Flutter | `vanmitra_tem/lib/features/livelihood/` | `app_router.dart`, `app.dart`, dashboard card, `api_endpoints.dart` |
| Backend | `vanmitra_backend/app/livelihood/` + 2 scripts + tests | `api/v1/__init__.py`, `app/mongo.py` (`INDEXES`), optionally `app/config.py` |

---

## 1. What the host gives us (verified)

| Need | Host provides | Where |
|---|---|---|
| Current user, role, village | `/me` returns roles with `village_id` and names; app maps `gram_sabha`→`UserRole.frc`; village id = `User.backendVillageId` | `app/api/v1/auth.py`, `frontend_backend.md` §A2 |
| Auth | JWT (phone + 6-digit PIN), `CurrentUser`, `CurrentPrincipal`, `require_village_role` | `app/auth/deps.py`, `principal.py` |
| Roles | `Role.VILLAGER`, `Role.GRAM_SABHA`, `SDO`, … (only village-level roles matter here) | `app/models/enums.py` |
| Database | `Store` unit of work over **MongoDB**: `db.get/find/find_one/add/count/aggregate/collection(model)`, `db.commit()`; `2dsphere` indexes already used for `cfr_boundary.geom` | `app/mongo.py` |
| Models | Pydantic `Doc` / `TimestampedDoc`, UUIDv7 ids, `APPEND_ONLY` flag | `app/models/base.py` |
| Errors | `ApiError`, `RuleViolation`; body `{error, message_key, rule?, details}` | `app/errors.py` |
| Geo libs | `shapely>=2.0`, `pyproj>=3.6` already in `requirements-core.txt` | `vanmitra_backend/requirements-core.txt` |
| HTTP client (app) | `ApiClient` (JWT header, UTF-8 JSON, `ApiException`), base URL via `--dart-define=VANMITRA_API_BASE_URL` | `lib/core/api/api_client.dart`, `api_endpoints.dart` |
| Theme | `AppColors`, `context.colors` (light/dark), `AppTypography`, `AppSpacing`, `AppRadius` | `lib/core/theme/*` |
| Strings | `AppLocalizations` map + `context.tr('key')`; default locale **Marathi**; supported `en`, `hi`, `mr`, `kn` | `lib/services/localization_service.dart`, `providers/locale_provider.dart` |
| Offline store | Hive (`hive`, `hive_flutter`), `data/local/hive_database.dart` | `lib/data/local/` |
| Packages | `geolocator`, `flutter_map`, `latlong2`, `fl_chart`, `url_launcher`, `shimmer`, `connectivity_plus`, `flutter_secure_storage` | `pubspec.yaml` |
| Navigation | **Named routes** (`AppRouter` constants + `MaterialApp.routes`/`onGenerateRoute`); **no `go_router`** | `lib/core/routes/app_router.dart`, `lib/app.dart` |

### What the host does **not** give us (gaps we must fill)

| Gap | Evidence | Our answer |
|---|---|---|
| **No village coordinates in the backend** | `Village` model has name, GP, taluka, district only | `lv_village_geo` collection (centroid, optional boundary) |
| **No plot geometry or survey number on a claim** | Only `survey_compartment_numbers: list[str]` free text on Form C; Form A has extents in ha, no geometry | User drops a **GPS pin** in the Add-details form (M0). Later: prefill from a saved claim |
| **No resource data** (water, forest, wildlife layers) | No such collection or files | `lv_resource` + loader; data source is [OPEN_QUESTIONS](OPEN_QUESTIONS.md) Q1 |
| **No CFR status per village** | Module 2 (Atlas) not provided | Skip in M0; header `cfr_status: null` |
| **PostGIS** | The PDF and `previous/BACKEND_PLAN.md` say PostgreSQL + PostGIS; the real backend is MongoDB (`previous/BACKEND.md`, `app/mongo.py`) | Use **MongoDB `2dsphere`** + Shapely |

---

## 2. Folder skeletons to create

```
vanmitra_tem/lib/features/livelihood/            (see FRONTEND_PLAN §1)
vanmitra_tem/assets/livelihood/                  sample_report.json, ideas.json   (declare in pubspec.yaml assets)
vanmitra_backend/app/livelihood/                 (see BACKEND_PLAN §1)
vanmitra_backend/app/livelihood/seed/            ideas.json, sample_resources.geojson, config.json
vanmitra_backend/scripts/seed_livelihood.py
vanmitra_backend/scripts/load_livelihood_resources.py
vanmitra_backend/tests/livelihood/
```

---

## 3. Exact host edits (keep each tiny)

### Backend

1. **`app/api/v1/__init__.py`**: import and include the router:
   ```python
   from ...livelihood.router import router as livelihood_router
   router.include_router(livelihood_router)      # mounted under the existing /api/v1 prefix
   ```
   (the livelihood router declares `prefix="/livelihood"`).
2. **`app/mongo.py` → `INDEXES`**: merge the `lv_*` entries from [BACKEND_PLAN](BACKEND_PLAN.md) §2.2. Then **a person** runs `python -m scripts.setup_mongo`.
3. **`app/models/__init__.py`**: **do not** re-export `lv_*` models; import them from `app.livelihood.models` (avoids touching the host's model index and keeps the merge a copy).
4. **`app/config.py`** *(optional)*: `livelihood_default_radius_m = 5000`, `livelihood_max_radius_m = 10000`, `livelihood_demo_endpoints = False` (the slice-1 demo routes must be off in production). Env prefix `VANMITRA_` as elsewhere. Defaults in code are fine for M0.
5. Nothing else. No change to auth, roles, claims, cases, or boundary code. **The module is read-only on legal records (L9).**

### Flutter

1. **`lib/core/routes/app_router.dart`**: add constants:
   `livelihoodHome = '/livelihood'`, `livelihoodDetails = '/livelihood/details'`, `livelihoodLocation = '/livelihood/location'`, `livelihoodReport = '/livelihood/report'`, `livelihoodResources = '/livelihood/resources'`, `livelihoodIdea = '/livelihood/idea'`, `livelihoodPolicy = '/livelihood/policy'`.
2. **`lib/app.dart`**: add the screens to `routes:`; the idea detail (takes an idea code) goes into `onGenerateRoute` like `cfrClaimDetail`.
3. **Dashboard entry**: add one `ActionListItem` / `ClaimActionCard` in `screens/home/villager_home_screen.dart` (for villagers, and for the `gram_sabha` user if Q17 = yes), icon `Icons.agriculture_rounded` or similar, title `context.tr('lv_card_title')`-style via the feature's string helper, `onTap: () => Navigator.pushNamed(context, AppRouter.livelihoodHome)`. **Do not add a bottom-nav tab** (style guide: keep the compact 5-item bar).
4. **`lib/core/api/api_endpoints.dart`**: add a `livelihood…` group (`/livelihood/profile`, `/livelihood/report`, `/livelihood/report/latest`, `/livelihood/resources/nearby`, `/livelihood/ideas/{code}`, `/livelihood/meta`).
5. **`pubspec.yaml`**: declare the `assets/livelihood/` folder. **No new dependencies** for M0.
6. **Strings**: stay in `livelihood_strings.dart`. Only merge into `localization_service.dart` later, if the team wants one file.

---

## 4. Running the host (from its docs)

```bash
# backend (port 8010; 8000 is used by another project on this PC)
cd vanmitra_backend
./venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
# fast start without the ML models: set VANMITRA_ENABLE_LEGACY_API=false in .env

# phone over USB
adb reverse tcp:8000 tcp:8010
flutter build apk --debug --dart-define=VANMITRA_API_BASE_URL=http://127.0.0.1:8000
```

Health check: `http://localhost:8010/api/v1/health` should say `"database":"ok"`. Interactive docs: `/docs`.
Host checks: `ruff check app tests scripts` · `ruff format --check …` · `mypy app scripts` · `pytest -q`; Flutter: `flutter analyze` · `flutter test`.

> The host `.env` holds the MongoDB connection (`VANMITRA_MONGODB_URI`). **Never commit it.** DB tests use a **throwaway** database via `VANMITRA_TEST_MONGODB_URI`; do not point them at the real one (they empty it before every run).

---

## 5. Differences between this module's PDF and the host (decisions already made)

| PDF says | Host reality | Decision |
|---|---|---|
| PostgreSQL + PostGIS | MongoDB Atlas | **MongoDB** `2dsphere` |
| `go_router`, ARB files, Mukta font | Named routes, `AppLocalizations` map, Noto Sans Devanagari | **Follow the host** (Noto Sans Devanagari is bundled) |
| Standalone repo `vanmitra-rozgar`, then copy `lib/features/livelihood/` | Host code is available locally | Build **inside a host feature branch** with isolated folders (Q3, default) |
| Five-tab bar: Dashboard, Resources, Schemes, Report, Profile | Five tabs: Dashboard, Claims, Profile, Gram Sabha, Atlas Map | **Dashboard card**, no new tab |
| 3 km "near" distance | n/a | **5 km** (requested), configurable; Q4 |
| Colours `#1A4331` / `#FF8D20` (style guide doc) | `AppColors.forestCanopy #1B4332`, `saffron #FF7A00` | **Use the code tokens** |
| "Claude Code in the Antigravity editor" | n/a | Irrelevant to the code |

---

## 6. Merge checklist

- [ ] Branch from the latest host `main`; confirm the host still builds before adding anything
- [ ] New folders created; **no edits** to unrelated host files
- [ ] The five Flutter and two backend registrations in §3 done
- [ ] `flutter analyze` and `ruff`/`mypy`/`pytest` pass with the module added
- [ ] Indexes created by a person; seed run by a person; `/api/v1/health` ok
- [ ] Walk the [MVP_SPRINT](MVP_SPRINT.md) §5 acceptance list on the **merged** app
- [ ] Light **and** dark themes checked; Marathi not clipped on the smallest viewport
- [ ] No `.env`, `google-services.json`, keys or personal data committed
- [ ] Update the host docs: add a Module 4 section to `docs/BACKEND.md` and `frontend_backend.md`; fix the stale PostGIS statements in `previous/BACKEND_PLAN.md`

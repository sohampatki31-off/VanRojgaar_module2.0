# host/: the parts that exist only inside the host app

Everything else in `backend/app/livelihood/` and `frontend/lib/features/livelihood/` is copied into
`vanMitraAI` unchanged. This folder holds the pieces that **differ** from the standalone repo, so
the integration can be repeated or reviewed:

| File | Goes to (in `vanMitraAI`) | What |
|---|---|---|
| `backend/app/livelihood/deps.py` | `vanmitra_backend/app/livelihood/deps.py` | the user from the host login and `user_role` grants; the store over the host's `get_database()`. Replaces the standalone `deps.py` (do not copy `auth.py`) |
| `backend/scripts/seed_livelihood.py` | `vanmitra_backend/scripts/seed_livelihood.py` | looks up Ozhar's real id (read-only) then upserts ideas and the village location. Dry run by default |
| `backend/tests/livelihood/test_host_wiring.py` | `vanmitra_backend/tests/livelihood/` | role mapping against the host's real `Principal`/`RoleGrant`, and the routes behind the host login |
| `host-edits.patch` | applied to the host | the 34 changed lines in 7 existing host files (router list, settings, indexes, requirements, routes, dashboard card, asset) |

Also **not copied** to the host: `backend/app/livelihood/auth.py` (the standalone JWT and dev users),
`frontend/lib/core/`, `frontend/lib/shell/`, `frontend/lib/main.dart`, `frontend/test/api_client_test.dart`
and `frontend/test/live_contract_test.dart` (they test the standalone client).

The host side lives on the local branch `feature/module4-livelihood` of `vanMitraAI` (commit `69b85ea`),
**not pushed**: that repository belongs to the team.

## Added later: the host look and the online demo

| Folder / file | Goes to (in `vanMitraAI`) | What |
|---|---|---|
| `frontend/lib/widgets/livelihood_host_frame.dart` | `vanmitra_tem/lib/widgets/` | the two hooks: host frame and hero for Module 4 |
| `frontend/lib/core/api/server_address.dart`, `api_endpoints.dart` | `vanmitra_tem/lib/core/api/` | the server address kept on the phone (a demo APK needs no rebuild when the server moves); `api_endpoints.dart` replaces the host's (adds `serverOverride`, `isConfigured`, `serverRoot`) |
| `frontend/lib/widgets/server_address_dialog.dart` | `vanmitra_tem/lib/widgets/` | "Server address": type, **Test**, save, use default |
| `frontend/test/server_address_test.dart` | `vanmitra_tem/test/` | their tests |
| `backend/scripts/setup_module4_demo.py` | `vanmitra_backend/scripts/` | `[USER RUNS]` `--check` (read only), dry run, `--apply`: indexes, ideas, schemes, village, sample resources |
| `backend/scripts/check_deploy.py` | same | `[USER RUNS]` read-only check of a deployed server, step by step |
| `backend/scripts/smoke_mongo.py` | same | `[USER RUNS]` the whole of Module 4 over the real Mongo code in a `*_test` database |
| `backend/scripts/seed_livelihood.py` | same | also seeds the Sample schemes |
| `backend/tests/livelihood/test_*.py` | `vanmitra_backend/tests/livelihood/` | tests for all of the above |
| `deploy/Dockerfile.api`, `deploy/railway.api.toml` | `vanmitra_backend/Dockerfile.api`, repo root | the lean server image (no PyTorch) for Railway |
| `host-ui-edits.patch` | applied to the host | edits to 7 existing host files (nav bar, home, main, manifest, config) |
| `host-demo-edits.patch` | applied to the host | the two further edits: sign-in screen (Server line) and `main.dart` (loads the address) |

Step-by-step for putting the server online: `docs/DEPLOY_DEMO.md` (also in the host repo).

## The universal offline demo APK (`docs/DEMO_APKS.md`)

One APK, no server: `ApiClient` hands every call to `DemoBackend` (`lib/demo/`), a Dart port of the
real backend (accounts and roles, the claim path, Forms A, B, C, evidence, the Gram Sabha, the FRC,
boundary mapping, ...) over an in-memory database kept on the phone, plus the Module 4 answers made
by the real Module 4 rules.

| File | Goes to (in `vanMitraAI/vanmitra_tem`) | What |
|---|---|---|
| `frontend/lib/demo/**` | `lib/demo/` | the demo server: `core/` (router, database, accounts, cases and the claim path), `forms/`, `evidence/`, `gramsabha/`, `procedure/`, `boundary/`, `demo_livelihood.dart`, `demo_seed_claims.dart`, `demo_backend.dart` |
| `frontend/assets/demo/livelihood_demo.json` | `assets/demo/` | Module 4 mock data, made by `backend/scripts/export_demo_fixtures.py` in this repo |
| `frontend/test/demo/**` | `test/demo/` | about 300 tests, ported from the backend's own unit tests plus route-level and end-to-end tests |
| edits to `core/api/api_client.dart`, `screens/onboarding/registration_screen.dart`, `widgets/livelihood_host_frame.dart`, `main.dart`, `pubspec.yaml` | same | the demo hooks (see the host branch history) |

Build: `flutter build apk --release --dart-define=VANMITRA_DEMO=all`.

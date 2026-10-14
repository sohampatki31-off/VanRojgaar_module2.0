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


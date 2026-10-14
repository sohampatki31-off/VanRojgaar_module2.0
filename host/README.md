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

# VanMitra Module 4: Flutter app (standalone shell)

The feature lives in `lib/features/livelihood/` and is copied into the host app at merge
(`../docs/INTEGRATION.md`). Everything else under `lib/` is either a copy of the host's own
code (`core/theme/*`, `core/api/api_client.dart`) or a **throwaway shell** (`lib/shell/`) that only
exists so the feature runs on its own.

## Run it

```bash
flutter pub get
flutter analyze
flutter test            # 74 tests; 3 live-contract tests are skipped unless a server is given
```

**Demo (no server):** `flutter run`. Shows the bundled SAMPLE report; your details stay in memory.

**Live (against the backend):**

```bash
# backend (see ../backend/README.md): dev users on, memory store
python scripts/dev_token.py                 # prints a login token
flutter run \
  --dart-define=VANMITRA_API_BASE_URL=http://10.0.2.2:8010 \
  --dart-define=VANMITRA_DEV_TOKEN=<token>
```

`10.0.2.2` is the Android emulator's address for the PC. On a phone over USB use
`adb reverse tcp:8010 tcp:8010` and `http://127.0.0.1:8010`. In live mode his details and last
report are kept on the phone in an **encrypted** box (key in the Android Keystore), and a change
made offline is sent when the phone is online again.

**Live contract test** (the real client against a running backend):

```bash
set VANMITRA_LIVE_API=http://127.0.0.1:8011
set VANMITRA_LIVE_TOKEN=<token>
flutter test test/live_contract_test.dart
```

## What is where

| Path | What |
|---|---|
| `lib/features/livelihood/models/` | `Report` (the backend contract, no numeric scores) and `LivelihoodProfile` |
| `lib/features/livelihood/data/` | repositories (sample, remote, offline-first profile), the cache, location, error mapping |
| `lib/features/livelihood/providers/` | Riverpod state: profile, the 5-step intake, report |
| `lib/features/livelihood/screens/` | home, add details, report, resources, wildlife policy |
| `lib/features/livelihood/livelihood_strings.dart` | English and Marathi text. **The Marathi is a machine draft: a native speaker must review it** |
| `lib/core/` | host copies: theme tokens, `ApiClient` |
| `lib/shell/` | throwaway: theme, language switch, repository wiring |

Plan and rules: `../docs/FRONTEND_PLAN.md`, `../CLAUDE.md`.

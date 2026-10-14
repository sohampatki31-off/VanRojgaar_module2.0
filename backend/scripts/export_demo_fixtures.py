"""
Write the Module 4 mock data for the OFFLINE DEMO APKs (SAMPLE data only; no database, no network).

The app bundles the result and answers its own Module 4 calls from it, so a phone with the demo
APK needs no server. Everything in it is real output of the real rules for one sample farmer, so
it is contract-accurate: the same code that serves the live app produced it.

    python scripts/export_demo_fixtures.py ../frontend/assets/demo/livelihood_demo.json
    (host:  .../vanmitra_tem/assets/demo/livelihood_demo.json)

What is in it: the sample farmer's saved details, her report, the full detail of every idea, the
schemes register, and the answers to the suggested questions (plus one refused and one grey
answer for typed questions the demo cannot place).
"""

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.livelihood.auth import get_current_user  # noqa: E402
from app.livelihood.deps import get_store  # noqa: E402
from app.livelihood.identity import UserInfo  # noqa: E402
from app.livelihood.store import InMemoryStore  # noqa: E402
from app.main import create_app  # noqa: E402

URL = "/api/v1/livelihood"

# The sample farmer: the walkthrough profile of docs/MVP_SPRINT.md §4, at the default coordinates.
DEMO_PROFILE = {
    "land": {
        "area_value": 3,
        "area_unit": "acre",
        "land_type": "irrigated",
        "water_on_land": "open_well",
    },
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "manual"},
    "livestock": {"cow": 2, "goat_sheep": 5, "poultry": 10},
    "assets": ["well", "pump", "shed"],
    "past_work": ["millets", "dairy"],
    "family_workers": 3,
    "money_level": "medium",
}

TYPED_REFUSED = "how to poison a leopard"
TYPED_GREY = "what is the capital of france"


def scenario(c: TestClient) -> dict[str, Any]:
    """Everything the app asks for once a report exists, for whoever [c] is signed in as."""

    def ok(r: Any) -> Any:
        assert r.status_code == 200, (r.status_code, r.text)
        return r.json()

    report = ok(c.post(f"{URL}/report", json={}))
    codes = [i["code"] for i in report["ideas"]] + [r["code"] for r in report["removed"]]
    ideas = {code: ok(c.get(f"{URL}/ideas/{code}")) for code in codes}
    schemes = ok(c.get(f"{URL}/schemes"))

    first = ok(c.post(f"{URL}/ask", json={"chip": "heading", "lang": "en"}))
    chips = first["chips"]
    chip_answers = {
        chip["id"]: ok(c.post(f"{URL}/ask", json={"chip": chip["id"], "lang": "en"}))["turn"]
        for chip in chips
    }
    refused = ok(c.post(f"{URL}/ask", json={"question": TYPED_REFUSED, "lang": "en"}))["turn"]
    grey = ok(c.post(f"{URL}/ask", json={"question": TYPED_GREY, "lang": "en"}))["turn"]
    assert refused["answer"]["kind"] == "REFUSED_HARMFUL", refused["answer"]["kind"]
    assert grey["answer"]["kind"] == "OFF_TOPIC", grey["answer"]["kind"]
    return {
        "report": report,
        "ideas": ideas,
        "schemes": schemes,
        "ask": {
            "chips": chips,
            "chip_answers": chip_answers,
            "refused": refused,
            "off_topic": grey,
        },
    }


def client_for(name: str) -> TestClient:
    store = InMemoryStore()
    user = UserInfo(uuid.uuid4(), name, "sample_ozhar", frozenset({"villager"}))
    app = create_app()
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_current_user] = lambda: user  # whoever calls is [name]
    return TestClient(app)


def build(name: str) -> dict[str, Any]:
    # 1. the sample farmer: her details are saved, and her report is built from them
    farmer = client_for(name)
    saved = farmer.put(f"{URL}/profile", json=DEMO_PROFILE)
    assert saved.status_code == 200, saved.text
    # 2. nobody's details (after "Delete my answers"): the village-level report
    nobody = client_for(name)
    return {
        "note": "SAMPLE data for the offline demo APK (scripts/export_demo_fixtures.py).",
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": saved.json(),
        "scenarios": {"farmer": scenario(farmer), "general": scenario(nobody)},
    }


def main(out: Path, name: str) -> None:
    data = build(name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    for key, sc in data["scenarios"].items():
        print(
            f"  {key}: level {sc['report']['header']['report_level']}, {len(sc['ideas'])} ideas, "
            f"{len(sc['ask']['chip_answers'])} answers"
        )
    print(f"wrote {out}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit("usage: python scripts/export_demo_fixtures.py <out.json> [name]")
    main(Path(args[0]), args[1] if len(args) > 1 else "Samrudhi")

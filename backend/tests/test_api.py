import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS", "true")
    get_settings.cache_clear()
    yield TestClient(create_app())  # type: ignore[misc]
    get_settings.cache_clear()


def test_demo_endpoints_are_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # the TRUE default, ignoring any local .env (which a developer turns on for the phone demo)
    monkeypatch.delenv("VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS", raising=False)
    assert Settings(_env_file=None).livelihood_demo_endpoints is False


def test_health(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_meta_lists_vocabularies_and_flags_sample_data(client: TestClient) -> None:
    body = client.get("/api/v1/livelihood/meta").json()
    assert body["default_radius_m"] == 5000 and body["max_radius_m"] == 10000
    assert body["dataset"]["is_sample"] is True
    assert "cow" in body["animal_codes"] and "pump" in body["asset_codes"]
    assert set(body["area_units"]) == {"hectare", "acre", "guntha"}


def test_demo_report_round_trip(client: TestClient) -> None:
    payload = {
        "name": "Demo",
        "profile": {
            "land": {"area_value": 3, "area_unit": "acre"},
            "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
            "livestock": {"cow": 2},
            "assets": ["well"],
        },
    }
    r = client.post("/api/v1/livelihood/demo/report", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["is_sample_data"] is True
    assert body["footer_key"] == "footer.suggestion_only"
    assert 0 < len(body["ideas"]) <= 5
    assert all(res["distance_m"] <= 5000 for res in body["resources"])


def test_demo_report_with_no_body_details_is_a_village_report(client: TestClient) -> None:
    r = client.post("/api/v1/livelihood/demo/report", json={})
    assert r.status_code == 200 and r.json()["header"]["report_level"] == "village"


def test_errors_use_the_host_error_shape(client: TestClient) -> None:
    r = client.post("/api/v1/livelihood/demo/report", json={"radius_m": 999999})
    assert r.status_code == 422
    assert r.json() == {
        "error": "RADIUS_TOO_LARGE",
        "message_key": "livelihood.radius_too_large",
        "details": {"max_m": 10000},
    }
    bad = client.post("/api/v1/livelihood/demo/report", json={"profile": {"caste": "x"}})
    assert bad.status_code == 422 and bad.json()["error"] == "VALIDATION_ERROR"


def test_demo_endpoints_can_be_switched_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEMO_ENDPOINTS", "false")
    get_settings.cache_clear()
    try:
        r = TestClient(create_app()).post("/api/v1/livelihood/demo/report", json={})
        assert r.status_code == 404
    finally:
        get_settings.cache_clear()

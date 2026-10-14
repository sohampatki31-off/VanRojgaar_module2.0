import json
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.livelihood.auth import (
    DEV_VILLAGER,
    DEV_VILLAGER_2,
    StaticDirectory,
    UserInfo,
    create_access_token,
    get_directory,
)
from app.livelihood.schemas import ReportOut
from app.livelihood.service import DatasetMeta
from app.livelihood.store import KEEP_REPORTS, InMemoryStore, get_store
from app.main import create_app

PROFILE = {
    "land": {"area_value": 3, "area_unit": "acre", "water_on_land": "open_well"},
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2, "goat_sheep": 5},
    "assets": ["well", "pump", "shed"],
    "past_work": ["dairy", "millets"],
    "money_level": "medium",
    "family_workers": 3,
}
URL = "/api/v1/livelihood"


class _NoDataStore(InMemoryStore):
    def dataset_meta(self) -> DatasetMeta | None:
        return None


class _NewerDataStore(InMemoryStore):
    """Pretends a newer dataset version has been loaded since the report was made."""

    def dataset_meta(self) -> DatasetMeta | None:
        base = super().dataset_meta()
        assert base is not None
        return DatasetMeta(base.name, "v2", base.is_sample, base.source, base.source_date)


def _client(monkeypatch: pytest.MonkeyPatch, store: InMemoryStore) -> TestClient:
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEV_USERS", "true")
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    yield _client(monkeypatch, InMemoryStore())
    get_settings.cache_clear()


def auth(user_id: uuid.UUID = DEV_VILLAGER.id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def keys(node: Any) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in keys(v)}
    if isinstance(node, list):
        return {k for v in node for k in keys(v)}
    return set()


def test_the_new_routes_need_a_login(client: TestClient) -> None:
    assert client.post(f"{URL}/report", json={}).status_code == 401
    assert client.get(f"{URL}/report/latest").status_code == 401
    nearby = client.post(f"{URL}/resources/nearby", json={"lat": 19.78, "lng": 73.22})
    assert nearby.status_code == 401


def test_report_without_saved_details_is_a_general_village_report(client: TestClient) -> None:
    r = client.post(f"{URL}/report", json={}, headers=auth())
    assert r.status_code == 200
    body = r.json()
    assert body["header"]["report_level"] == "village"
    assert body["header"]["name"] == "Demo villager"  # from his login, not the request
    assert body["is_sample_data"] is True
    assert "profile_incomplete" in body["analysis"]["notes"]
    assert {i["group"] for i in body["ideas"]} == {"ranked"}


def test_report_uses_his_saved_details(client: TestClient) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    body = client.post(f"{URL}/report", json={}, headers=auth()).json()
    assert body["header"]["report_level"] == "plot"
    assert body["header"]["radius_m"] == 5000
    assert body["counts"]["total"] == len(body["resources"]) == 10
    top3 = [i["code"] for i in body["ideas"][:3]]
    assert "dairy_small" in top3 and "goat_rearing" in top3
    assert {t["code"] for t in body["told_by_you"]} >= {"cow", "pump", "shed"}
    distances = [x["distance_m"] for x in body["resources"]]
    assert distances == sorted(distances) and max(distances) <= 5000


def test_the_report_is_labels_only_with_no_scores(client: TestClient) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    body = client.post(f"{URL}/report", json={}, headers=auth()).json()
    assert not keys(body) & {"u", "f", "score", "fit_score", "_u", "percent", "rating"}


def test_the_latest_report_is_kept_and_returned_as_made(client: TestClient) -> None:
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 404
    made = client.post(f"{URL}/report", json={}, headers=auth()).json()
    latest = client.get(f"{URL}/report/latest", headers=auth()).json()
    assert latest["id"] == made["id"] and latest["generated_at"] == made["generated_at"]
    assert latest["newer_version_available"] is False
    newer = client.post(f"{URL}/report", json={"radius_m": 3000}, headers=auth()).json()
    assert client.get(f"{URL}/report/latest", headers=auth()).json()["id"] == newer["id"]


def test_latest_says_when_newer_data_has_been_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    # make a report against the "v1" data ...
    report = _client(monkeypatch, InMemoryStore()).post(f"{URL}/report", json={}, headers=auth())
    report = report.json()
    assert report["data_version"] == "v1"
    # ... then look at it while "v2" is the current data
    newer = _NewerDataStore()
    newer.save_report(str(DEV_VILLAGER.id), ReportOut.model_validate(report))
    latest = _client(monkeypatch, newer).get(f"{URL}/report/latest", headers=auth()).json()
    assert latest["newer_version_available"] is True
    assert latest["id"] == report["id"]  # the old report is shown unchanged, only flagged


def test_reports_are_private_to_their_owner(client: TestClient) -> None:
    mine = client.post(f"{URL}/report", json={}, headers=auth(DEV_VILLAGER.id)).json()
    assert client.get(f"{URL}/report/latest", headers=auth(DEV_VILLAGER_2.id)).status_code == 404
    theirs = client.post(f"{URL}/report", json={}, headers=auth(DEV_VILLAGER_2.id)).json()
    assert theirs["id"] != mine["id"] and theirs["header"]["name"] == "Second villager"
    assert (
        client.get(f"{URL}/report/latest", headers=auth(DEV_VILLAGER.id)).json()["id"] == mine["id"]
    )


def test_deleting_answers_deletes_the_reports_made_from_them(client: TestClient) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    client.post(f"{URL}/report", json={}, headers=auth())
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 200
    assert client.delete(f"{URL}/profile", headers=auth()).status_code == 204
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 404
    assert client.get(f"{URL}/profile", headers=auth()).status_code == 404


def test_only_the_latest_few_reports_are_kept() -> None:
    store = InMemoryStore()
    base = ReportOut.model_validate(_any_report(store))
    for n in range(KEEP_REPORTS + 3):
        store.save_report("u", base.model_copy(update={"id": f"r{n}"}))
    assert store.latest_report("u").id == f"r{KEEP_REPORTS + 2}"  # type: ignore[union-attr]
    assert len(store._reports["u"]) == KEEP_REPORTS


def _any_report(store: InMemoryStore) -> dict[str, Any]:
    from app.livelihood.schemas import ProfileIn
    from app.livelihood.seed import load_demo_village, load_ideas, load_sample_weather
    from app.livelihood.service import build_report

    meta = store.dataset_meta()
    assert meta is not None
    report = build_report(
        profile=ProfileIn(),
        user_name="x",
        village=load_demo_village(),
        resources=list(store._resources),
        ideas=load_ideas(),
        dataset=meta,
        weather=load_sample_weather(),
    )
    return json.loads(report.model_dump_json())


def test_radius_is_validated_and_capped(client: TestClient) -> None:
    too_big = client.post(f"{URL}/report", json={"radius_m": 10_001}, headers=auth())
    assert too_big.status_code == 422
    assert too_big.json() == {
        "error": "RADIUS_TOO_LARGE",
        "message_key": "livelihood.radius_too_large",
        "details": {"max_m": 10000},
    }
    assert client.post(f"{URL}/report", json={"radius_m": 0}, headers=auth()).status_code == 422
    assert client.post(f"{URL}/report", json={"radius": 5}, headers=auth()).status_code == 422
    small = client.post(f"{URL}/report", json={"radius_m": 1000}, headers=auth()).json()
    assert small["header"]["radius_m"] == 1000
    assert all(x["distance_m"] <= 1000 for x in small["resources"])


def test_a_small_radius_still_warns_about_a_protected_area_just_outside_it(
    client: TestClient,
) -> None:
    """The listed radius is 1 km, but a protected area 1.3 km away must still raise the flag."""
    near_protected = {
        **PROFILE,
        "location": {"lat": 19.7805 + 0.0090, "lng": 73.2210 + 0.0016, "source": "gps"},
    }
    client.put(f"{URL}/profile", json=near_protected, headers=auth())
    body = client.post(f"{URL}/report", json={"radius_m": 1000}, headers=auth()).json()
    assert body["header"]["radius_m"] == 1000
    assert any(c["key"] == "analysis.near_protected_area" for c in body["analysis"]["constraints"])
    assert all(any(f["key"] == "flag.ask_forest_dept" for f in i["flags"]) for i in body["ideas"])
    # the protected layer itself is never listed as a resource
    assert "wildlife_compartment" not in {x["kind"] for x in body["resources"]}


def test_a_user_with_no_village_cannot_get_a_report(monkeypatch: pytest.MonkeyPatch) -> None:
    homeless = UserInfo(uuid.uuid4(), "No village", None, frozenset({"villager"}))
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEV_USERS", "true")
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_store] = lambda: InMemoryStore()
    app.dependency_overrides[get_directory] = lambda: StaticDirectory([homeless])
    r = TestClient(app).post(f"{URL}/report", json={}, headers=auth(homeless.id))
    assert r.status_code == 422 and r.json()["message_key"] == "livelihood.no_village"
    get_settings.cache_clear()


def test_an_empty_database_is_an_error_not_an_empty_report(monkeypatch: pytest.MonkeyPatch) -> None:
    """No data loaded must never read as 'nothing is near you' (rule L1)."""
    c = _client(monkeypatch, _NoDataStore())
    r = c.post(f"{URL}/report", json={}, headers=auth())
    assert r.status_code == 503 and r.json()["message_key"] == "livelihood.data_not_loaded"
    r2 = c.post(f"{URL}/resources/nearby", json={"lat": 19.78, "lng": 73.22}, headers=auth())
    assert r2.status_code == 503
    get_settings.cache_clear()


def test_nearby_lists_labelled_resources_nearest_first(client: TestClient) -> None:
    r = client.post(
        f"{URL}/resources/nearby", json={"lat": 19.7805, "lng": 73.2210}, headers=auth()
    )
    assert r.status_code == 200
    body = r.json()
    assert body["radius_m"] == 5000 and body["is_sample_data"] is True
    assert body["centre"]["source"] == "manual"
    assert body["counts"]["total"] == len(body["resources"]) == 10
    d = [x["distance_m"] for x in body["resources"]]
    assert d == sorted(d) and max(d) <= 5000
    assert "wildlife_compartment" not in {x["kind"] for x in body["resources"]}
    assert not keys(body) & {"u", "score", "_u"}
    assert all(x["trust"]["source"] for x in body["resources"])


def test_nearby_can_filter_by_kind_and_narrow_the_radius(client: TestClient) -> None:
    wells = client.post(
        f"{URL}/resources/nearby",
        json={"lat": 19.7805, "lng": 73.2210, "kinds": ["well"]},
        headers=auth(),
    ).json()
    assert {x["kind"] for x in wells["resources"]} == {"well"}
    narrow = client.post(
        f"{URL}/resources/nearby",
        json={"lat": 19.7805, "lng": 73.2210, "radius_m": 500},
        headers=auth(),
    ).json()
    assert [x["distance_m"] for x in narrow["resources"]] == [420]


def test_nearby_rejects_bad_requests(client: TestClient) -> None:
    bad = [
        {"lat": 28.6, "lng": 77.2},  # Delhi
        {"lat": 19.78, "lng": 73.22, "radius_m": 99999},
        {"lat": 19.78, "lng": 73.22, "kinds": ["spaceship"]},
        {"lat": 19.78, "lng": 73.22, "extra": 1},
        {"lat": 999, "lng": 73.22},
        {"lat": 19.78},
    ]
    for payload in bad:
        r = client.post(f"{URL}/resources/nearby", json=payload, headers=auth())
        assert r.status_code == 422, payload


def test_nearby_in_an_empty_area_is_an_honest_empty_list(client: TestClient) -> None:
    r = client.post(f"{URL}/resources/nearby", json={"lat": 21.0, "lng": 79.0}, headers=auth())
    assert r.status_code == 200
    assert r.json()["resources"] == [] and r.json()["counts"]["total"] == 0


def test_nearby_saves_nothing(client: TestClient) -> None:
    client.post(f"{URL}/resources/nearby", json={"lat": 19.78, "lng": 73.22}, headers=auth())
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 404

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.livelihood.auth import (
    DEV_OFFICER,
    DEV_VILLAGER,
    DEV_VILLAGER_2,
    create_access_token,
)
from app.livelihood.deps import get_store
from app.livelihood.store import InMemoryStore
from app.main import create_app

PROFILE = {
    "land": {"area_value": 3, "area_unit": "acre", "land_type": "irrigated"},
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2, "goat_sheep": 5},
    "assets": ["well", "pump"],
    "past_work": ["dairy"],
    "money_level": "medium",
}


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEV_USERS", "true")
    get_settings.cache_clear()
    app = create_app()
    store = InMemoryStore()  # a fresh, empty store for every test
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    get_settings.cache_clear()


def auth(user_id: uuid.UUID = DEV_VILLAGER.id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def test_profile_needs_a_login(client: TestClient) -> None:
    for call in (client.get, client.delete):
        r = call("/api/v1/livelihood/profile")
        assert r.status_code == 401
        assert r.json()["error"] == "NOT_AUTHENTICATED"
    assert client.put("/api/v1/livelihood/profile", json=PROFILE).status_code == 401


def test_bad_tokens_are_refused(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    url = "/api/v1/livelihood/profile"
    assert (
        client.get(url, headers={"Authorization": "Bearer nonsense"}).json()["error"]
        == "TOKEN_INVALID"
    )

    expired = create_access_token(DEV_VILLAGER.id, minutes=-5)
    assert (
        client.get(url, headers={"Authorization": f"Bearer {expired}"}).json()["error"]
        == "TOKEN_EXPIRED"
    )

    s = get_settings()
    refresh_kind = jwt.encode(
        {
            "sub": str(DEV_VILLAGER.id),
            "type": "refresh",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        s.jwt_secret,
        algorithm=s.jwt_algorithm,
    )
    assert (
        client.get(url, headers={"Authorization": f"Bearer {refresh_kind}"}).json()["error"]
        == "TOKEN_INVALID"
    )

    wrong_key = jwt.encode(
        {
            "sub": str(DEV_VILLAGER.id),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        "some-other-secret-key-of-enough-length-1234",
        algorithm="HS256",
    )
    assert client.get(url, headers={"Authorization": f"Bearer {wrong_key}"}).status_code == 401


def test_unknown_user_and_wrong_role(client: TestClient) -> None:
    url = "/api/v1/livelihood/profile"
    stranger = auth(uuid.uuid4())  # a valid token for someone the directory does not know
    assert client.get(url, headers=stranger).status_code == 401
    r = client.get(url, headers=auth(DEV_OFFICER.id))  # an SDO has no use for this module
    assert r.status_code == 403 and r.json()["message_key"] == "livelihood.role_not_allowed"


def test_dev_users_are_off_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # the TRUE default, ignoring any local .env (which a developer turns on for the phone demo)
    monkeypatch.delenv("VANMITRA_LIVELIHOOD_DEV_USERS", raising=False)
    assert Settings(_env_file=None).livelihood_dev_users is False
    # and with the switch off, a perfectly good token is still refused
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEV_USERS", "false")
    get_settings.cache_clear()
    try:
        app = create_app()
        app.dependency_overrides[get_store] = lambda: InMemoryStore()
        r = TestClient(app).get("/api/v1/livelihood/profile", headers=auth())
        assert r.status_code == 401  # a good token is still refused: nobody is known
    finally:
        get_settings.cache_clear()


def test_get_before_put_is_a_clear_404(client: TestClient) -> None:
    r = client.get("/api/v1/livelihood/profile", headers=auth())
    assert r.status_code == 404 and r.json()["message_key"] == "livelihood.no_profile"


def test_put_then_get_round_trip(client: TestClient) -> None:
    put = client.put("/api/v1/livelihood/profile", json=PROFILE, headers=auth())
    assert put.status_code == 200
    body = put.json()
    assert body["area_ha"] == pytest.approx(1.2141, abs=1e-3)  # 3 acres
    assert body["village"] == {"id": "sample_ozhar", "name_mr": "ओझर", "name_en": "Ozhar"}
    assert body["profile"]["livestock"]["cow"] == 2

    got = client.get("/api/v1/livelihood/profile", headers=auth()).json()
    assert got["profile"]["assets"] == ["pump", "well"]  # stored sorted and de-duplicated
    assert got["created_at"] == body["created_at"]


def test_put_replaces_and_never_merges(client: TestClient) -> None:
    url = "/api/v1/livelihood/profile"
    first = client.put(url, json=PROFILE, headers=auth()).json()
    second = client.put(url, json={"assets": ["shed"]}, headers=auth()).json()
    assert second["profile"]["assets"] == ["shed"]
    assert second["profile"]["livestock"] is None  # the old livestock is gone, not merged
    assert second["area_ha"] is None
    assert second["created_at"] == first["created_at"]
    assert second["updated_at"] >= first["updated_at"]


def test_people_never_see_each_others_answers(client: TestClient) -> None:
    url = "/api/v1/livelihood/profile"
    client.put(url, json=PROFILE, headers=auth(DEV_VILLAGER.id))
    assert client.get(url, headers=auth(DEV_VILLAGER_2.id)).status_code == 404
    client.put(url, json={"assets": ["shed"]}, headers=auth(DEV_VILLAGER_2.id))
    assert client.get(url, headers=auth(DEV_VILLAGER.id)).json()["profile"]["assets"] == [
        "pump",
        "well",
    ]
    # deleting one person's answers leaves the other's alone
    client.delete(url, headers=auth(DEV_VILLAGER_2.id))
    assert client.get(url, headers=auth(DEV_VILLAGER.id)).status_code == 200


def test_a_village_in_the_body_is_ignored(client: TestClient) -> None:
    """His village comes from his login: a body that tries to name one is refused outright."""
    r = client.put(
        "/api/v1/livelihood/profile",
        json={**PROFILE, "village_id": "someone-elses-village"},
        headers=auth(),
    )
    assert r.status_code == 422 and r.json()["error"] == "VALIDATION_ERROR"


def test_delete_clears_the_answers_and_is_repeatable(client: TestClient) -> None:
    url = "/api/v1/livelihood/profile"
    client.put(url, json=PROFILE, headers=auth())
    assert client.delete(url, headers=auth()).status_code == 204
    assert client.get(url, headers=auth()).status_code == 404
    assert client.delete(url, headers=auth()).status_code == 204  # nothing to delete: still fine


@pytest.mark.parametrize(
    "bad",
    [
        {"caste": "x"},
        {"income": 100000},
        {"land": {"area_value": -1}},
        {"land": {"area_value": 0}},
        {"land": {"income": 1}},
        {"livestock": {"cow": 1000}},
        {"livestock": {"cow": -1}},
        {"assets": ["spaceship"]},
        {"past_work": ["astronaut"]},
        {"family_workers": 99},
        {"money_level": "huge"},
    ],
)
def test_bad_details_are_refused_in_the_host_error_shape(
    client: TestClient, bad: dict[str, object]
) -> None:
    r = client.put("/api/v1/livelihood/profile", json=bad, headers=auth())
    assert r.status_code == 422
    assert r.json()["error"] == "VALIDATION_ERROR" and r.json()["message_key"] == "error.validation"


def test_location_outside_maharashtra_is_refused(client: TestClient) -> None:
    bad = {"location": {"lat": 28.6, "lng": 77.2, "source": "gps"}}
    r = client.put("/api/v1/livelihood/profile", json=bad, headers=auth())
    assert r.status_code == 422
    assert r.json()["message_key"] == "livelihood.location_outside_maharashtra"
    # the village-centre fallback carries no real coordinates to check
    ok = {"location": {"lat": 0, "lng": 0, "source": "village_centre"}}
    assert client.put("/api/v1/livelihood/profile", json=ok, headers=auth()).status_code == 200


def test_an_empty_profile_is_allowed(client: TestClient) -> None:
    """Every question is optional (PDF §10), so saving nothing is valid."""
    r = client.put("/api/v1/livelihood/profile", json={}, headers=auth())
    assert r.status_code == 200 and r.json()["area_ha"] is None

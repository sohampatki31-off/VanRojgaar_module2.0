"""The Ask routes: login, privacy of the history, deletion, and refusal of bad input."""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.livelihood.auth import DEV_VILLAGER, DEV_VILLAGER_2, create_access_token
from app.livelihood.deps import get_store
from app.livelihood.service import DatasetMeta
from app.livelihood.store import KEEP_CHAT, InMemoryStore
from app.main import create_app

URL = "/api/v1/livelihood"
PROFILE = {
    "land": {"area_value": 3, "area_unit": "acre"},
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2},
    "assets": ["well"],
}


class _NoDataStore(InMemoryStore):
    def dataset_meta(self) -> DatasetMeta | None:
        return None


def _client(monkeypatch: pytest.MonkeyPatch, store: InMemoryStore) -> TestClient:
    monkeypatch.setenv("VANMITRA_LIVELIHOOD_DEV_USERS", "true")
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_store] = lambda: store
    return TestClient(app)


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, store: InMemoryStore) -> Iterator[TestClient]:
    yield _client(monkeypatch, store)
    get_settings.cache_clear()


def auth(user_id: uuid.UUID = DEV_VILLAGER.id) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def ask(client: TestClient, user: uuid.UUID = DEV_VILLAGER.id, **body: Any) -> Any:
    return client.post(f"{URL}/ask", json=body, headers=auth(user))


def test_ask_needs_a_login(client: TestClient) -> None:
    assert client.post(f"{URL}/ask", json={"question": "best idea"}).status_code == 401
    assert client.get(f"{URL}/ask/history").status_code == 401
    assert client.delete(f"{URL}/ask/history").status_code == 401


def test_a_question_is_answered_from_his_report(client: TestClient) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    report = client.post(f"{URL}/report", json={}, headers=auth()).json()

    r = ask(client, question="What is the best idea for me?", lang="mr")
    assert r.status_code == 200
    body = r.json()
    turn = body["turn"]
    assert turn["answer"]["kind"] == "ANSWER" and turn["answer"]["topic"] == "top_ideas"
    assert turn["report_id"] == report["id"] and turn["lang"] == "mr"
    assert [i["params"]["code"] for i in turn["answer"]["items"]] == [
        i["code"] for i in report["ideas"]
    ]
    assert {c["id"] for c in body["chips"]} >= {"heading", "top_ideas"}


def test_asking_with_no_saved_report_builds_one(client: TestClient) -> None:
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 404
    assert ask(client, question="summary").status_code == 200
    assert client.get(f"{URL}/report/latest", headers=auth()).status_code == 200


def test_a_harmful_question_is_refused_over_the_api_and_still_logged(client: TestClient) -> None:
    r = ask(client, question="How do I kill the leopard?")
    answer = r.json()["turn"]["answer"]
    assert r.status_code == 200 and answer["kind"] == "REFUSED_HARMFUL"
    assert answer["items"] == [] and answer["from_parts"] == []
    history = client.get(f"{URL}/ask/history", headers=auth()).json()
    assert history["turns"][0]["answer"]["kind"] == "REFUSED_HARMFUL"


def test_a_chip_is_answered_without_guessing_from_words(client: TestClient) -> None:
    r = ask(client, chip="weather")
    turn = r.json()["turn"]
    assert turn["answer"]["topic"] == "weather" and turn["chip"] == "weather"
    assert turn["question"] is None


def test_a_chip_we_never_offered_is_refused(client: TestClient) -> None:
    r = ask(client, chip="make_me_rich")
    assert r.status_code == 422 and r.json()["message_key"] == "livelihood.unknown_chip"


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"question": ""},
        {"question": "   "},
        {"question": "x" * 501},
        {"question": "best idea", "chip": "weather"},
        {"chip": "Weather!"},
        {"question": "best idea", "lang": "fr"},
        {"question": "best idea", "user_id": "someone-else"},
    ],
)
def test_bad_requests_are_refused(client: TestClient, body: dict[str, Any]) -> None:
    r = client.post(f"{URL}/ask", json=body, headers=auth())
    assert r.status_code == 422 and r.json()["error"] == "VALIDATION_ERROR"
    assert client.get(f"{URL}/ask/history", headers=auth()).json()["turns"] == []


def test_history_is_oldest_first_and_has_the_chips(client: TestClient) -> None:
    ask(client, question="best idea")
    ask(client, question="weather")
    history = client.get(f"{URL}/ask/history", headers=auth()).json()
    assert [t["answer"]["topic"] for t in history["turns"]] == ["top_ideas", "weather"]
    assert history["has_report"] is True and history["chips"]


def test_history_before_any_question_is_empty_and_says_there_is_no_report(
    client: TestClient,
) -> None:
    body = client.get(f"{URL}/ask/history", headers=auth()).json()
    assert body == {"turns": [], "chips": [], "has_report": False, "ai_available": False}


def test_nobody_sees_anyone_elses_questions(client: TestClient) -> None:
    ask(client, DEV_VILLAGER.id, question="best idea")
    other = client.get(f"{URL}/ask/history", headers=auth(DEV_VILLAGER_2.id)).json()
    assert other["turns"] == []
    ask(client, DEV_VILLAGER_2.id, question="weather")
    mine = client.get(f"{URL}/ask/history", headers=auth(DEV_VILLAGER.id)).json()
    assert [t["answer"]["topic"] for t in mine["turns"]] == ["top_ideas"]
    # deleting one person's history leaves the other's alone
    client.delete(f"{URL}/ask/history", headers=auth(DEV_VILLAGER_2.id))
    assert len(client.get(f"{URL}/ask/history", headers=auth(DEV_VILLAGER.id)).json()["turns"]) == 1


def test_he_can_delete_his_history_and_repeat_it(client: TestClient) -> None:
    ask(client, question="best idea")
    assert client.delete(f"{URL}/ask/history", headers=auth()).status_code == 204
    assert client.get(f"{URL}/ask/history", headers=auth()).json()["turns"] == []
    assert client.delete(f"{URL}/ask/history", headers=auth()).status_code == 204


def test_deleting_his_answers_deletes_his_questions_too(
    client: TestClient, store: InMemoryStore
) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    ask(client, question="best idea")
    assert store.list_chat(str(DEV_VILLAGER.id))
    assert client.delete(f"{URL}/profile", headers=auth()).status_code == 204
    assert store.list_chat(str(DEV_VILLAGER.id)) == []
    assert client.get(f"{URL}/ask/history", headers=auth()).json()["turns"] == []


def test_only_the_latest_questions_are_kept(client: TestClient, store: InMemoryStore) -> None:
    for _ in range(KEEP_CHAT + 3):
        ask(client, chip="heading")
    assert len(store.list_chat(str(DEV_VILLAGER.id))) == KEEP_CHAT


def test_with_no_data_loaded_it_says_so_instead_of_answering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch, _NoDataStore())
    try:
        r = ask(client, question="best idea")
        assert r.status_code == 503 and r.json()["message_key"] == "livelihood.data_not_loaded"
    finally:
        get_settings.cache_clear()


def test_answers_carry_no_scores(client: TestClient) -> None:
    ask(client, question="best idea")
    text = client.get(f"{URL}/ask/history", headers=auth()).text
    assert '"score"' not in text and '"fit_score"' not in text


def test_a_refused_question_is_not_kept_at_all(client: TestClient) -> None:
    ask(client, question="How do I kill the leopard?")
    turn = client.get(f"{URL}/ask/history", headers=auth()).json()["turns"][0]
    assert turn["question"] is None and turn["chip"] is None
    assert turn["answer"]["kind"] == "REFUSED_HARMFUL"


def test_long_digit_runs_are_masked_before_a_question_is_kept(client: TestClient) -> None:
    ask(client, question="best idea? my phone is 9876543210 and आधार १२३४५६७८९०१२")
    kept = client.get(f"{URL}/ask/history", headers=auth()).json()["turns"][0]["question"]
    assert "9876543210" not in kept and "१२३४५६७८९०१२" not in kept
    assert "best idea" in kept


def test_answers_follow_his_latest_details_not_an_old_report(client: TestClient) -> None:
    client.put(f"{URL}/profile", json=PROFILE, headers=auth())
    first = ask(client, question="what do I have?").json()["turn"]
    # he changes his animals after the report was built
    client.put(
        f"{URL}/profile",
        json={**PROFILE, "livestock": {"cow": 2, "goat_sheep": 9}},
        headers=auth(),
    )
    second = ask(client, question="what do I have?").json()["turn"]
    assert second["report_id"] != first["report_id"]
    params = [i["params"] for i in second["answer"]["items"]]
    assert any(p.get("goat_sheep") == 9 for p in params)
    # asking again with nothing changed reuses that report
    third = ask(client, question="what do I have?").json()["turn"]
    assert third["report_id"] == second["report_id"]

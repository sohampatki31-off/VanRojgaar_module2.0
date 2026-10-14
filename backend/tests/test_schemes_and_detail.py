"""Stage 3: the scheme register (links only) and the idea detail built from his report."""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import get_settings
from app.livelihood.ask_schemas import AnswerKind
from app.livelihood.auth import DEV_VILLAGER, DEV_VILLAGER_2, create_access_token
from app.livelihood.deps import get_store
from app.livelihood.domain import ask_engine
from app.livelihood.domain.idea_detail import build_idea_detail, scheme_counts
from app.livelihood.schemas import Idea, ProfileIn
from app.livelihood.scheme_schemas import AUDIENCES, HELP_TYPES, SchemeRecord
from app.livelihood.seed import load_ideas, load_sample_weather, load_schemes
from app.livelihood.service import build_report
from app.livelihood.store import InMemoryStore
from app.main import create_app

URL = "/api/v1/livelihood"
PROFILE = {
    "land": {"area_value": 3, "area_unit": "acre"},
    "location": {"lat": 19.7805, "lng": 73.2210, "source": "gps"},
    "livestock": {"cow": 2, "goat_sheep": 5},
    "assets": ["well", "pump"],
    "past_work": ["dairy"],
}


class _EmptyRegisterStore(InMemoryStore):
    def list_schemes(self) -> list[SchemeRecord]:
        return []


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


def put_profile(client: TestClient, body: dict[str, Any] | None = None) -> None:
    client.put(f"{URL}/profile", json=body or PROFILE, headers=auth())


# ── the register itself ───────────────────────────────────────────────────────


def test_every_bundled_scheme_is_a_labelled_sample_with_no_amount() -> None:
    rows = load_schemes()
    assert len(rows) >= 6
    codes = {i.code for i in load_ideas()}
    for r in rows:
        assert r.is_sample and r.status == "draft" and r.last_checked_on == "unknown"
        assert set(r.idea_codes) <= codes, r.code
        assert r.official_url is None or r.official_url.startswith("https://")
        assert "qualify" not in r.who_en.lower() or "cannot tell you" in r.who_en.lower()
        assert not any(w in r.what_en.lower() for w in ("rs.", "₹", "lakh", "subsidy of"))
    assert {r.kind.value for r in rows} == {"government", "ngo"}


def _row(**over: Any) -> dict[str, Any]:
    base = load_schemes()[0].model_dump(mode="json")
    return {**base, **over}


def test_a_scheme_row_cannot_hold_an_amount_or_a_plain_http_link() -> None:
    with pytest.raises(ValidationError):
        SchemeRecord.model_validate(_row(amount=50000))  # no field for money, by design
    with pytest.raises(ValidationError):
        SchemeRecord.model_validate(_row(official_url="http://insecure.example"))
    with pytest.raises(ValidationError):
        SchemeRecord.model_validate(_row(help_types=["gold_mining"]))
    with pytest.raises(ValidationError):
        SchemeRecord.model_validate(_row(audiences=["rich"]))
    assert SchemeRecord.model_validate(_row(official_url="https://example.gov.in/x"))


# ── GET /schemes ──────────────────────────────────────────────────────────────


def test_schemes_need_a_login(client: TestClient) -> None:
    assert client.get(f"{URL}/schemes").status_code == 401
    assert client.get(f"{URL}/ideas/dairy_small").status_code == 401


def test_the_register_lists_everything_as_sample(client: TestClient) -> None:
    body = client.get(f"{URL}/schemes", headers=auth()).json()
    assert len(body["schemes"]) == len(load_schemes())
    assert body["is_sample_data"] is True and body["register_empty"] is False
    assert set(body["help_types"]) <= set(HELP_TYPES)
    assert set(body["audiences"]) <= set(AUDIENCES)
    assert all(s["is_sample"] for s in body["schemes"])


def test_the_register_filters(client: TestClient) -> None:
    def codes(query: str) -> set[str]:
        r = client.get(f"{URL}/schemes{query}", headers=auth())
        assert r.status_code == 200
        return {s["code"] for s in r.json()["schemes"]}

    gov, ngo = codes("?kind=government"), codes("?kind=ngo")
    assert gov and ngo and not gov & ngo
    fish = codes("?help=fishing")
    assert fish == {r.code for r in load_schemes() if "fishing" in r.help_types}
    women_ngo = codes("?kind=ngo&audience=women")
    assert women_ngo <= ngo and all(
        "women" in s.audiences for s in load_schemes() if s.code in women_ngo
    )
    assert (
        codes("?help=fishing&audience=tribal") == set()
    )  # nothing matches: an empty list, no error


@pytest.mark.parametrize(
    "query", ["?kind=bank", "?help=gold_mining", "?audience=rich", "?help=Farming!"]
)
def test_unknown_filters_are_refused(client: TestClient, query: str) -> None:
    assert client.get(f"{URL}/schemes{query}", headers=auth()).status_code == 422


def test_an_empty_register_says_so_and_is_not_marked_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch, _EmptyRegisterStore())
    try:
        body = client.get(f"{URL}/schemes", headers=auth()).json()
        assert body["schemes"] == [] and body["register_empty"] is True
        assert body["is_sample_data"] is False
    finally:
        get_settings.cache_clear()


# ── the report counts them ────────────────────────────────────────────────────


def test_each_idea_card_counts_the_schemes_that_name_it(client: TestClient) -> None:
    put_profile(client)
    report = client.post(f"{URL}/report", json={}, headers=auth()).json()
    counts = scheme_counts(load_schemes())
    for card in report["ideas"]:
        assert card["schemes_count"] == counts.get(card["code"], 0)
    assert any(c["schemes_count"] for c in report["ideas"])
    assert report["is_sample_data"] is True


def test_a_report_with_no_register_counts_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _client(monkeypatch, _EmptyRegisterStore())
    try:
        report = client.post(f"{URL}/report", json={}, headers=auth()).json()
        assert {c["schemes_count"] for c in report["ideas"]} == {0}
    finally:
        get_settings.cache_clear()


# ── GET /ideas/{code} ─────────────────────────────────────────────────────────


def test_an_idea_in_the_report_has_its_full_detail(client: TestClient) -> None:
    put_profile(client)
    report = client.post(f"{URL}/report", json={}, headers=auth()).json()
    card = next(c for c in report["ideas"] if c["code"] == "dairy_small")
    d = client.get(f"{URL}/ideas/dairy_small", headers=auth()).json()

    assert d["status"] == "in_report" and d["rank"] == card["rank"] and d["fit"] == card["fit"]
    assert d["reason"] == card["reason"] and d["flags"] == card["flags"]
    assert d["cost_level"] == card["cost_level"] and d["wildlife_risk"] == card["wildlife_risk"]
    checks = {c["check"]: c for c in d["checks"]}
    assert checks["law"]["result"] == "passed"
    assert checks["wildlife"]["reason"]["key"].startswith("detail.check.wildlife_")
    assert d["needs"] and all(n["options"] for n in d["needs"])
    # the resources it would use are the very ones in the report
    in_report = {r["id"]: r for r in report["resources"]}
    assert d["resources"] and all(r == in_report[r["id"]] for r in d["resources"])
    assert d["schemes"] and all(s["is_sample"] for s in d["schemes"])
    assert d["is_sample_data"] is True and d["draft"] is True
    assert d["weather_note"] is not None


def test_what_he_owns_counts_as_a_need_met(client: TestClient) -> None:
    put_profile(client)
    d = client.get(f"{URL}/ideas/dairy_small", headers=auth()).json()
    met = {n["met_by"] for n in d["needs"] if n["met_by"]}
    assert met  # a well or pump he owns, or water nearby
    idea = next(i for i in load_ideas() if i.code == "dairy_small")
    assert len(d["needs"]) == len(idea.needs)


def test_an_idea_removed_by_law_shows_the_law_and_no_schemes(client: TestClient) -> None:
    put_profile(client)
    d = client.get(f"{URL}/ideas/timber_sale", headers=auth()).json()
    assert d["status"] == "removed" and d["rank"] is None
    assert [c["check"] for c in d["checks"]] == ["law"]
    assert d["checks"][0]["result"] == "flagged"
    assert d["checks"][0]["reason"]["key"] == "gate.timber_or_harm"
    assert d["schemes"] == [] and d["needs"] == [] and d["resources"] == []


def test_an_idea_held_back_says_it_is_held_back(client: TestClient) -> None:
    put_profile(client)
    report = client.post(f"{URL}/report", json={}, headers=auth()).json()
    held = next(r for r in report["removed"] if r["gate"] is None)
    d = client.get(f"{URL}/ideas/{held['code']}", headers=auth()).json()
    assert d["status"] == "held_back" and d["reason"]["key"] == "reason.held_back_lower_fit"
    assert d["fit"] == held["fit"]


def test_an_idea_the_report_knows_nothing_about_is_a_404(client: TestClient) -> None:
    put_profile(client)
    for code in ("flying_cars", "wildlife_trapping"):  # unknown, and one kept off every list
        r = client.get(f"{URL}/ideas/{code}", headers=auth())
        assert r.status_code == 404 and r.json()["message_key"] == "livelihood.idea_not_found"


def test_detail_follows_his_own_details_not_someone_elses(client: TestClient) -> None:
    put_profile(client)
    client.put(
        f"{URL}/profile",
        json={"assets": ["shed"], "land": {"area_value": 0.1, "area_unit": "acre"}},
        headers=auth(DEV_VILLAGER_2.id),
    )
    mine = client.get(f"{URL}/ideas/dairy_small", headers=auth(DEV_VILLAGER.id)).json()
    theirs = client.get(f"{URL}/ideas/dairy_small", headers=auth(DEV_VILLAGER_2.id)).json()
    assert mine != theirs


def test_detail_has_no_scores(client: TestClient) -> None:
    put_profile(client)
    text = client.get(f"{URL}/ideas/dairy_small", headers=auth()).text
    for word in ('"score"', '"fit_score"', '"f":', '"u":'):
        assert word not in text


def test_a_land_check_appears_only_for_ideas_with_a_minimum(client: TestClient) -> None:
    put_profile(client, {**PROFILE, "land": {"area_value": 0.05, "area_unit": "acre"}})
    dairy = client.get(f"{URL}/ideas/dairy_small", headers=auth()).json()  # needs about 0.2 ha
    land = [c for c in dairy["checks"] if c["check"] == "land"]
    assert land and land[0]["result"] == "flagged"
    assert land[0]["reason"]["key"] == "flag.needs_more_land"
    # with enough land the same check passes
    put_profile(client, {**PROFILE, "land": {"area_value": 3, "area_unit": "acre"}})
    dairy = client.get(f"{URL}/ideas/dairy_small", headers=auth()).json()
    assert [c["result"] for c in dairy["checks"] if c["check"] == "land"] == ["passed"]
    # an idea with no minimum has no land check at all
    plain = client.get(f"{URL}/ideas/mushroom_shed", headers=auth())
    if plain.status_code == 200:
        assert not [c for c in plain.json()["checks"] if c["check"] == "land"]


# ── pure function ─────────────────────────────────────────────────────────────


def test_build_detail_is_pure_and_needs_the_idea_to_be_in_the_report(
    records,
    dataset,
    village,  # type: ignore[no-untyped-def]
) -> None:
    ideas = load_ideas()
    report = build_report(
        profile=ProfileIn.model_validate(PROFILE),
        user_name="T",
        village=village,
        resources=records,
        ideas=ideas,
        dataset=dataset,
        weather=load_sample_weather(),
        schemes=load_schemes(),
    )
    top = next(i for i in ideas if i.code == report.ideas[0].code)
    detail = build_idea_detail(report, top, load_schemes())
    assert detail is not None and detail.rank == 1
    assert (
        build_idea_detail(report, Idea.model_validate({**top.model_dump(), "code": "nope"}), [])
        is None
    )


# ── Ask uses the counts ───────────────────────────────────────────────────────


def test_ask_about_schemes_names_the_ideas_and_never_says_he_qualifies(client: TestClient) -> None:
    put_profile(client)
    r = client.post(f"{URL}/ask", json={"question": "Which schemes can help me?"}, headers=auth())
    answer = r.json()["turn"]["answer"]
    assert answer["kind"] == "ANSWER" and answer["topic"] == "schemes"
    assert answer["headline"]["key"] == "ask.schemes.header"
    assert answer["items"] and all(i["key"] == "ask.item.idea_schemes" for i in answer["items"])
    assert "schemes" in {c["id"] for c in r.json()["chips"]}
    chip = client.post(f"{URL}/ask", json={"chip": "schemes"}, headers=auth())
    assert chip.json()["turn"]["answer"]["kind"] == "ANSWER"


def test_ask_about_schemes_with_an_empty_register_is_not_in_the_report(
    records,
    ideas,
    dataset,
    village,  # type: ignore[no-untyped-def]
) -> None:
    report = build_report(
        profile=None,
        user_name="T",
        village=village,
        resources=records,
        ideas=ideas,
        dataset=dataset,
    )
    a = ask_engine.respond("which schemes are there", report, ideas)
    assert a.kind is AnswerKind.NOT_IN_REPORT

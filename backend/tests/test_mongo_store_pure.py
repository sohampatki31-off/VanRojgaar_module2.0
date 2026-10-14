"""The parts of the Mongo store that need no database: document conversion and index definitions."""

from datetime import UTC, datetime

from app.livelihood.mongo_store import INDEXES, doc_to_profile, profile_to_doc
from app.livelihood.schemas import ProfileIn
from app.livelihood.store import StoredProfile


def _stored() -> StoredProfile:
    return StoredProfile(
        user_id="u1",
        village_id="sample_ozhar",
        profile=ProfileIn.model_validate(
            {
                "land": {"area_value": 40, "area_unit": "guntha", "land_type": "rain_fed"},
                "location": {"lat": 19.78, "lng": 73.22, "source": "gps"},
                "livestock": {"cow": 2},
                "assets": ["pump", "well"],
                "past_work": ["dairy"],
                "money_level": "low",
            }
        ),
        created_at=datetime(2026, 10, 14, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 10, 14, 13, 0, tzinfo=UTC),
    )


def test_document_round_trip_is_lossless() -> None:
    stored = _stored()
    assert doc_to_profile(profile_to_doc(stored)) == stored


def test_document_holds_only_plain_json_types() -> None:
    doc = profile_to_doc(_stored())
    # enums are stored as their text, so the database never holds Python-specific values
    assert doc["profile"]["land"]["area_unit"] == "guntha"
    assert doc["profile"]["money_level"] == "low"
    assert set(doc) == {"user_id", "village_id", "profile", "created_at", "updated_at"}


def test_document_never_carries_sensitive_fields() -> None:
    """We never ask or store caste, income or ID numbers (rule L8)."""
    text = repr(profile_to_doc(_stored())).lower()
    for banned in ("caste", "income", "aadhaar", "pan"):
        assert banned not in text


def test_user_id_index_is_unique() -> None:
    names = {ix.document["name"]: ix.document for ixs in INDEXES.values() for ix in ixs}
    assert names["user_unique"].get("unique") is True
    assert names["village_unique"].get("unique") is True

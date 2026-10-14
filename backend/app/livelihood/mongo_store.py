"""
The MongoDB implementation of LivelihoodStore.

IMPORTANT: this file has been unit-tested for its pure parts (document conversion, index
definitions) but NOT run against a real database by the author: database writes are run by a
person (CLAUDE.md). Run `scripts/smoke_mongo.py` against a THROWAWAY database before trusting it.

Collections use the `lv_` prefix (docs/BACKEND_PLAN.md §2). Dates are stored as UTC datetimes;
ids are strings here because the standalone module has no host UUID layer.
"""

from typing import Any

from pymongo import ASCENDING, IndexModel, MongoClient
from pymongo.collection import Collection

from ..config import Settings
from .schemas import ProfileIn, VillageGeo
from .store import StoredProfile

PROFILES = "lv_profile"
VILLAGES = "lv_village_geo"

# Created by `scripts/setup_livelihood_indexes.py` (a person runs it). In the host, merge these
# into `INDEXES` in app/mongo.py instead.
INDEXES: dict[str, list[IndexModel]] = {
    PROFILES: [IndexModel([("user_id", ASCENDING)], name="user_unique", unique=True)],
    VILLAGES: [IndexModel([("village_id", ASCENDING)], name="village_unique", unique=True)],
}


def profile_to_doc(stored: StoredProfile) -> dict[str, Any]:
    return {
        "user_id": stored.user_id,
        "village_id": stored.village_id,
        "profile": stored.profile.model_dump(mode="json"),
        "created_at": stored.created_at,
        "updated_at": stored.updated_at,
    }


def doc_to_profile(doc: dict[str, Any]) -> StoredProfile:
    return StoredProfile(
        user_id=doc["user_id"],
        village_id=doc.get("village_id"),
        profile=ProfileIn.model_validate(doc["profile"]),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class MongoStore:
    def __init__(self, client: "MongoClient[dict[str, Any]]", db_name: str) -> None:
        self._db = client[db_name]

    @classmethod
    def from_settings(cls, settings: Settings) -> "MongoStore":
        client: MongoClient[dict[str, Any]] = MongoClient(
            settings.mongodb_uri,
            tz_aware=True,
            serverSelectionTimeoutMS=settings.db_connect_timeout_s * 1000,
            appname="vanmitra-livelihood",
        )
        return cls(client, settings.mongodb_db)

    def _col(self, name: str) -> "Collection[dict[str, Any]]":
        return self._db[name]

    def get_profile(self, user_id: str) -> StoredProfile | None:
        doc = self._col(PROFILES).find_one({"user_id": user_id})
        return doc_to_profile(doc) if doc else None

    def put_profile(
        self, user_id: str, village_id: str | None, profile: ProfileIn
    ) -> StoredProfile:
        existing = self.get_profile(user_id)
        stored = StoredProfile(user_id=user_id, village_id=village_id, profile=profile)
        if existing:
            stored = stored.model_copy(update={"created_at": existing.created_at})
        # replace, never merge: what he sends is the whole truth about his answers
        self._col(PROFILES).replace_one({"user_id": user_id}, profile_to_doc(stored), upsert=True)
        return stored

    def delete_profile(self, user_id: str) -> bool:
        return self._col(PROFILES).delete_one({"user_id": user_id}).deleted_count > 0

    def get_village(self, village_id: str) -> VillageGeo | None:
        doc = self._col(VILLAGES).find_one({"village_id": village_id})
        if not doc:
            return None
        doc.pop("_id", None)
        return VillageGeo.model_validate(doc)

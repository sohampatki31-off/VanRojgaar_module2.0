"""
Where profiles (and, in module 3, reports and resources) are kept.

`LivelihoodStore` is the one interface the routes use. Two implementations:
- `InMemoryStore`: nothing persists. Development and tests. Needs no database.
- `MongoStore` (mongo_store.py): the real database.

At merge the host's `Store` unit of work replaces `MongoStore`; the routes do not change.
Every method is keyed by the signed-in user's id: there is no way to ask for someone else's data.
"""

import threading
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Protocol

from pydantic import BaseModel, Field

from ..config import get_settings
from .schemas import ProfileIn, VillageGeo
from .seed import load_demo_village


class StoredProfile(BaseModel):
    """A saved profile: what he told us, and when. Exists once per user."""

    user_id: str
    village_id: str | None
    profile: ProfileIn
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LivelihoodStore(Protocol):
    def get_profile(self, user_id: str) -> StoredProfile | None: ...

    def put_profile(
        self, user_id: str, village_id: str | None, profile: ProfileIn
    ) -> StoredProfile:
        """Create or REPLACE (never merge) the user's profile. created_at is kept on replace."""
        ...

    def delete_profile(self, user_id: str) -> bool:
        """Delete his answers (rule L8). True if there was something to delete."""
        ...

    def get_village(self, village_id: str) -> VillageGeo | None: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._profiles: dict[str, StoredProfile] = {}

    def get_profile(self, user_id: str) -> StoredProfile | None:
        with self._lock:
            stored = self._profiles.get(user_id)
            return stored.model_copy(deep=True) if stored else None

    def put_profile(
        self, user_id: str, village_id: str | None, profile: ProfileIn
    ) -> StoredProfile:
        with self._lock:
            now = datetime.now(UTC)
            existing = self._profiles.get(user_id)
            stored = StoredProfile(
                user_id=user_id,
                village_id=village_id,
                profile=profile,
                created_at=existing.created_at if existing else now,
                updated_at=now,
            )
            self._profiles[user_id] = stored
            return stored.model_copy(deep=True)

    def delete_profile(self, user_id: str) -> bool:
        with self._lock:
            return self._profiles.pop(user_id, None) is not None

    def get_village(self, village_id: str) -> VillageGeo | None:
        demo = load_demo_village()
        return demo if demo.village_id == village_id else None


_memory_store = InMemoryStore()


@lru_cache
def _mongo_store() -> Any:
    from .mongo_store import MongoStore  # imported lazily: tests and dev need no database

    return MongoStore.from_settings(get_settings())


def get_store() -> LivelihoodStore:
    """FastAPI dependency. Tests override it; production picks the Mongo store by setting."""
    if get_settings().livelihood_store == "mongo":
        store: LivelihoodStore = _mongo_store()
        return store
    return _memory_store

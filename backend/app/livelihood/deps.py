"""
THE ONLY FILE THAT DIFFERS BETWEEN THE STANDALONE APP AND THE HOST (docs/INTEGRATION.md).

It answers two questions the routes ask:
- `CurrentUser`: who is calling? (standalone: a dev/JWT directory in auth.py. Host: the host's own
  login and role grants.)
- `get_store`: where is the data? (standalone: in memory, or Mongo by setting. Host: the host's
  MongoDB database.)

Routes and tests override these two names with `app.dependency_overrides`, so they never depend
on how either is wired.
"""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends

from ..config import get_settings
from .auth import get_current_user
from .identity import UserInfo
from .store import InMemoryStore, LivelihoodStore

# ── who is calling ────────────────────────────────────────────────────────────

CurrentUser = Annotated[UserInfo, Depends(get_current_user)]

# ── where the data is ─────────────────────────────────────────────────────────

_memory_store = InMemoryStore()


@lru_cache
def _mongo_store() -> Any:
    from .mongo_store import MongoStore  # imported lazily: tests and dev need no database

    return MongoStore.from_settings(get_settings())


def get_store() -> LivelihoodStore:
    """FastAPI dependency. Tests override it; the standalone app picks Mongo by setting."""
    if get_settings().livelihood_store == "mongo":
        store: LivelihoodStore = _mongo_store()
        return store
    return _memory_store

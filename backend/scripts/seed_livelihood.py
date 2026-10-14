"""
[USER RUNS] Seed the idea library and the demo village into MongoDB.

    python scripts/seed_livelihood.py            # dry run: prints what it would write
    python scripts/seed_livelihood.py --apply    # writes

Upserts by `code` (ideas) and `village_id` (village): safe to run again, and never deletes. The
ideas are a DRAFT, not reviewed by a forest-law expert, an agriculture expert, an animal-welfare
NGO or the Forest Department (docs/IDEA_LIBRARY.md). The demo village is SAMPLE data: do not seed
it into a database that serves real users.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymongo import MongoClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.livelihood.mongo_store import IDEAS, VILLAGES  # noqa: E402
from app.livelihood.seed import load_demo_village, load_ideas  # noqa: E402


def main(apply: bool) -> None:
    s = get_settings()
    ideas = load_ideas()
    village = load_demo_village()
    print(f"database: {s.mongodb_db}   mode: {'APPLY' if apply else 'dry run'}")
    print(f"  ideas: {len(ideas)} (draft): {', '.join(i.code for i in ideas)}")
    print(f"  village: {village.village_id} (sample={village.is_sample})")
    if not apply:
        print("dry run only; add --apply to write")
        return
    client: MongoClient[dict[str, object]] = MongoClient(
        s.mongodb_uri, serverSelectionTimeoutMS=s.db_connect_timeout_s * 1000
    )
    db = client[s.mongodb_db]
    for idea in ideas:
        db[IDEAS].replace_one({"code": idea.code}, idea.model_dump(mode="json"), upsert=True)
    db[VILLAGES].replace_one(
        {"village_id": village.village_id}, village.model_dump(mode="json"), upsert=True
    )
    print("done")


if __name__ == "__main__":
    main("--apply" in sys.argv)

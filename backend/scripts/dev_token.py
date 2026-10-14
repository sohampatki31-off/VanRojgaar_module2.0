"""
Print a login token for a built-in DEVELOPMENT user, in the host's token format. No database.

    python scripts/dev_token.py            # the demo villager
    python scripts/dev_token.py 2          # the second villager

Use it as:  Authorization: Bearer <token>. Needs VANMITRA_LIVELIHOOD_DEV_USERS=true on the
server. Refused when VANMITRA_ENV=production.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.livelihood.auth import DEV_VILLAGER, DEV_VILLAGER_2, create_access_token  # noqa: E402


def main() -> None:
    if get_settings().env == "production":
        raise SystemExit("refusing to mint a dev token in production")
    user = DEV_VILLAGER_2 if sys.argv[1:] == ["2"] else DEV_VILLAGER
    print(create_access_token(user.id, minutes=60 * 24))


if __name__ == "__main__":
    main()

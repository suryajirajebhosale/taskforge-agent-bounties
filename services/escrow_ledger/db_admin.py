"""Schema management via SQLAlchemy directly — no separate migration framework.

For now this is `create_all`/`drop_all` against the current model definitions in
`models.py`, which is sufficient while the schema is still additive and there's no real
data to preserve across changes. Once the schema needs versioned, in-place changes
against a live database with real data, this is where that logic should live — e.g.
hand-written, numbered upgrade steps gated by a small `schema_version` table this module
tracks itself — rather than pulling in a separate tool.

Usage: `uv run python -m services.escrow_ledger.db_admin create|drop`
"""

import argparse

from sqlalchemy import Engine

from .database import Base, make_engine
from .models import *  # noqa: F401,F403  (ensures every table is registered on Base.metadata)


def create_all(engine: Engine | None = None) -> None:
    """Create every table that doesn't already exist. Safe to call repeatedly."""
    Base.metadata.create_all(engine or make_engine())


def drop_all(engine: Engine | None = None) -> None:
    """Drop every table this service owns. Local/test use only — never run this
    against an environment holding real escrow data."""
    Base.metadata.drop_all(engine or make_engine())


def _main() -> None:
    parser = argparse.ArgumentParser(description="Escrow ledger schema management.")
    parser.add_argument("action", choices=["create", "drop"])
    args = parser.parse_args()

    if args.action == "create":
        create_all()
        print("Tables created.")
    else:
        drop_all()
        print("Tables dropped.")


if __name__ == "__main__":
    _main()

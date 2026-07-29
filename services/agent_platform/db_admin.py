"""Schema management via SQLAlchemy directly — no separate migration framework.
Mirrors `services/escrow_ledger/db_admin.py`; see that module's docstring for the
rationale and for how this should evolve once real data needs to survive schema changes.

Usage: `uv run python -m services.agent_platform.db_admin create|drop`
"""

import argparse

from sqlalchemy import Engine

from .database import Base, make_engine
from .models import *  # noqa: F401,F403  (ensures every table is registered on Base.metadata)


def create_all(engine: Engine | None = None) -> None:
    Base.metadata.create_all(engine or make_engine())


def drop_all(engine: Engine | None = None) -> None:
    Base.metadata.drop_all(engine or make_engine())


def _main() -> None:
    parser = argparse.ArgumentParser(description="Agent platform schema management.")
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

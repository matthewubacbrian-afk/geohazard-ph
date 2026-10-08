"""Preview or apply a full canonical-event reconciliation."""

import argparse
import logging

from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.services.dedup import reconcile_canonical_events

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile persisted canonical event groups")
    parser.add_argument("--apply", action="store_true", help="Commit the proposed corrections")
    args = parser.parse_args()
    configure_logging()
    with SessionLocal() as session:
        inspected, changed = reconcile_canonical_events(session, apply=args.apply)
    logger.info(
        "canonical event reconciliation complete",
        extra={"inspected": inspected, "changed": changed, "applied": args.apply},
    )


if __name__ == "__main__":
    main()

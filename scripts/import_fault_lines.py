"""Quarterly import of reviewed GEM/PHIVOLCS reference vectors."""

import argparse
import logging
from pathlib import Path

from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.services.static_layers import replace_layer
from ingestion.sources.static_layers import parse_features, read_features

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", choices=["faults", "volcano_zones"], default="faults")
    parser.add_argument("--source", choices=["gem", "phivolcs"], required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--license-name", required=True)
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    configure_logging()
    try:
        rows = parse_features(
            read_features(args.path),
            kind=args.kind,
            source=args.source,
            source_url=args.source_url,
            license_name=args.license_name,
            dataset_version=args.dataset_version,
        )
        if not rows:
            raise ValueError(
                "No features intersect the Philippines; existing data retained"
            )
        if not args.dry_run:
            with SessionLocal() as session:
                replace_layer(session, rows, kind=args.kind, source=args.source)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Import failed: {exc}\n")
    logger.info(
        "Static layer validated" if args.dry_run else "Static layer imported",
        extra={"count": len(rows), "source": args.source, "kind": args.kind},
    )


if __name__ == "__main__":
    main()

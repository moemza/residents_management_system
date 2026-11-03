#!/usr/bin/env python3
"""Safely normalise legacy HTML-escaped text in a SQLite database.

Usage:
    # Report only (default; no writes, no backup)
    python scripts/migrate_unescape.py --db /path/to/residents.db

    # Apply changes after creating a verified backup
    python scripts/migrate_unescape.py --db /path/to/residents.db --apply

The script refuses to run without an explicit database path. It never reads the
repository database implicitly. Run it against a copy or a synthetic database
first, and obtain operational approval before touching production data.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.migrations import MigrationError, migrate_unescape  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Path to the SQLite database")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes after creating and verifying a backup (default: dry run)",
    )
    parser.add_argument(
        "--backup-dir",
        default=None,
        help="Backup directory (default: <database directory>/backups)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as JSON",
    )
    args = parser.parse_args(argv)

    try:
        report = migrate_unescape(
            args.db,
            apply=args.apply,
            backup_dir=args.backup_dir,
        )
    except MigrationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        mode = "APPLIED" if report.applied else "DRY RUN"
        print(f"Mode: {mode}")
        print(f"Database: {report.database}")
        print(f"Values to change: {report.changes_found}")
        print(f"Rows affected: {report.rows_changed}")
        if report.backup_path:
            print(f"Backup: {report.backup_path}")
        for change in report.changes[:20]:
            print(
                f"  {change.table}.{change.column} id={change.row_id}: "
                f"{change.before!r} -> {change.after!r}"
            )
        if report.changes_found > 20:
            print(f"  … {report.changes_found - 20} more")
        if report.dry_run and report.changes_found:
            print("No changes were written. Re-run with --apply to apply them.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

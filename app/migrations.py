"""Utilities for normalising legacy HTML-escaped text in an existing database.

Older versions applied ``html.escape`` before persistence. This module finds
those escaped values, reports them, and can rewrite them as raw text after
taking a verified SQLite backup.

The utility is deliberately conservative:

* Dry-run is the default; nothing is written without ``apply=True``.
* Only an explicit allow-list of text columns is touched.
* Only the five entities emitted by ``html.escape`` are decoded. Other
  entity-like text that a user typed is preserved verbatim.
* A consistent backup is created and integrity-checked before any write.
* Each row is updated in a single transaction.
* Running the migration twice is a no-op.

This module never connects to the repository database unless a caller passes
that path. The CLI defaults to a dry run.
"""

from __future__ import annotations

import pathlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

# ``html.escape(quote=True)`` emits exactly these entities. Decode ``&amp;``
# last so a single pass cannot turn ``&amp;lt;`` into ``<`` (double-unescaping).
LEGACY_ESCAPES: tuple[tuple[str, str], ...] = (
    ("&lt;", "<"),
    ("&gt;", ">"),
    ("&quot;", '"'),
    ("&#x27;", "'"),
    ("&amp;", "&"),
)


def unescape_legacy(text: str) -> str:
    """Decode only the entities produced by the legacy ``html.escape`` call."""
    for escaped, raw in LEGACY_ESCAPES:
        text = text.replace(escaped, raw)
    return text


# Fixed allow-list: never interpolate table or column names from user input.
TEXT_COLUMNS: dict[str, tuple[str, ...]] = {
    "residents": (
        "first_name",
        "last_name",
        "gender",
        "village",
        "cellphone_no",
        "cellphone_no2",
        "email",
    ),
    "qualifications": ("institution", "name", "type", "level", "year"),
    "experiences": ("company", "position", "years"),
    "skills": ("name",),
}


class MigrationError(RuntimeError):
    """Raised when the database is not safe to migrate."""


@dataclass
class Change:
    table: str
    column: str
    row_id: int
    before: str
    after: str


@dataclass
class MigrationReport:
    database: str
    dry_run: bool
    changes: list[Change] = field(default_factory=list)
    backup_path: str | None = None
    applied: bool = False

    @property
    def changes_found(self) -> int:
        return len(self.changes)

    @property
    def rows_changed(self) -> int:
        return len({(change.table, change.row_id) for change in self.changes})

    def as_dict(self, sample_limit: int | None = 20) -> dict:
        changes = self.changes
        if sample_limit is not None:
            changes = changes[:sample_limit]
        return {
            "database": self.database,
            "dry_run": self.dry_run,
            "applied": self.applied,
            "changes_found": self.changes_found,
            "rows_changed": self.rows_changed,
            "backup_path": self.backup_path,
            "changes": [
                {
                    "table": change.table,
                    "column": change.column,
                    "id": change.row_id,
                    "before": change.before,
                    "after": change.after,
                }
                for change in changes
            ],
        }


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _column_exists(connection: sqlite3.Connection, table: str, column: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def find_changes(connection: sqlite3.Connection) -> list[Change]:
    """Return text values that would change when HTML entities are unescaped."""
    changes: list[Change] = []
    for table, columns in TEXT_COLUMNS.items():
        if not _table_exists(connection, table):
            raise MigrationError(f"Expected table is missing: {table}")
        for column in columns:
            if not _column_exists(connection, table, column):
                raise MigrationError(f"Expected column is missing: {table}.{column}")
            rows = connection.execute(
                f"SELECT id, {column} FROM {table} WHERE {column} IS NOT NULL"
            ).fetchall()
            for row_id, value in rows:
                text = str(value)
                unescaped = unescape_legacy(text)
                if unescaped != text:
                    changes.append(
                        Change(
                            table=table,
                            column=column,
                            row_id=row_id,
                            before=text,
                            after=unescaped,
                        )
                    )
    return changes


def _backup_database(db_path: pathlib.Path, backup_dir: pathlib.Path) -> pathlib.Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = backup_dir / f"residents_pre_migration_{timestamp}.db"

    source = sqlite3.connect(db_path)
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    check = sqlite3.connect(backup_path)
    try:
        result = check.execute("PRAGMA quick_check").fetchone()
    finally:
        check.close()
    if not result or result[0] != "ok":
        backup_path.unlink(missing_ok=True)
        raise MigrationError("Migration backup failed its integrity check")

    return backup_path


def migrate_unescape(
    db_path: str | pathlib.Path,
    *,
    apply: bool = False,
    backup_dir: str | pathlib.Path | None = None,
) -> MigrationReport:
    """Report or apply HTML-entity unescaping for a SQLite database.

    ``apply=False`` (the default) performs no writes and creates no backup.
    """
    path = pathlib.Path(db_path).expanduser()
    if not path.exists():
        raise MigrationError(f"Database not found: {path}")

    connection = sqlite3.connect(path)
    try:
        changes = find_changes(connection)
        report = MigrationReport(database=str(path), dry_run=not apply, changes=changes)

        if not apply or not changes:
            return report

        destination = (
            pathlib.Path(backup_dir).expanduser()
            if backup_dir is not None
            else path.parent / "backups"
        )
        report.backup_path = str(_backup_database(path, destination))

        try:
            with connection:
                for change in changes:
                    connection.execute(
                        f"UPDATE {change.table} SET {change.column} = ? WHERE id = ?",
                        (change.after, change.row_id),
                    )
        except sqlite3.Error:
            # The context manager rolls back on exception. The pre-migration
            # backup remains available for recovery.
            raise
        report.applied = True
        return report
    finally:
        connection.close()


def iter_tables() -> Iterable[str]:
    """Expose the allow-listed tables for documentation and tests."""
    return TEXT_COLUMNS.keys()

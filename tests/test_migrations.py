"""Synthetic tests for the legacy HTML-entity migration utility."""

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from app.migrations import MigrationError, migrate_unescape


def _make_synthetic_db(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE residents (
            id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            gender TEXT,
            village TEXT,
            cellphone_no TEXT,
            cellphone_no2 TEXT,
            email TEXT
        );
        CREATE TABLE qualifications (
            id INTEGER PRIMARY KEY,
            institution TEXT,
            name TEXT,
            type TEXT,
            level TEXT,
            year TEXT,
            resident_id INTEGER
        );
        CREATE TABLE experiences (
            id INTEGER PRIMARY KEY,
            company TEXT,
            position TEXT,
            years TEXT,
            resident_id INTEGER
        );
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY,
            name TEXT,
            resident_id INTEGER
        );
        """
    )
    connection.execute(
        """
        INSERT INTO residents
            (id, first_name, last_name, gender, village, cellphone_no, cellphone_no2, email)
        VALUES (1, 'Thabo &amp; Sons', 'O&#x27;Brien', 'Male', 'Village A',
                '0821234567', NULL, 'thabo@example.com')
        """
    )
    connection.execute(
        """
        INSERT INTO qualifications
            (id, institution, name, type, level, year, resident_id)
        VALUES (1, 'UNISA', 'Software Engineering', 'Degree', 'NQF 7', '2020', 1)
        """
    )
    connection.execute(
        "INSERT INTO experiences (id, company, position, years, resident_id) "
        "VALUES (1, 'Acme &amp; Co', 'Developer', '3', 1)"
    )
    connection.execute(
        "INSERT INTO skills (id, name, resident_id) VALUES (1, 'C&amp;A', 1)"
    )
    connection.commit()
    connection.close()


def test_dry_run_reports_without_writing(tmp_path):
    database = tmp_path / "synthetic.db"
    _make_synthetic_db(database)

    report = migrate_unescape(database)

    assert report.dry_run is True
    assert report.applied is False
    assert report.changes_found == 4
    assert report.rows_changed == 3
    assert report.backup_path is None

    connection = sqlite3.connect(database)
    try:
        value = connection.execute("SELECT first_name FROM residents WHERE id = 1").fetchone()[0]
        assert value == "Thabo &amp; Sons"
    finally:
        connection.close()


def test_apply_unescapes_values_and_creates_verified_backup(tmp_path):
    database = tmp_path / "synthetic.db"
    backup_dir = tmp_path / "backups"
    _make_synthetic_db(database)

    report = migrate_unescape(database, apply=True, backup_dir=backup_dir)

    assert report.applied is True
    assert report.changes_found == 4
    assert report.backup_path is not None

    backup = Path(report.backup_path)
    assert backup.exists()
    backup_connection = sqlite3.connect(backup)
    try:
        assert backup_connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert (
            backup_connection.execute("SELECT first_name FROM residents WHERE id = 1").fetchone()[0]
            == "Thabo &amp; Sons"
        )
    finally:
        backup_connection.close()

    connection = sqlite3.connect(database)
    try:
        resident = connection.execute(
            "SELECT first_name, last_name FROM residents WHERE id = 1"
        ).fetchone()
        assert resident == ("Thabo & Sons", "O'Brien")
        assert connection.execute("SELECT company FROM experiences WHERE id = 1").fetchone()[0] == "Acme & Co"
        assert connection.execute("SELECT name FROM skills WHERE id = 1").fetchone()[0] == "C&A"
    finally:
        connection.close()


def test_second_apply_is_a_no_op(tmp_path):
    database = tmp_path / "synthetic.db"
    _make_synthetic_db(database)

    first = migrate_unescape(database, apply=True, backup_dir=tmp_path / "backups")
    assert first.applied is True

    second = migrate_unescape(database, apply=True, backup_dir=tmp_path / "backups")
    assert second.changes_found == 0
    assert second.applied is False


def test_missing_database_is_rejected(tmp_path):
    with pytest.raises(MigrationError):
        migrate_unescape(tmp_path / "missing.db")


def test_missing_expected_table_is_rejected(tmp_path):
    database = tmp_path / "incomplete.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE residents (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()

    with pytest.raises(MigrationError):
        migrate_unescape(database)


def test_only_legacy_escape_entities_are_decoded(tmp_path):
    """Entity-like text a user typed is preserved, not turned into symbols."""
    database = tmp_path / "synthetic.db"
    _make_synthetic_db(database)
    connection = sqlite3.connect(database)
    try:
        # ``html.escape`` would have produced this from a literal "&copy;".
        connection.execute(
            "UPDATE residents SET first_name = '&amp;copy; and &amp;lt;' WHERE id = 1"
        )
        connection.commit()
    finally:
        connection.close()

    migrate_unescape(database, apply=True, backup_dir=tmp_path / "backups")

    connection = sqlite3.connect(database)
    try:
        value = connection.execute("SELECT first_name FROM residents WHERE id = 1").fetchone()[0]
    finally:
        connection.close()
    # One pass only: "&amp;copy;" -> "&copy;" (not ©), "&amp;lt;" -> "&lt;" (not <).
    assert value == "&copy; and &lt;"


def test_cli_dry_run_is_safe(tmp_path):
    database = tmp_path / "synthetic.db"
    _make_synthetic_db(database)
    script = Path(__file__).resolve().parent.parent / "scripts" / "migrate_unescape.py"

    result = subprocess.run(
        [sys.executable, str(script), "--db", str(database), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert '"dry_run": true' in result.stdout
    assert '"changes_found": 4' in result.stdout

    connection = sqlite3.connect(database)
    try:
        assert (
            connection.execute("SELECT first_name FROM residents WHERE id = 1").fetchone()[0]
            == "Thabo &amp; Sons"
        )
    finally:
        connection.close()

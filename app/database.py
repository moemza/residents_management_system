import glob
import logging
import os
import pathlib
import sqlite3
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "database" / "residents.db"
DEFAULT_BACKUP_DIR = BASE_DIR / "database" / "backups"

DEFAULT_BACKUP_RETENTION = 10


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    """Read a positive integer environment variable with a safe fallback."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError:
        logger.warning("Invalid integer for %s; using %s", name, default)
        return default
    return parsed if parsed >= minimum else default


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a conservative default."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _env_path(name: str, default: pathlib.Path) -> pathlib.Path:
    """Read a path environment variable, falling back to the default."""
    value = os.environ.get(name, "").strip()
    return pathlib.Path(value).expanduser() if value else default


# Runtime paths are configurable so tests and deployments do not have to write
# to the repository's default database location. Defaults preserve the
# documented single-file SQLite setup.
DB_PATH = _env_path("RESIDENTS_DB_PATH", DEFAULT_DB_PATH)
BACKUP_DIR = _env_path("RESIDENTS_BACKUP_DIR", DEFAULT_BACKUP_DIR)
BACKUP_ENABLED = _env_bool("RESIDENTS_BACKUP_ENABLED", True)
BACKUP_REQUIRED = _env_bool("RESIDENTS_BACKUP_REQUIRED", False)
BACKUP_RETENTION = _env_int(
    "RESIDENTS_BACKUP_RETENTION", DEFAULT_BACKUP_RETENTION, minimum=1
)
DB_INTEGRITY_CHECK = _env_bool("RESIDENTS_DB_INTEGRITY_CHECK", True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """Enable foreign-key enforcement for every SQLite connection.

    SQLite does not enforce foreign keys unless this pragma is set per
    connection. The listener is registered globally because tests create their
    own SQLAlchemy engine.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


# Search columns and foreign keys are indexed explicitly. SQLAlchemy's
# ``create_all`` adds indexes for new databases; ``ensure_indexes`` adds them to
# databases created before these indexes existed.
INDEX_STATEMENTS = (
    "CREATE INDEX IF NOT EXISTS ix_residents_first_name ON residents (first_name)",
    "CREATE INDEX IF NOT EXISTS ix_residents_last_name ON residents (last_name)",
    "CREATE INDEX IF NOT EXISTS ix_residents_village ON residents (village)",
    "CREATE INDEX IF NOT EXISTS ix_qualifications_resident_id ON qualifications (resident_id)",
    "CREATE INDEX IF NOT EXISTS ix_qualifications_name ON qualifications (name)",
    "CREATE INDEX IF NOT EXISTS ix_experiences_resident_id ON experiences (resident_id)",
    "CREATE INDEX IF NOT EXISTS ix_skills_resident_id ON skills (resident_id)",
    "CREATE INDEX IF NOT EXISTS ix_skills_name ON skills (name)",
)


def ensure_indexes() -> None:
    """Create missing indexes on an existing database without altering tables."""
    with engine.begin() as connection:
        for statement in INDEX_STATEMENTS:
            connection.exec_driver_sql(statement)


def create_tables():
    # Import models so their tables are registered when this function is used
    # directly (for example, ``python -m app.database``).
    from . import models  # noqa: F401

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    ensure_indexes()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _next_backup_path(backup_dir: pathlib.Path) -> pathlib.Path:
    """Return a backup path that does not overwrite an existing backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    candidate = backup_dir / f"residents_backup_{timestamp}.db"
    counter = 1
    while candidate.exists():
        candidate = backup_dir / f"residents_backup_{timestamp}_{counter:02d}.db"
        counter += 1
    return candidate


def _integrity_ok(database_file: pathlib.Path) -> bool:
    """Run SQLite's quick integrity check on a database file."""
    connection = sqlite3.connect(database_file, timeout=5)
    try:
        result = connection.execute("PRAGMA quick_check").fetchone()
        return bool(result) and result[0] == "ok"
    finally:
        connection.close()


def verify_database_integrity() -> bool:
    """Return whether the configured database passes SQLite's quick check.

    A missing file is treated as healthy because startup creates it. A corrupt
    or unreadable file returns ``False`` so the application can refuse to serve
    data from it.
    """
    if not DB_PATH.exists():
        return True
    try:
        return _integrity_ok(DB_PATH)
    except sqlite3.Error as error:
        logger.error("Database integrity check failed: %s", error)
        return False


def backup_database() -> bool:
    """Create a consistent timestamped snapshot of the SQLite database.

    The snapshot uses SQLite's online backup API instead of copying the file.
    This avoids capturing a database mid-transaction and works while the
    application holds the database open.

    Backups are disabled when ``RESIDENTS_BACKUP_ENABLED`` is false. Tests set
    this to false so they never copy or rotate the configured application
    database.

    Returns ``True`` when a verified backup was created, otherwise ``False``.
    """
    if not BACKUP_ENABLED:
        logger.debug("Database backups are disabled")
        return False

    source_db = DB_PATH
    if not source_db.exists():
        logger.warning("Source database not found: %s", source_db)
        return False

    backup_dir = BACKUP_DIR
    backup_file = None
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = _next_backup_path(backup_dir)

        source_connection = sqlite3.connect(source_db)
        destination_connection = sqlite3.connect(backup_file)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()

        if not _integrity_ok(backup_file):
            logger.error("Backup failed integrity check: %s", backup_file)
            backup_file.unlink(missing_ok=True)
            return False

        logger.info("Database backup created: %s", backup_file)

        # Sort by filename because the filename contains the creation
        # timestamp. Older copy-based backups preserved the source mtime, so
        # mtime is not a reliable ordering key.
        backup_files = sorted(
            glob.glob(os.path.join(backup_dir, "residents_backup_*.db")),
            key=os.path.basename,
        )
        for old_backup in backup_files[:-BACKUP_RETENTION]:
            os.remove(old_backup)
            logger.info("Removed old backup: %s", old_backup)
        return True
    except (OSError, sqlite3.Error) as error:
        logger.error("Backup failed: %s", error)
        if backup_file is not None:
            try:
                backup_file.unlink(missing_ok=True)
            except OSError:
                logger.error("Could not remove incomplete backup: %s", backup_file)
        return False


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully!")

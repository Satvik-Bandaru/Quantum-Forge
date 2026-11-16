"""Ordered transactional upgrades. Existing databases require explicit approval."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class MigrationRequired(RuntimeError):
    """The owner must approve upgrading an existing database."""


def _v1(db):
    for table in ('experiments', 'circuits', 'workspaces'):
        db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, document TEXT NOT NULL)')


def _v2(db):
    columns = {row[1] for row in db.execute('PRAGMA table_info(experiments)')}
    if 'summary' not in columns:
        db.execute('ALTER TABLE experiments ADD COLUMN summary TEXT')


MIGRATIONS = (_v1, _v2)


def migrate(path, *, allow_migration=False):
    """Back up committed SQLite state (including WAL), then atomically upgrade."""
    path = Path(path)
    with sqlite3.connect(path, timeout=10) as db:
        # Reserve the writer before inspection and backup so no concurrent writes
        # can fall between the saved snapshot and the schema upgrade.
        db.execute('BEGIN IMMEDIATE')
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        version = 0
        if 'meta' in tables:
            rows = db.execute('SELECT schema_version FROM meta').fetchall()
            if len(rows) != 1 or type(rows[0][0]) is not int or rows[0][0] < 1:
                raise RuntimeError('Invalid database schema version metadata.')
            version = rows[0][0]
        if version > len(MIGRATIONS):
            raise RuntimeError('Database schema is newer than this application supports.')
        if version == len(MIGRATIONS):
            return
        if tables and not allow_migration:
            raise MigrationRequired('Existing database upgrade requires owner approval. After approval, use Store(path, allow_migration=True); a backup is created before migration.')
        if tables:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = path.parent / f'backup-{stamp}-{uuid4().hex[:8]}.sqlite3'
            # SQLite backup on the same connection as BEGIN IMMEDIATE can block.
            # A separate reader sees committed WAL pages while this writer lock
            # prevents another connection from changing the source.
            with sqlite3.connect(path, timeout=10) as source, sqlite3.connect(backup) as destination:
                source.backup(destination)
        db.execute('CREATE TABLE IF NOT EXISTS meta (schema_version INTEGER NOT NULL)')
        if not version:
            db.execute('INSERT INTO meta VALUES (1)')
        for index in range(version, len(MIGRATIONS)):
            MIGRATIONS[index](db)
            db.execute('UPDATE meta SET schema_version=?', (index + 1,))

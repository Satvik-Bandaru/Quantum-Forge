"""Storage acceptance tests use generated fixtures, never the user's database."""
import json
import shutil
import sqlite3

import pytest

from backend.store import Store


def old_database(path):
    with sqlite3.connect(path) as db:
        for table in ('experiments', 'circuits', 'workspaces'):
            db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY, document TEXT NOT NULL)')
        db.execute('INSERT INTO experiments VALUES (?, ?)', ('old', json.dumps({'id': 'old', 'status': 'completed', 'result': {'kind': 'qubo', 'runtime_s': 3, 'solvers': [{'algorithm': 'QAOA', 'quality': .75}]}})))
        db.execute('INSERT INTO circuits VALUES (?, ?)', ('saved', '{"id":"saved"}'))
        db.execute('INSERT INTO workspaces VALUES (?, ?)', ('bench', '{"revision":3,"config":{}}'))


def test_existing_upgrade_requires_explicit_approval(tmp_path):
    path = tmp_path / 'old.sqlite3'
    old_database(path)
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match='allow_migration=True'):
        Store(path)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob('backup-*.sqlite3'))


def test_copied_old_fixture_migration_backup_and_idempotence(tmp_path):
    original = tmp_path / 'fixture.sqlite3'
    old_database(original)
    path = tmp_path / 'copy.sqlite3'
    shutil.copyfile(original, path)
    before = original.read_bytes()
    store = Store(path, allow_migration=True)
    assert store.get('old')['result']['runtime_s'] == 3
    assert store.circuits() == [{'id': 'saved'}]
    assert store.workspace('bench')['revision'] == 3
    assert store.history()[0]['summary']['best_quality'] == .75
    with store.connect() as db:
        assert db.execute('SELECT schema_version FROM meta').fetchall() == [(2,)]
        assert db.execute('SELECT summary FROM experiments').fetchone() == (None,)
    backups = list(tmp_path.glob('backup-*.sqlite3'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute('SELECT document FROM experiments').fetchone()
        assert 'meta' not in [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    Store(path)
    assert list(tmp_path.glob('backup-*.sqlite3')) == backups
    assert original.read_bytes() == before


def test_backup_includes_committed_wal_rows(tmp_path):
    path = tmp_path / 'wal.sqlite3'
    old_database(path)
    with sqlite3.connect(path) as writer:
        writer.execute('PRAGMA journal_mode=WAL')
        writer.execute('INSERT INTO circuits VALUES (?,?)', ('wal', '{"id":"wal"}'))
        writer.commit()
        Store(path, allow_migration=True)
        backup = next(tmp_path.glob('backup-*.sqlite3'))
        with sqlite3.connect(backup) as db:
            assert db.execute('SELECT document FROM circuits WHERE id="wal"').fetchone() == ('{"id":"wal"}',)


def test_future_schema_refused_without_changes(tmp_path):
    path = tmp_path / 'future.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE meta (schema_version INTEGER NOT NULL)')
        db.execute('INSERT INTO meta VALUES (999)')
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match='newer'):
        Store(path, allow_migration=True)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob('backup-*.sqlite3'))


def test_summary_updates_without_parsing_result_for_history(tmp_path):
    store = Store(tmp_path / 'new.sqlite3')
    result = {'kind': 'circuit', 'qubits': 2, 'depth': 2, 'runtime_s': .1,
              'probabilities': [.5, 0, 0, .5], 'amplitudes': [[.707, 0], [0, 0], [0, 0], [.707, 0]]}
    store.insert({'id': 'bell', 'status': 'running', 'result': result})
    store.update('bell', status='completed', title='updated')
    with store.connect() as db:
        cached = json.loads(db.execute('SELECT summary FROM experiments').fetchone()[0])
        assert 'result' not in cached
        assert cached['title'] == 'updated'
        # A malformed large document is a sentinel: history must read only its cache.
        db.execute("UPDATE experiments SET document='not JSON'")
    assert store.history() == [cached]
    assert cached['summary']['bell'] is True


@pytest.mark.parametrize('configured,cap', [('100', 100), ('2', 100), (None, 1000)])
def test_retention_prunes_only_oldest_beyond_cap(tmp_path, monkeypatch, configured, cap):
    if configured is None:
        monkeypatch.delenv('QF_MAX_SAVED_CIRCUITS', raising=False)
    else:
        monkeypatch.setenv('QF_MAX_SAVED_CIRCUITS', configured)
    store = Store(tmp_path / 'circuits.sqlite3')
    with store.connect() as db:
        db.executemany('INSERT INTO circuits VALUES (?,?)', [(str(i), json.dumps({'id': str(i)})) for i in range(cap)])
    Store(store.path)
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM circuits').fetchone()[0] == cap
    store.insert({'id': 'new'}, table='circuits')
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM circuits').fetchone()[0] == cap
        assert db.execute('SELECT id FROM circuits ORDER BY rowid LIMIT 1').fetchone() == ('1',)
        assert db.execute('SELECT id FROM circuits WHERE id="new"').fetchone() == ('new',)


def test_failed_upgrade_rolls_back_schema_and_keeps_backup(tmp_path, monkeypatch):
    import backend.migrations as migrations
    path = tmp_path / 'failure.sqlite3'
    old_database(path)
    def fail_after_schema_change(db):
        db.execute('ALTER TABLE experiments ADD COLUMN incomplete TEXT')
        raise RuntimeError('injected failure')
    monkeypatch.setattr(migrations, 'MIGRATIONS', (migrations._v1, fail_after_schema_change))
    with pytest.raises(RuntimeError, match='injected failure'):
        Store(path, allow_migration=True)
    with sqlite3.connect(path) as db:
        assert [r[1] for r in db.execute('PRAGMA table_info(experiments)')] == ['id', 'document']
        assert db.execute("SELECT name FROM sqlite_master WHERE name='meta'").fetchall() == []
        assert db.execute('SELECT COUNT(*) FROM experiments').fetchone() == (1,)
    assert len(list(tmp_path.glob('backup-*.sqlite3'))) == 1


def test_v1_upgrade_and_interrupted_run_refresh_summary(tmp_path):
    path = tmp_path / 'v1.sqlite3'
    old_database(path)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE meta (schema_version INTEGER NOT NULL)')
        db.execute('INSERT INTO meta VALUES (1)')
        db.execute('INSERT INTO experiments VALUES (?,?)', ('queued', '{"id":"queued","status":"queued","result":null}'))
    store = Store(path, allow_migration=True)
    assert store.get('queued')['status'] == 'interrupted'
    assert store.history()[0]['status'] == 'interrupted'
    with store.connect() as db:
        assert db.execute('SELECT schema_version FROM meta').fetchone() == (2,)
        assert json.loads(db.execute('SELECT summary FROM experiments WHERE id="queued"').fetchone()[0])['status'] == 'interrupted'


def test_existing_over_cap_is_pruned_only_on_successful_insert(tmp_path, monkeypatch):
    monkeypatch.setenv('QF_MAX_SAVED_CIRCUITS', '100')
    store = Store(tmp_path / 'overcap.sqlite3')
    with store.connect() as db:
        db.executemany('INSERT INTO circuits VALUES (?,?)', [(str(i), json.dumps({'id': str(i)})) for i in range(105)])
    Store(store.path)
    with pytest.raises(sqlite3.IntegrityError):
        store.insert({'id': '104'}, table='circuits')
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM circuits').fetchone() == (105,)
    store.insert({'id': 'new'}, table='circuits')
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM circuits').fetchone() == (100,)
        assert db.execute('SELECT id FROM circuits ORDER BY rowid LIMIT 1').fetchone() == ('6',)

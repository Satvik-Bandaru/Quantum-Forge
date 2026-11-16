import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from backend.migrations import migrate


def now():
    return datetime.now(timezone.utc).isoformat()

class RevisionConflict(ValueError):
    """A different browser saved this workspace after it was loaded."""

class Store:
    def __init__(self, path, *, allow_migration=False):
        self.path=Path(path)
        self.max_saved_circuits=max(100, int(os.getenv('QF_MAX_SAVED_CIRCUITS', '1000')))
        self.path.parent.mkdir(parents=True,exist_ok=True)
        migrate(self.path, allow_migration=allow_migration)
        for run in self.history(full=True):
            if run['status'] in ('running','queued'):
                self.update(run['id'],status='interrupted',error='The local service restarted before this run finished.',finished_at=now())

    def connect(self):
        return sqlite3.connect(self.path,timeout=10)

    def insert(self,document,table='experiments'):
        assert table in ('experiments','circuits')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            serialized=json.dumps(document,allow_nan=False)
            if table == 'experiments':
                db.execute('INSERT INTO experiments (id,document,summary) VALUES (?,?,?)',
                           (document['id'],serialized,json.dumps(history_document(document),allow_nan=False)))
            else:
                db.execute('INSERT INTO circuits (id,document) VALUES (?,?)',(document['id'],serialized))
                db.execute('DELETE FROM circuits WHERE rowid IN '
                           '(SELECT rowid FROM circuits ORDER BY rowid DESC LIMIT -1 OFFSET ?)',
                           (self.max_saved_circuits,))
        return document

    def get(self,run_id):
        with self.connect() as db:
            row=db.execute('SELECT document FROM experiments WHERE id=?',(run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def update(self,run_id,**changes):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT document FROM experiments WHERE id=?',(run_id,)).fetchone()
            if not row: raise KeyError(run_id)
            document=json.loads(row[0]);document.update(changes)
            db.execute('UPDATE experiments SET document=?, summary=? WHERE id=?',
                       (json.dumps(document,allow_nan=False),json.dumps(history_document(document),allow_nan=False),run_id))
        return document

    def history(self,full=False):
        with self.connect() as db:
            if full:
                rows=db.execute('SELECT document FROM experiments ORDER BY rowid DESC LIMIT 200').fetchall()
                return [json.loads(row[0]) for row in rows]
            # CASE prevents transferring the potentially large result for cached rows.
            rows=db.execute('SELECT summary, CASE WHEN summary IS NULL THEN document END '
                            'FROM experiments ORDER BY rowid DESC LIMIT 200').fetchall()
        return [json.loads(summary) if summary is not None else history_document(json.loads(document))
                for summary,document in rows]

    def save_circuit(self,circuit):
        return self.insert({'id':str(uuid4()),'created_at':now(),**circuit},'circuits')

    def circuits(self):
        with self.connect() as db:
            rows=db.execute('SELECT document FROM circuits ORDER BY rowid DESC LIMIT 100').fetchall()
        return [json.loads(row[0]) for row in rows]

    def workspace(self, workspace_id):
        with self.connect() as db:
            row = db.execute('SELECT document FROM workspaces WHERE id=?', (workspace_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_workspace(self, workspace_id, config, revision):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT document FROM workspaces WHERE id=?', (workspace_id,)).fetchone()
            previous = json.loads(row[0]) if row else None
            current_revision = previous['revision'] if previous else 0
            if revision != current_revision:
                raise RevisionConflict('The saved apparatus changed in another session. Reload it before saving again.')
            document = {'revision': revision + 1, 'config': config, 'updated_at': now()}
            db.execute('INSERT INTO workspaces VALUES (?,?) ON CONFLICT(id) DO UPDATE SET document=excluded.document',
                       (workspace_id, json.dumps(document, allow_nan=False)))
        return document


def history_document(document):
    """The list representation, retaining metadata without the full result."""
    document = dict(document)
    result = document.pop('result', None)
    document['summary'] = {k: result.get(k) for k in ('runtime_s', 'qubits', 'depth', 'exact_optimum')} if result else None
    if result:
        probabilities = result.get('probabilities', [])
        amplitudes = result.get('amplitudes', [])
        document['summary']['bell'] = bool(result.get('kind') == 'circuit' and result.get('qubits') == 2
            and len(probabilities) == 4 and len(amplitudes) == 4
            and abs(probabilities[0]-.5) < 1e-8 and abs(probabilities[3]-.5) < 1e-8
            and abs(amplitudes[0][0]-amplitudes[3][0]) < 1e-8
            and abs(amplitudes[0][1]-amplitudes[3][1]) < 1e-8)
        qualities = [s['quality'] for s in result.get('solvers', [])
                     if s['algorithm'] == 'QAOA' and s.get('quality') is not None]
        document['summary']['best_quality'] = max(qualities, default=None)
    return document

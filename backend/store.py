import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()

class Store:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS experiments (id TEXT PRIMARY KEY, document TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS circuits (id TEXT PRIMARY KEY, document TEXT NOT NULL)')
        for run in self.history(full=True):
            if run['status'] in ('running','queued'):
                self.update(run['id'],status='interrupted',error='The local service restarted before this run finished.',finished_at=now())

    def connect(self):
        return sqlite3.connect(self.path,timeout=10)

    def insert(self,document,table='experiments'):
        assert table in ('experiments','circuits')
        with self.connect() as db:
            db.execute(f'INSERT INTO {table} VALUES (?,?)',(document['id'],json.dumps(document,allow_nan=False)))
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
            db.execute('UPDATE experiments SET document=? WHERE id=?',(json.dumps(document,allow_nan=False),run_id))
        return document

    def history(self,full=False):
        with self.connect() as db:
            rows=db.execute('SELECT document FROM experiments ORDER BY rowid DESC LIMIT 200').fetchall()
        documents=[json.loads(row[0]) for row in rows]
        if not full:
            for document in documents:
                result=document.pop('result',None)
                document['summary']={k:result.get(k) for k in ('runtime_s','qubits','depth','exact_optimum')} if result else None
                if result:
                    probabilities=result.get('probabilities',[])
                    amplitudes=result.get('amplitudes',[])
                    document['summary']['bell']=bool(result['kind']=='circuit' and result['qubits']==2
                        and len(probabilities)==4 and abs(probabilities[0]-.5)<1e-8 and abs(probabilities[3]-.5)<1e-8
                        and abs(amplitudes[0][0]-amplitudes[3][0])<1e-8 and abs(amplitudes[0][1]-amplitudes[3][1])<1e-8)
                    qualities=[s['quality'] for s in result.get('solvers',[]) if s['algorithm']=='QAOA' and s.get('quality') is not None]
                    document['summary']['best_quality']=max(qualities,default=None)
        return documents

    def save_circuit(self,circuit):
        return self.insert({'id':str(uuid4()),'created_at':now(),**circuit},'circuits')

    def circuits(self):
        with self.connect() as db:
            rows=db.execute('SELECT document FROM circuits ORDER BY rowid DESC LIMIT 100').fetchall()
        return [json.loads(row[0]) for row in rows]

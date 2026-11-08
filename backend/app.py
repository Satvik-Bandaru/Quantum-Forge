import csv
import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import JSONResponse,Response,FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ValidationError,ConfigDict
from .models import CircuitRequest,OptimizationRequest,SavedCircuit,MAX_QUBITS,MAX_SHOTS
from .machine import MachineRequest
from .experiments import ExperimentRequest
from .physics import PhysicsRequest
from .photonics import PhotonicsRequest
from .qubo import QuboRequest
from .store import Store
from .jobs import JobManager,BusyError
from .http_limits import RequestBodyLimit

ROOT=Path(__file__).resolve().parents[1]

class JobRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind: Literal['circuit','optimization','machine','experiment','physics','photonics','qubo']
    config: dict=Field(default_factory=dict)


def create_app(db_path=None,timeout_s=None,memory_mb=None):
    timeout_s=timeout_s if timeout_s is not None else min(120,max(1,float(os.getenv('QF_TIMEOUT_SECONDS','45'))))
    memory_mb=memory_mb if memory_mb is not None else min(2048,max(128,int(os.getenv('QF_MEMORY_MB','1024'))))
    @asynccontextmanager
    async def lifespan(app):
        app.state.store=Store(db_path or ROOT/'data'/'experiments.sqlite3')
        app.state.jobs=JobManager(app.state.store,timeout_s,memory_mb)
        yield
        app.state.jobs.close()
    app=FastAPI(title='Quantum Forge Lab',version='0.4.0',lifespan=lifespan)
    app.add_middleware(RequestBodyLimit)

    @app.middleware('http')
    async def local_only(request:Request,call_next):
        host=request.url.hostname
        if host not in ('127.0.0.1','localhost','::1','testserver'):
            return JSONResponse({'detail':'Use the local loopback address.'},status_code=403)
        origin=request.headers.get('origin')
        if request.method in ('POST','PUT','PATCH','DELETE') and origin:
            parsed=urlparse(origin)
            if parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.scheme not in ('http','https'):
                return JSONResponse({'detail':'Only local browser origins may change experiments.'},status_code=403)
        return await call_next(request)

    @app.get('/api/health')
    def health():
        return {'app':'quantum-forge-lab','version':'0.4.0','status':'ready','execution':'local CPU simulation','limits':{'qubits':MAX_QUBITS,'shots':MAX_SHOTS,'timeout_s':timeout_s,'memory_mb':memory_mb,'concurrent_jobs':1,'machine_qubits':min(8,MAX_QUBITS),'machine_instructions':96,'qubo_variables':min(8,MAX_QUBITS)}}

    @app.post('/api/jobs',status_code=202)
    def start(body:JobRequest):
        try:
            config={'circuit':CircuitRequest,'optimization':OptimizationRequest,'machine':MachineRequest,'experiment':ExperimentRequest,'physics':PhysicsRequest,'photonics':PhotonicsRequest,'qubo':QuboRequest}[body.kind](**body.config)
        except ValidationError as exc:
            return JSONResponse({'detail':[{'loc':list(e['loc']),'msg':e['msg'],'type':e['type']} for e in exc.errors()]},status_code=422)
        if getattr(config,'shots',0)>MAX_SHOTS:
            raise HTTPException(422,f'The configured sample limit is {MAX_SHOTS}.')
        try: return app.state.jobs.start(body.kind,config.model_dump())
        except BusyError as exc: raise HTTPException(409,str(exc))

    @app.get('/api/jobs/{run_id}')
    @app.get('/api/history/{run_id}')
    def get_run(run_id:str):
        run=app.state.store.get(run_id)
        if not run: raise HTTPException(404,'Experiment not found.')
        return run

    @app.delete('/api/jobs/{run_id}')
    def cancel_run(run_id:str):
        run=app.state.jobs.cancel(run_id)
        if not run: raise HTTPException(404,'Experiment not found.')
        return run

    @app.get('/api/history')
    def history(): return app.state.store.history()

    @app.get('/api/circuits')
    def circuits(): return app.state.store.circuits()

    @app.post('/api/circuits',status_code=201)
    def save_circuit(body:SavedCircuit): return app.state.store.save_circuit(body.model_dump())

    @app.get('/api/history/{run_id}/export')
    def export(run_id:str,format:Literal['json','csv']='json'):
        run=get_run(run_id)
        if format=='json':
            return Response(json.dumps(run,indent=2,allow_nan=False),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="quantum-forge-{run_id}.json"'})
        result=run.get('result') or {}
        if result.get('kind')=='qubo':
            output=io.StringIO()
            fields=['id','kind','status','created_at','finished_at','key','algorithm','family','backend','energy','gap','expected_energy','expected_gap','solution','bitstring','runtime_s','initialization_s','evaluations','shots','seed','qubits','exact_energy','config','versions','limitations']
            writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader()
            for solver in result['solvers']:
                writer.writerow({'id':run['id'],'kind':run['kind'],'status':run['status'],
                    'created_at':run['created_at'],'finished_at':run['finished_at'],
                    'seed':run['config']['seed'],'qubits':result['qubits'],'exact_energy':result['exact_energy'],
                    **solver,'solution':json.dumps(solver['solution']),
                    'config':json.dumps(run['config']),'versions':json.dumps(result['versions']),
                    'limitations':json.dumps(result['limitations'])})
            return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="quantum-forge-qubo-{run_id}.csv"'})
        rows=result.get('solvers') or [{'algorithm':'Circuit simulation',**result}]
        if result.get('kind') in ('circuit','machine','experiment'):
            rows=[]
            for i,probability in enumerate(result['probabilities']):
                state=f"{i:0{result['qubits']}b}"
                real,imag=result['amplitudes'][i]
                rows.append({'algorithm':result.get('algorithm','Virtual computer' if run['kind']=='machine' else 'Circuit simulation'),'version':result['versions']['qiskit-aer'],
                    'backend':result['backend'],'runtime_s':result['runtime_s'],'qubits':result['qubits'],
                    'depth':result['depth'],'shots':result['shots'],'seed':result['seed'],
                    'state':state,'count':result['counts'].get(state,0),'ideal_probability':probability,
                    'amplitude_real':real,'amplitude_imag':imag})
        if result.get('kind') in ('physics','photonics'):
            output=io.StringIO()
            rows=result['series']
            fields=['id','kind','backend','seed','shots','runtime_s']+list(rows[0])+['config','versions','metrics','limitations']
            writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader()
            for row in rows:
                writer.writerow({'id':run['id'],'kind':run['kind'],'backend':result['backend'],
                    'seed':run['config']['seed'],'shots':result['shots'],'runtime_s':result['runtime_s'],**row,
                    'config':json.dumps(run['config']),'versions':json.dumps(result['versions']),
                    'metrics':json.dumps(result['metrics']),'limitations':json.dumps(result['limitations'])})
            return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="quantumlab-{run_id}.csv"'})
        output=io.StringIO()
        fields=['id','run_status','status','problem','algorithm','version','backend','objective','feasible','violations','quality','runtime_s','qubits','depth','shots','evaluations','seed','repetition','solution','state','count','ideal_probability','amplitude_real','amplitude_imag','config','versions','limitations']
        writer=csv.DictWriter(output,fieldnames=fields,extrasaction='ignore');writer.writeheader()
        for row in rows:
            writer.writerow({'id':run['id'],'run_status':run['status'],'status':run['status'],'problem':result.get('problem'),'seed':run['config']['seed'],'repetition':1,**{k:v for k,v in row.items() if k not in ('config','versions','limitations')},
                             'config':json.dumps(run['config']),'versions':json.dumps(result.get('versions',{})),'limitations':json.dumps(result.get('limitations',[]))})
        return Response(output.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="quantum-forge-{run_id}.csv"'})

    dist=ROOT/'frontend'/'dist'
    if dist.exists():
        app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
        @app.get('/')
        def index(): return FileResponse(dist/'index.html')
    return app

app=create_app()

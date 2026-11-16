"""One spawned compute worker at a time, with hard termination and parent-owned persistence."""
import logging
import multiprocessing as mp
import os
import threading
import time
import psutil
import resource
import sys
from uuid import uuid4
from .store import now

class BusyError(Exception): pass


def compute(send,kind,payload):
    started = time.perf_counter()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
        os.environ[key]='1'
    try:
        send.send(('progress','Loading scientific simulator'))
        from .models import CircuitRequest,OptimizationRequest
        from .science import run_circuit,run_optimization
        from .machine import MachineRequest,run_machine
        from .experiments import ExperimentRequest,run_experiment
        from .physics import PhysicsRequest,run_physics
        from .photonics import PhotonicsRequest,run_photonics
        from .qubo import QuboRequest,run_qubo
        from .connected import ConnectedRequest,run_connected
        from .research import ResearchRequest,run_research
        messages={'qubo':'Mapping QUBO to Ising and comparing five executed solvers','physics':'Propagating the driven Lindblad system and sampling independent readouts','photonics':'Calculating coherent optical fields, phase sweep and power-meter readouts','circuit':'Executing circuit','optimization':'Solving baseline, QAOA and annealing','machine':'Executing program and inspecting register states','experiment':'Running quantum experiment and independent reference checks'}
        messages['connected'] = 'Validating instrument connections and propagating the thermal pulse sequence'
        messages['research'] = 'Executing the bounded quantum channel and independent reference checks'
        send.send(('progress',messages[kind]))
        schema,runner={'circuit':(CircuitRequest,run_circuit),'optimization':(OptimizationRequest,run_optimization),'machine':(MachineRequest,run_machine),'experiment':(ExperimentRequest,run_experiment),'physics':(PhysicsRequest,run_physics),'photonics':(PhotonicsRequest,run_photonics),'qubo':(QuboRequest,run_qubo),'connected':(ConnectedRequest,run_connected),'research':(ResearchRequest,run_research)}[kind]
        result=runner(schema(**payload))
        high_water = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['resources'] = {
            'worker_wall_s': time.perf_counter() - started,
            'peak_rss_bytes': int(high_water if sys.platform == 'darwin' else high_water * 1024),
            'execution': 'local_cpu',
            'scope': 'Worker process high-water resident memory; includes scientific library imports. Wall time starts at worker entry.',
        }
        send.send(('result',result))
    except Exception as exc:
        send.send(('error',f'{type(exc).__name__}: {exc}'))
    finally:
        send.close()

class JobManager:
    def __init__(self,store,timeout_s=45,memory_mb=1024):
        self.store=store; self.timeout_s=timeout_s
        self.memory_mb=memory_mb
        self.lock=threading.RLock();self.active=None;self.closed=False
        self.thread=threading.Thread(target=self.monitor,daemon=True)
        self.thread.start()

    def start(self,kind,payload):
        with self.lock:
            if self.closed: raise BusyError('The job manager is closed.')
            if self.active: raise BusyError('A simulation is already running. Wait or cancel it before starting another.')
            document={'id':str(uuid4()),'kind':kind,'config':payload,'status':'running','created_at':now(),'finished_at':None,
                      'progress':'Starting isolated CPU worker','result':None,'error':None}
            self.store.insert(document)
            receive,send=mp.get_context('spawn').Pipe(duplex=False)
            process=mp.get_context('spawn').Process(target=compute,args=(send,kind,payload),daemon=True)
            try:
                process.start()
            except Exception as exc:
                receive.close();send.close()
                self.store.update(document['id'],status='failed',error=str(exc),finished_at=now())
                raise
            send.close()
            self.active={'id':document['id'],'process':process,'pipe':receive,'started':time.monotonic()}
            return document

    def finish(self,status,*,job=None,**changes):
        # Reserve the slot through cleanup and persistence. Only one caller owns
        # termination, while competing cancellation requests can return promptly.
        with self.lock:
            if job is None:
                job=self.active
            if job is None or self.active is not job or job.get('finishing'):
                return
            # Keep the original decision/result across cleanup or database retries.
            if 'terminal' not in job:
                job['terminal']=(status,dict(finished_at=now(),**changes))
            status,changes=job['terminal']
            job['finishing']=True
        try:
            process=job['process']
            if process.is_alive(): process.terminate()
            process.join(timeout=2)
            if process.is_alive(): process.kill();process.join(timeout=1)
            if process.is_alive():
                # A kill request is not proof of exit; retain ownership and retry.
                return
            job['pipe'].close()
            with self.lock:
                self.store.update(job['id'],status=status,**changes)
                if self.active is job:
                    self.active=None
        except Exception as exc:
            # A transient OS/SQLite failure must not kill the monitor or poison
            # the slot. Retain the terminal payload and retry on its next pass.
            message=f'{type(exc).__name__}: {exc}'
            if job.get('finish_error')!=message:
                logging.getLogger(__name__).warning('Job %s finalization will retry: %s',job['id'],message)
            job['finish_error']=message
        finally:
            with self.lock:
                job['finishing']=False

    def monitor(self):
        while True:
            outcome=None
            with self.lock:
                job=self.active
                if self.closed and job is None:
                    return
                if job and not job.get('finishing'):
                    try:
                        if 'terminal' in job:
                            outcome=job['terminal']
                        elif self.closed:
                            outcome=('interrupted',dict(error='Local service stopped.'))
                        elif time.monotonic()-job['started']>self.timeout_s:
                            outcome=('timed_out',dict(error=f'Run exceeded the {self.timeout_s:g}-second time limit. Reduce circuit size, layers or repetitions.'))
                        elif job['pipe'].poll():
                            tag,value=job['pipe'].recv()
                            if tag=='progress': self.store.update(job['id'],progress=value)
                            elif tag=='result': outcome=('completed',dict(result=value,progress='Complete'))
                            else: outcome=('failed',dict(error=value))
                        elif not job['process'].is_alive():
                            # Exit may have happened just after the first empty poll.
                            # A dead sender cannot enqueue anything after this recheck.
                            if job['pipe'].poll():
                                continue
                            outcome=('failed',dict(error='Compute worker exited without a result.'))
                        else:
                            try:
                                resident=psutil.Process(job['process'].pid).memory_info().rss
                            except psutil.NoSuchProcess:
                                # Drain a result sent just before the worker exited.
                                continue
                            if resident>self.memory_mb*1024**2:
                                outcome=('memory_limited',dict(error=f'Worker exceeded the {self.memory_mb:g} MiB memory budget. Reduce the problem size.'))
                    except (EOFError,OSError,psutil.Error) as exc:
                        outcome=('failed',dict(error=f'Compute worker disconnected: {exc}'))
            if outcome:
                status,changes=outcome
                self.finish(status,job=job,**changes)
            time.sleep(0.05)

    def cancel(self,job_id):
        with self.lock:
            job=self.active
            if not job or job['id']!=job_id:
                job=None
        if job:
            self.finish('cancelled',job=job,progress='Cancelled by user')
        return self.store.get(job_id)

    def close(self):
        with self.lock:
            self.closed=True
            job=self.active
        if job:
            self.finish('interrupted',job=job,error='Local service stopped.')
        self.thread.join(timeout=3)

"""One spawned compute worker at a time, with hard termination and parent-owned persistence."""
import multiprocessing as mp
import os
import threading
import time
import psutil
from uuid import uuid4
from .store import now

class BusyError(Exception): pass


def compute(send,kind,payload):
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
        messages={'qubo':'Mapping QUBO to Ising and comparing five executed solvers','physics':'Propagating the driven Lindblad system and sampling independent readouts','photonics':'Calculating coherent optical fields, phase sweep and power-meter readouts','circuit':'Executing circuit','optimization':'Solving baseline, QAOA and annealing','machine':'Executing program and inspecting register states','experiment':'Running quantum experiment and independent reference checks'}
        send.send(('progress',messages[kind]))
        schema,runner={'circuit':(CircuitRequest,run_circuit),'optimization':(OptimizationRequest,run_optimization),'machine':(MachineRequest,run_machine),'experiment':(ExperimentRequest,run_experiment),'physics':(PhysicsRequest,run_physics),'photonics':(PhotonicsRequest,run_photonics),'qubo':(QuboRequest,run_qubo)}[kind]
        result=runner(schema(**payload))
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

    def finish(self,status,**changes):
        job=self.active
        process=job['process']
        if process.is_alive(): process.terminate()
        process.join(timeout=2)
        if process.is_alive(): process.kill();process.join(timeout=1)
        job['pipe'].close()
        self.store.update(job['id'],status=status,finished_at=now(),**changes)
        self.active=None

    def monitor(self):
        while not self.closed:
            with self.lock:
                job=self.active
                if job:
                    try:
                        if time.monotonic()-job['started']>self.timeout_s:
                            self.finish('timed_out',error=f'Run exceeded the {self.timeout_s:g}-second time limit. Reduce circuit size, layers or repetitions.')
                        elif job['pipe'].poll():
                            tag,value=job['pipe'].recv()
                            if tag=='progress': self.store.update(job['id'],progress=value)
                            elif tag=='result': self.finish('completed',result=value,progress='Complete')
                            else: self.finish('failed',error=value)
                        elif not job['process'].is_alive():
                            # Exit may have happened just after the first empty poll.
                            # A dead sender cannot enqueue anything after this recheck.
                            if job['pipe'].poll():
                                continue
                            self.finish('failed',error='Compute worker exited without a result.')
                        else:
                            try:
                                resident=psutil.Process(job['process'].pid).memory_info().rss
                            except psutil.NoSuchProcess:
                                # The worker may have sent its result and exited between
                                # is_alive() and this lookup. Drain its pipe next pass.
                                continue
                            if resident>self.memory_mb*1024**2:
                                self.finish('memory_limited',error=f'Worker exceeded the {self.memory_mb:g} MiB memory budget. Reduce the problem size.')
                    except (EOFError,OSError,psutil.Error) as exc:
                        if self.active: self.finish('failed',error=f'Compute worker disconnected: {exc}')
            time.sleep(0.05)

    def cancel(self,job_id):
        with self.lock:
            if self.active and self.active['id']==job_id:
                self.finish('cancelled',progress='Cancelled by user')
            return self.store.get(job_id)

    def close(self):
        with self.lock:
            self.closed=True
            if self.active: self.finish('interrupted',error='Local service stopped.')
        self.thread.join(timeout=3)

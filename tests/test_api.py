import time
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'test.sqlite3')) as client:
        yield client


def wait_for(client,job_id):
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        data=client.get('/api/jobs/'+job_id).json()
        if data['status'] not in ('running','queued'):
            return data
        time.sleep(0.1)
    pytest.fail('Job did not finish in 40 seconds')


def test_run_persists_and_exports_actual_results(client):
    started=client.post('/api/jobs',json={'kind':'circuit','config':{'qubits':1,'gates':[{'name':'X','target':0}]}})
    assert started.status_code==202
    data=wait_for(client,started.json()['id'])
    assert data['status']=='completed',data
    assert data['result']['counts']=={'1':1024}
    history=client.get('/api/history').json()
    assert len(history)==1
    loaded=client.get('/api/history/'+data['id']).json()
    assert loaded['config']['gates'][0]['name']=='X'
    assert client.get('/api/history/'+data['id']+'/export?format=json').json()['result']['counts']=={'1':1024}
    csv=client.get('/api/history/'+data['id']+'/export?format=csv')
    assert csv.status_code==200
    assert 'runtime_s' in csv.text


def test_api_validates_input_and_circuit_save_load(client):
    assert client.post('/api/jobs',json={'kind':'circuit','config':{'qubits':100}}).status_code==422
    saved=client.post('/api/circuits',json={'name':'Bell','config':{'qubits':2,'gates':[{'name':'H','target':0},{'name':'CNOT','control':0,'target':1}]}})
    assert saved.status_code==201
    assert client.get('/api/circuits').json()[0]['name']=='Bell'
    assert client.post('/api/circuits',json={'name':'Broken','config':{'qubits':100}}).status_code==422
    assert client.get('/api/history/missing').status_code==404


def test_single_job_limit_and_cancel_are_persisted(client):
    first=client.post('/api/jobs',json={'kind':'optimization','config':{'iterations':150,'repetitions':3}}).json()
    assert client.post('/api/jobs',json={'kind':'circuit','config':{}}).status_code==409
    cancelled=client.delete('/api/jobs/'+first['id'])
    assert cancelled.status_code==200
    assert cancelled.json()['status']=='cancelled'
    assert client.get('/api/history/'+first['id']).json()['status']=='cancelled'
    second=client.post('/api/jobs',json={'kind':'circuit','config':{}})
    assert second.status_code==202
    client.delete('/api/jobs/'+second.json()['id'])


def test_timeout_terminates_worker_and_releases_slot(tmp_path):
    with TestClient(create_app(tmp_path/'timeout.sqlite3',timeout_s=0.01)) as client:
        job=client.post('/api/jobs',json={'kind':'optimization','config':{}}).json()
        result=wait_for(client,job['id'])
        assert result['status']=='timed_out'
        assert client.post('/api/jobs',json={'kind':'circuit','config':{}}).status_code==202


def test_reopen_database_preserves_results_and_circuits(tmp_path):
    path=tmp_path/'persist.sqlite3'
    with TestClient(create_app(path)) as client:
        client.post('/api/circuits',json={'name':'Saved','config':{'qubits':1}})
    with TestClient(create_app(path)) as client:
        assert client.get('/api/circuits').json()[0]['name']=='Saved'


def test_nonlocal_origin_cannot_submit_jobs(client):
    assert client.post('/api/jobs',json={'kind':'circuit','config':{}},headers={'origin':'https://untrusted.example'}).status_code==403


def test_challenge_scoring_requires_actual_bell_state(client):
    for gates in ([{'name':'H','target':0},{'name':'CNOT','target':1,'control':0}], [{'name':'H','target':0}]):
        job=client.post('/api/jobs',json={'kind':'circuit','config':{'qubits':2,'gates':gates}}).json()
        assert wait_for(client,job['id'])['status']=='completed'
    history=client.get('/api/history').json()
    assert history[0]['summary']['bell'] is False
    assert history[1]['summary']['bell'] is True


def test_memory_limit_terminates_worker(tmp_path):
    with TestClient(create_app(tmp_path/'memory.sqlite3',memory_mb=1)) as client:
        job=client.post('/api/jobs',json={'kind':'optimization','config':{}}).json()
        result=wait_for(client,job['id'])
        assert result['status']=='memory_limited'


def test_unexpected_worker_exit_releases_slot(client):
    job=client.post('/api/jobs',json={'kind':'optimization','config':{}}).json()
    manager=client.app.state.jobs
    with manager.lock:
        manager.active['process'].kill()
        manager.active['process'].join(timeout=2)
    assert wait_for(client,job['id'])['status']=='failed'
    another=client.post('/api/jobs',json={'kind':'circuit','config':{}})
    assert another.status_code==202
    client.delete('/api/jobs/'+another.json()['id'])


def test_circuit_csv_contains_measurement_distribution(client):
    job=client.post('/api/jobs',json={'kind':'circuit','config':{'qubits':1,'gates':[{'name':'X','target':0}]}}).json()
    wait_for(client,job['id'])
    import csv,io
    rows=list(csv.DictReader(io.StringIO(client.get('/api/history/'+job['id']+'/export?format=csv').text)))
    measured=next(row for row in rows if row['state']=='1')
    assert measured['count']=='1024'
    assert float(measured['ideal_probability'])==1
    assert measured['seed']=='42'


def test_virtual_computer_run_history_and_export(client):
    job=client.post('/api/jobs',json={'kind':'machine','config':{'qubits':2,'program':'H q0\nCX q0,q1'}})
    assert job.status_code==202
    result=wait_for(client,job.json()['id'])
    assert result['status']=='completed',result
    assert len(result['result']['snapshots'])==3
    assert client.get('/api/history/'+result['id']).json()['config']['program']=='H q0\nCX q0,q1'
    csv=client.get('/api/history/'+result['id']+'/export?format=csv')
    assert 'ideal_probability' in csv.text
    assert '0.5' in csv.text or '0.4999' in csv.text


def test_general_experiment_job_and_invalid_program_validation(client):
    assert client.post('/api/jobs',json={'kind':'machine','config':{'qubits':2,'program':'CX q0,q0'}}).status_code==422
    job=client.post('/api/jobs',json={'kind':'experiment','config':{'algorithm':'superdense','message':'11'}})
    assert job.status_code==202
    result=wait_for(client,job.json()['id'])
    assert result['status']=='completed',result
    assert result['result']['metrics']['decoded_message']=='11'


def test_physical_lab_rabi_job_and_time_series_export(client):
    job=client.post('/api/jobs',json={'kind':'physics','config':{'drive_mhz':1,'duration_us':.5,'t1_us':None,'tphi_us':None,'points':101}})
    assert job.status_code==202
    record=wait_for(client,job.json()['id'])
    assert record['status']=='completed',record
    assert record['result']['series'][-1]['noisy_p1']==pytest.approx(1,abs=1e-7)
    restored=client.get('/api/history/'+record['id']).json()
    assert restored['kind']=='physics'
    assert restored['config']['duration_us']==.5
    csv=client.get('/api/history/'+record['id']+'/export?format=csv')
    assert 'time_us' in csv.text and 'noisy_p1' in csv.text


def test_photonics_job_phase_power_and_validation(client):
    missing=client.post('/api/jobs',json={'kind':'photonics','config':{'bench_components':['source']}})
    assert missing.status_code==422
    job=client.post('/api/jobs',json={'kind':'photonics','config':{'phase_rad':0,'power_mw':1}})
    assert job.status_code==202
    record=wait_for(client,job.json()['id'])
    assert record['status']=='completed',record
    assert record['result']['metrics']['port0_mw']==pytest.approx(0,abs=1e-8)
    assert record['result']['metrics']['port1_mw']==pytest.approx(1,abs=1e-8)
    assert 'phase_rad' in client.get('/api/history/'+record['id']+'/export?format=csv').text


def test_worker_process_lookup_race_does_not_discard_result(client,monkeypatch):
    from backend import jobs
    real_process=jobs.psutil.Process
    interrupted=[False]
    def transient_lookup(pid):
        if not interrupted[0]:
            interrupted[0]=True
            raise jobs.psutil.NoSuchProcess(pid)
        return real_process(pid)
    monkeypatch.setattr(jobs.psutil,'Process',transient_lookup)
    job=client.post('/api/jobs',json={'kind':'photonics','config':{}}).json()
    result=wait_for(client,job['id'])
    assert result['status']=='completed',result
    assert interrupted[0]
    assert result['result']['metrics']['port1_mw']==pytest.approx(1)


def test_worker_exit_after_empty_poll_rechecks_queued_evidence(client):
    job=client.post('/api/jobs',json={'kind':'circuit','config':{'qubits':1}}).json()
    manager=client.app.state.jobs
    with manager.lock:
        active=manager.active
        assert active is not None
        active['process'].join(timeout=10)
        assert not active['process'].is_alive()
        original=active['pipe']
        class LateReadablePipe:
            first=True
            def poll(self):
                if self.first:
                    self.first=False
                    return False
                return original.poll()
            def recv(self): return original.recv()
            def close(self): return original.close()
        active['pipe']=LateReadablePipe()
    record=wait_for(client,job['id'])
    assert record['status']=='completed',record
    assert record['result']['counts']=={'0':1024}

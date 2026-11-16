"""Physical workflow API regressions with isolated stores and actual workers."""
import csv
import importlib
import io
import json
import time

import pytest

from fastapi.testclient import TestClient

from backend.app import create_app


def wait_run(client, run_id):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        run = client.get('/api/jobs/' + run_id).json()
        if run['status'] not in ('running', 'queued'):
            return run
        time.sleep(.04)
    raise AssertionError('Connected job did not finish within test deadline')


def test_numerical_inspection_failure_is_reported_without_saving(tmp_path, monkeypatch):
    module = importlib.import_module('backend.app')
    with TestClient(create_app(tmp_path / 'numerical.sqlite3')) as client:
        before = client.get('/api/apparatus').json()

        def fail(_):
            raise ArithmeticError('Thermal solver failed its energy check')

        with monkeypatch.context() as patch:
            patch.setattr(module, 'apparatus_status', fail)
            response = client.post('/api/apparatus/inspect', json=before['config'])
            assert response.status_code == 422
            assert 'energy check' in response.json()['detail']
            response = client.put('/api/apparatus', json={'revision': 0, 'config': before['config']})
            assert response.status_code == 422
        assert client.get('/api/apparatus').json() == before
        assert client.get('/api/history').json() == []


def test_connected_csv_preserves_physical_model_and_validation_evidence(tmp_path):
    with TestClient(create_app(tmp_path / 'export.sqlite3')) as client:
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': {'points': 51}})
        assert response.status_code == 202, response.text
        run = wait_run(client, response.json()['id'])
        assert run['status'] == 'completed', run
        exported = client.get('/api/history/' + run['id'] + '/export?format=csv')
        rows = list(csv.DictReader(io.StringIO(exported.text)))
        assert json.loads(rows[0]['model']) == run['result']['model']
        assert json.loads(rows[0]['checks']) == run['result']['checks']
        assert json.loads(rows[0]['apparatus_status']) == run['result']['apparatus_status']


def test_connected_timeout_releases_worker_and_preserves_failure(tmp_path):
    with TestClient(create_app(tmp_path / 'timeout.sqlite3', timeout_s=.01)) as client:
        job = client.post('/api/jobs', json={'kind': 'connected', 'config': {}})
        assert job.status_code == 202
        run = wait_run(client, job.json()['id'])
        assert run['status'] == 'timed_out'
        assert run['result'] is None
        assert client.get('/api/history/' + run['id']).json() == run
        second = client.post('/api/jobs', json={'kind': 'connected', 'config': {}})
        assert second.status_code == 202
        client.delete('/api/jobs/' + second.json()['id'])


def test_worker_reports_numerical_failure_without_fabricated_result(monkeypatch):
    from backend import connected, jobs

    def fail(_):
        raise ArithmeticError('Density matrix physicality check failed')

    class CapturePipe:
        def __init__(self):
            self.messages = []
            self.closed = False

        def send(self, message):
            self.messages.append(message)

        def close(self):
            self.closed = True

    monkeypatch.setattr(connected, 'run_connected', fail)
    pipe = CapturePipe()
    jobs.compute(pipe, 'connected', {})
    assert pipe.closed
    assert pipe.messages[-1] == ('error', 'ArithmeticError: Density matrix physicality check failed')
    assert not any(kind == 'result' for kind, _ in pipe.messages)


def test_thermal_network_run_persists_and_replays_exact_samples(tmp_path):
    database = tmp_path / 'thermal-replay.sqlite3'
    with TestClient(create_app(database)) as client:
        inspected = client.post('/api/apparatus/inspect', json={'cryostat': {'thermal_model': 'thermal_network'}})
        assert inspected.status_code == 200, inspected.text
        status = inspected.json()
        assert status['ready'], status['issues']
        request = {'apparatus': {'cryostat': {'thermal_model': 'thermal_network'}},
                   'points': 51, 'sweep_stop': .1, 'seed': 23}
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': request})
        assert response.status_code == 202, response.text
        run = wait_run(client, response.json()['id'])
        assert run['status'] == 'completed', run
        thermal = run['result']['apparatus_status']['thermal']
        assert thermal['model'] == 'thermal-network-1'
        assert all(check['passed'] for check in thermal['checks'])
        assert run['result']['apparatus_status']['derived']['temperature_k'] == pytest.approx(status['derived']['temperature_k'])
    with TestClient(create_app(database)) as client:
        restored = client.get('/api/history/' + run['id']).json()
        assert restored == run
        replay = client.post('/api/jobs', json={'kind': 'connected', 'config': restored['config']})
        assert replay.status_code == 202, replay.text
        repeated = wait_run(client, replay.json()['id'])
        assert repeated['status'] == 'completed', repeated
        assert repeated['id'] != restored['id']
        assert repeated['result']['series'] == restored['result']['series']
        assert repeated['result']['apparatus_status'] == restored['result']['apparatus_status']
        assert client.get('/api/history/' + restored['id']).json() == restored


@pytest.mark.parametrize('sequence', ['amplitude_calibration', 'dephasing'])
def test_new_protocols_execute_and_export_full_saved_evidence(tmp_path, sequence):
    with TestClient(create_app(tmp_path / 'protocol.sqlite3')) as client:
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': {
            'sequence': sequence, 'sweep_stop': 2 if sequence == 'amplitude_calibration' else 100,
            'shots': 8192, 'seed': 23,
        }})
        assert response.status_code == 202, response.text
        run = wait_run(client, response.json()['id'])
        assert run['status'] == 'completed', run
        assert run['result']['sequence'] == sequence
        assert all(check['passed'] for check in run['result']['checks'])
        assert client.get('/api/history/' + run['id'] + '/export?format=json').json() == run


def test_legacy_apparatus_without_thermal_extensions_still_runs(tmp_path):
    from backend.instruments import ApparatusConfig
    config = ApparatusConfig().model_dump()
    config['cryostat'].pop('thermal_model', None)
    config['cryostat'].pop('network', None)
    with TestClient(create_app(tmp_path / 'legacy.sqlite3')) as client:
        inspected = client.post('/api/apparatus/inspect', json=config)
        assert inspected.status_code == 200
        # Exact historical exponential temperature, not a silently substituted network.
        import math
        assert inspected.json()['derived']['temperature_k'] == pytest.approx(.02 + 3.98 * math.exp(-10), abs=1e-14)
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': {'apparatus': config, 'points': 51}})
        assert response.status_code == 202
        run = wait_run(client, response.json()['id'])
        assert run['status'] == 'completed', run

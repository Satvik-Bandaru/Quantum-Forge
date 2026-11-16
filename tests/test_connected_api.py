"""Connected instrument API: persistence, boundaries, real workers and provenance."""
import csv
import io
import time

from fastapi.testclient import TestClient

from backend.app import create_app


def wait_run(client, run_id):
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        run = client.get('/api/jobs/' + run_id).json()
        if run['status'] != 'running':
            return run
        time.sleep(0.04)
    raise AssertionError('Connected worker failed to finish within bounded test time')


def test_apparatus_persists_across_restart_and_rejects_stale_revision(tmp_path):
    database = tmp_path / 'apparatus.sqlite3'
    with TestClient(create_app(database, testing=True)) as client:
        initial = client.get('/api/apparatus')
        assert initial.status_code == 200
        state = initial.json()
        assert state['revision'] == 0 and state['status']['ready']
        config = state['config']
        config['cryostat']['elapsed_s'] = 0
        inspected = client.post('/api/apparatus/inspect', json=config)
        assert inspected.status_code == 200
        assert not inspected.json()['ready']
        saved = client.put('/api/apparatus', json={'revision': 0, 'config': config})
        assert saved.status_code == 200
        assert saved.json()['revision'] == 1
        assert saved.json()['updated_at']
        assert client.put('/api/apparatus', json={'revision': 0, 'config': config}).status_code == 409
    with TestClient(create_app(database, testing=True)) as client:
        saved = client.get('/api/apparatus').json()
        assert saved['revision'] == 1
        assert saved['config']['cryostat']['elapsed_s'] == 0
        assert not saved['status']['ready']


def test_invalid_connections_and_unrunnable_bench_do_not_start_worker(tmp_path):
    with TestClient(create_app(tmp_path / 'validation.sqlite3', testing=True)) as client:
        response = client.get('/api/apparatus')
        assert response.status_code == 200
        config = response.json()['config']
        broken = {**config, 'connections': [{'source': 'microwave:rf', 'target': 'cryostat:thermal'}]}
        assert client.post('/api/apparatus/inspect', json=broken).status_code == 422
        assert client.put('/api/apparatus', json={'revision': 0, 'config': broken}).status_code == 422
        config['connections'] = []
        assert not client.post('/api/apparatus/inspect', json=config).json()['ready']
        blocked = client.post('/api/jobs', json={'kind': 'connected', 'config': {'apparatus': config}})
        assert blocked.status_code == 422
        assert client.get('/api/history').json() == []


def test_real_connected_job_saved_exported_and_resource_metered(tmp_path):
    with TestClient(create_app(tmp_path / 'runs.sqlite3', testing=True)) as client:
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': {
            'sequence': 'ramsey', 'sweep_stop': 0.5, 'points': 51, 'shots': 256, 'seed': 17,
        }})
        assert response.status_code == 202, response.text
        submitted = response.json()
        run = wait_run(client, submitted['id'])
        assert run['status'] == 'completed', run
        result = run['result']
        assert result['kind'] == 'connected'
        assert len(result['series']) == 51
        assert result['shots'] == 256 and result['seed'] == 17
        assert result['resources']['worker_wall_s'] > 0
        assert result['resources']['peak_rss_bytes'] > 0
        assert result['resources']['execution'] == 'local_cpu'
        assert run['config']['apparatus']['microwave']['frequency_ghz'] == 5
        restored = client.get('/api/history/' + run['id']).json()
        assert restored == run
        exported = client.get('/api/history/' + run['id'] + '/export?format=csv')
        assert exported.status_code == 200
        rows = list(csv.DictReader(io.StringIO(exported.text)))
        assert len(rows) == 51
        assert float(rows[0]['probability']) == result['series'][0]['probability']
        assert 'apparatus' in rows[0]['config']
        assert 'peak_rss_bytes' in rows[0]['resources']
        assert client.get('/api/history').json()[0]['kind'] == 'connected'


def test_connected_job_cancellation_uses_existing_worker_lifecycle(tmp_path):
    with TestClient(create_app(tmp_path / 'cancel.sqlite3', testing=True)) as client:
        response = client.post('/api/jobs', json={'kind': 'connected', 'config': {}})
        assert response.status_code == 202
        run_id = response.json()['id']
        run = client.delete('/api/jobs/' + run_id).json()
        assert run['status'] == 'cancelled'
        assert run['result'] is None


def test_compute_policy_is_explicitly_local_and_noncommercial(tmp_path):
    with TestClient(create_app(tmp_path / 'policy.sqlite3', testing=True)) as client:
        response = client.get('/api/compute/policy')
        assert response.status_code == 200
        policy = response.json()
        assert policy['accounts_enabled'] is False
        assert policy['payments_enabled'] is False
        assert policy['remote']['enabled'] is False
        assert {tier['id'] for tier in policy['tiers']} == {'local_educational', 'local_advanced'}
        assert all(tier['price'] == 0 and tier['concurrent_jobs'] == 1 for tier in policy['tiers'])


def test_apparatus_rejects_invalid_revision_and_nonfinite_controls(tmp_path):
    with TestClient(create_app(tmp_path / 'invalid.sqlite3', testing=True)) as client:
        assert client.put('/api/apparatus', json={'revision': -1, 'config': {}}).status_code == 422
        assert client.post('/api/apparatus/inspect', json={'cryostat': {'elapsed_s': 'NaN'}}).status_code == 422
        assert client.post('/api/jobs', json={'kind': 'connected', 'config': {'shots': 8193}}).status_code == 422

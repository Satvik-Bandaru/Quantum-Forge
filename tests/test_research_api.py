"""The bounded research protocols use real workers, history and export."""
import csv
import io
import time
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


@pytest.mark.parametrize('experiment', ['repetition_code', 'single_photon_mzi'])
def test_research_run_persists_physical_results_and_exports(tmp_path, experiment):
    with TestClient(create_app(tmp_path / (experiment + '.sqlite3'))) as client:
        response = client.post('/api/jobs', json={'kind': 'research', 'config': {
            'experiment': experiment, 'shots': 256, 'seed': 29,
        }})
        assert response.status_code == 202, response.text
        run_id = response.json()['id']
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            run = client.get('/api/jobs/' + run_id).json()
            if run['status'] != 'running': break
            time.sleep(.04)
        assert run['status'] == 'completed', run
        result = run['result']
        assert result['experiment'] == experiment
        assert sum(result['counts'].values()) == 256
        assert sum(result['probabilities'].values()) == pytest.approx(1, abs=1e-12)
        assert result['resources']['peak_rss_bytes'] > 0
        assert client.get('/api/history/' + run_id).json() == run
        response = client.get('/api/history/' + run_id + '/export?format=csv')
        assert response.status_code == 200
        rows = list(csv.DictReader(io.StringIO(response.text)))
        assert sum(int(row['count']) for row in rows) == 256
        assert {row['outcome'] for row in rows} == set(result['counts'])
        assert all('peak_rss_bytes' in row['resources'] for row in rows)


def test_unphysical_research_input_never_enters_history(tmp_path):
    with TestClient(create_app(tmp_path / 'reject.sqlite3')) as client:
        for config in ({'bit_flip_probability': 1.1}, {'detector0_efficiency': -1}, {'shots': 8193}, {'path_coherence': 'NaN'}):
            response = client.post('/api/jobs', json={'kind': 'research', 'config': config})
            assert response.status_code == 422
        assert client.get('/api/history').json() == []

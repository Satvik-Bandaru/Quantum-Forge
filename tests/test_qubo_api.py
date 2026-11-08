import csv
import io
import json

from test_api import client, wait_for


TRIANGLE = {'matrix': [[-2, 2, 2], [0, -2, 2], [0, 0, -2]], 'iterations': 12, 'shots': 128, 'seed': 73}


def test_qubo_job_history_and_exports_preserve_real_solver_outputs(client):
    started = client.post('/api/jobs', json={'kind': 'qubo', 'config': TRIANGLE})
    assert started.status_code == 202, started.text
    run = wait_for(client, started.json()['id'])
    assert run['status'] == 'completed', run
    result = run['result']
    assert result['exact_energy'] == -2
    assert len(result['solvers']) == 5
    assert all(row['energy'] >= -2 - 1e-9 for row in result['solvers'])
    qaoa = next(row for row in result['solvers'] if row['key'] == 'qaoa')
    assert sum(qaoa['counts'].values()) == 128
    loaded = client.get('/api/history/' + run['id']).json()
    assert loaded['result'] == result
    assert loaded['config']['matrix'] == TRIANGLE['matrix']
    assert client.get('/api/history').json()[0]['kind'] == 'qubo'
    exported = client.get('/api/history/' + run['id'] + '/export?format=json').json()
    assert exported['result']['ising'] == result['ising']
    rows = list(csv.DictReader(io.StringIO(client.get('/api/history/' + run['id'] + '/export?format=csv').text)))
    assert len(rows) == 5
    by_key = {row['key']: row for row in rows}
    for solver in result['solvers']:
        assert float(by_key[solver['key']]['energy']) == solver['energy']
        assert float(by_key[solver['key']]['gap']) == solver['gap']
        assert json.loads(by_key[solver['key']]['config']) == run['config']
        assert json.loads(by_key[solver['key']]['versions']) == result['versions']
    assert float(by_key['qaoa']['expected_energy']) == qaoa['expected_energy']
    assert float(by_key['qaoa']['initialization_s']) == qaoa['initialization_s']


def test_qubo_invalid_models_do_not_enter_history(client):
    invalid = [
        {},
        {'matrix': [[1, 2], [2, 1]]},
        {'matrix': [[1, 2], [0]]},
        {'matrix': [[101, 0], [0, 1]]},
        {'matrix': [[0] * 9 for _ in range(9)]},
        {**TRIANGLE, 'layers': 3, 'iterations': 5},
        {**TRIANGLE, 'program': '__import__("os")'},
    ]
    for config in invalid:
        response = client.post('/api/jobs', json={'kind': 'qubo', 'config': config})
        assert response.status_code == 422, response.text
    assert client.get('/api/history').json() == []

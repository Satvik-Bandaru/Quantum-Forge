from fastapi.testclient import TestClient
from backend.app import create_app


def test_malformed_content_length_is_a_client_error(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3')) as client:
        for length in ('invalid', '-1'):
            response = client.post('/api/jobs', content=b'{}', headers={'content-length': length})
            assert response.status_code == 400
            assert 'Content-Length' in response.json()['detail']
        assert client.get('/api/history').json() == []


def test_actual_body_limit_does_not_trust_declared_length(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3')) as client:
        response = client.post('/api/jobs', content=b'x' * 256001, headers={'content-length': '1'})
        assert response.status_code == 413
        assert client.get('/api/history').json() == []


def test_chunked_body_limit_and_valid_replay(tmp_path):
    with TestClient(create_app(tmp_path / 'chunked.sqlite3')) as client:
        response = client.post('/api/jobs', content=iter([b'x' * 128000, b'x' * 128001]))
        assert response.status_code == 413
        saved = client.post('/api/circuits', content=iter([
            b'{"name":"Chunked input",', b'"config":{"qubits":1}}',
        ]), headers={'content-type': 'application/json'})
        assert saved.status_code == 201
        assert client.get('/api/circuits').json()[0]['name'] == 'Chunked input'

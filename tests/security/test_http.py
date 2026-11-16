"""HTTP boundaries use temporary databases and never contact the live server."""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


@pytest.fixture(autouse=True)
def no_cli_override(monkeypatch):
    monkeypatch.delenv('QF_ALLOW_ORIGINLESS', raising=False)


@pytest.mark.parametrize('host', ['evil.example', 'testserver'])
def test_production_rejects_untrusted_host(tmp_path, host):
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url='http://' + host) as client:
        assert client.get('/api/health').status_code == 403


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
@pytest.mark.parametrize('origin', [None, '', 'http://localhost:3000', 'https://localhost:8777',
                                    'http://127.0.0.1:8777', 'null', 'http://localhost:bad',
                                    'http://localhost:8777/path', 'http://user@localhost:8777'])
def test_mutations_require_exact_origin(tmp_path, method, origin):
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url='http://localhost:8777') as client:
        headers = {} if origin is None else {'origin': origin}
        response = client.request(method, '/api/circuits', headers=headers, json={'name': 'Blocked', 'config': {}})
        assert response.status_code == 403
        assert client.get('/api/circuits').json() == []


@pytest.mark.parametrize('base_url,origin', [
    ('http://localhost:8777', 'http://localhost:8777'),
    ('http://localhost', 'http://localhost:80'),
    ('http://localhost:80', 'http://localhost'),
    ('https://localhost', 'https://localhost:443'),
    ('http://[::1]:8777', 'http://[::1]:8777'),
])
def test_same_origin_can_save(tmp_path, base_url, origin):
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url=base_url) as client:
        response = client.post('/api/circuits', headers={'origin': origin}, json={'name': 'Allowed', 'config': {}})
        assert response.status_code == 201
        assert client.get('/api/circuits').json()[0]['name'] == 'Allowed'


@pytest.mark.parametrize('setting,status', [('1', 201), ('0', 403), ('true', 403)])
def test_cli_originless_override_is_explicit(tmp_path, monkeypatch, setting, status):
    monkeypatch.setenv('QF_ALLOW_ORIGINLESS', setting)
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url='http://localhost:8777') as client:
        assert client.post('/api/circuits', json={'name': 'CLI', 'config': {}}).status_code == status
        assert client.post('/api/circuits', headers={'origin': 'http://localhost:3000'}, json={'name': 'Bad', 'config': {}}).status_code == 403


def test_testing_allows_testserver_and_absent_origin_only(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3', testing=True)) as client:
        assert client.get('/api/health').status_code == 200
        assert client.post('/api/circuits', json={'name': 'Test', 'config': {}}).status_code == 201
        assert client.post('/api/circuits', headers={'origin': 'http://localhost:3000'}, json={'name': 'Bad', 'config': {}}).status_code == 403
        assert client.get('/api/health', headers={'host': 'evil.example'}).status_code == 403


@pytest.mark.parametrize('chunked', [False, True])
def test_300kb_body_is_rejected_without_side_effects(tmp_path, chunked):
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url='http://localhost:8777') as client:
        body = iter([b'x' * 100000] * 3) if chunked else b'x' * 300000
        response = client.post('/api/jobs', content=body, headers={'origin': 'http://localhost:8777'})
        assert response.status_code == 413
        assert client.get('/api/history').json() == []


def test_testing_requires_explicit_non_user_database():
    from backend.app import ROOT
    for path in (None, ROOT / 'data' / 'experiments.sqlite3'):
        with pytest.raises(ValueError, match='explicit database path'):
            create_app(path, testing=True)


def test_duplicate_origin_headers_are_rejected(tmp_path):
    with TestClient(create_app(tmp_path / 'http.sqlite3'), base_url='http://localhost:8777') as client:
        response = client.post('/api/circuits', headers=[('origin', 'http://localhost:8777'), ('origin', 'http://evil.example')], json={'name': 'Bad', 'config': {}})
        assert response.status_code == 403

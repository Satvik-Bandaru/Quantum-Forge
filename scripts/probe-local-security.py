#!/usr/bin/env python3
"""Exercise production HTTP boundaries with curl and an isolated temporary app."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def serve(database, marker):
    sys.path.insert(0, str(ROOT))
    import uvicorn
    from backend.app import create_app
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    Path(marker).write_text(f'http://127.0.0.1:{sock.getsockname()[1]}')
    uvicorn.Server(uvicorn.Config(create_app(db_path=database, timeout_s=15), log_level='info')).run(sockets=[sock])


def probe(output):
    output.mkdir(parents=True, exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='qf-m2-curl-'))
    env = os.environ.copy()
    for key in ('QF_DB_PATH', 'QF_ALLOW_DB_MIGRATION', 'QF_ALLOW_ORIGINLESS'):
        env.pop(key, None)
    env.update({key: '1' for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')})
    evidence = {'temporary_directory': str(scratch), 'probes': [], 'passed': False}
    server = None
    def curl(name, endpoint, expected, *args):
        command = ['curl', '--silent', '--show-error', '--verbose', '--noproxy', '*', '--max-time', '10',
                   '--output', str(output / (name + '.body')), '--write-out', '%{http_code}', *args, base + endpoint]
        run = subprocess.run(command, capture_output=True, text=True, env=env, timeout=12)
        (output / (name + '.headers.log')).write_text(run.stderr)
        body = (output / (name + '.body')).read_text()
        result = {'name': name, 'command': command, 'exit_code': run.returncode,
                  'expected_status': expected, 'status': run.stdout, 'body': body}
        evidence['probes'].append(result)
        assert run.returncode == 0 and run.stdout == str(expected), result
        return json.loads(body)
    try:
        with (output / 'server.log').open('w') as log:
            server = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--serve',
                                       str(scratch / 'probe.sqlite3'), str(scratch / 'url')],
                                      env=env, stdout=log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                if server.poll() is not None:
                    raise RuntimeError('Isolated server exited; inspect server.log')
                if (scratch / 'url').exists():
                    base = (scratch / 'url').read_text()
                    ready = subprocess.run(['curl', '--silent', '--noproxy', '*', '--max-time', '1',
                                            base + '/api/health'], capture_output=True, text=True, env=env)
                    if ready.returncode == 0:
                        break
                time.sleep(.1)
            else:
                raise RuntimeError('Isolated server did not become ready')
            evidence['base_url'] = base
            curl('health', '/api/health', 200)
            curl('evil-host', '/api/health', 403, '-H', 'Host: evil.example')
            curl('testserver-host', '/api/health', 403, '-H', 'Host: testserver')
            curl('cross-port-origin', '/api/jobs', 403, '-X', 'POST', '-H', 'Origin: http://localhost:3000',
                 '-H', 'Content-Type: application/json', '--data', '{"kind":"circuit","config":{}}')
            body = scratch / '300kb.bin'
            body.write_bytes(b'x' * 300000)
            headers = ('-H', 'Origin: ' + base, '-H', 'Content-Type: application/json')
            curl('fixed-300kb', '/api/jobs', 413, *headers, '--data-binary', '@' + str(body))
            curl('chunked-300kb', '/api/jobs', 413, *headers, '-H', 'Transfer-Encoding: chunked', '--data-binary', '@' + str(body))
            assert '> Content-Length: 300000' in (output / 'fixed-300kb.headers.log').read_text()
            assert '> Transfer-Encoding: chunked' in (output / 'chunked-300kb.headers.log').read_text()
            first = curl('first-job', '/api/jobs', 202, *headers, '--data', json.dumps({
                'kind': 'optimization', 'config': {'nodes': 12, 'layers': 4, 'iterations': 150, 'repetitions': 3}}))
            try:
                curl('second-job', '/api/jobs', 409, *headers, '--data', '{"kind":"circuit","config":{}}')
            finally:
                cancelled = curl('cancel-first', '/api/jobs/' + first['id'], 200, *headers, '-X', 'DELETE')
                assert cancelled['status'] == 'cancelled', cancelled
            history = curl('history', '/api/history', 200)
            assert len(history) == 1 and history[0]['status'] == 'cancelled', history
            evidence['passed'] = True
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            evidence['server_exit_code'] = server.returncode
        (output / 'results.json').write_text(json.dumps(evidence, indent=2) + '\n')
        print(json.dumps({'passed': evidence['passed'], 'evidence': str(output),
                          'statuses': {p['name']: p['status'] for p in evidence['probes']}}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', nargs=2, metavar=('DATABASE', 'MARKER'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.serve:
        serve(*args.serve)
    elif args.output:
        probe(args.output.resolve())
    else:
        parser.error('--output is required')

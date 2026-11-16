#!/usr/bin/env bash
# Run from any directory after installing the locked Python and npm dependencies.
# QF_PYTHON selects Python; PLAYWRIGHT_BROWSER=chromium selects bundled Chromium.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
python="${QF_PYTHON:-$repo_root/.venv/bin/python}"
artifacts="${QF_REGRESSION_ARTIFACTS:-$repo_root/docs/verification/regression}"
mkdir -p "$artifacts" "$repo_root/docs/screenshots"

"$python" --version | tee "$artifacts/python.log"
node --version | tee "$artifacts/node.log"
"$python" -m pip check 2>&1 | tee "$artifacts/pip-check.log"
npm --prefix frontend ls --depth=0 2>&1 | tee "$artifacts/npm-ls.log"
"$python" -m pytest -q 2>&1 | tee "$artifacts/pytest.log"
npm --prefix frontend run build 2>&1 | tee "$artifacts/build.log"

temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/quantum-forge-regression.XXXXXX")"
server_pid=''
cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
  fi
  rm -rf "$temp_dir"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Reserve an ephemeral loopback port, and start an isolated app using a temporary
# database. An already running user instance is never reused or terminated.
cat > "$temp_dir/server.py" <<'PY'
import socket
import sys
from pathlib import Path

import uvicorn
from backend.app import create_app

if __name__ == '__main__':
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    Path(sys.argv[2]).write_text(f'http://127.0.0.1:{sock.getsockname()[1]}')
    server = uvicorn.Server(uvicorn.Config(create_app(db_path=sys.argv[1]), log_level='info'))
    server.run(sockets=[sock])
PY
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}" "$python" "$temp_dir/server.py" \
  "$temp_dir/experiments.sqlite3" "$temp_dir/base-url" > "$artifacts/server.log" 2>&1 &
server_pid=$!

"$python" - "$temp_dir/base-url" "$artifacts/health.log" <<'PY'
import json
import sys
import time
import urllib.request
from pathlib import Path

deadline = time.monotonic() + 45
last_error = None
while time.monotonic() < deadline:
    try:
        base_url = Path(sys.argv[1]).read_text()
        with urllib.request.urlopen(base_url + '/api/health', timeout=1) as response:
            health = json.load(response)
        if health.get('app') != 'quantum-forge-lab' or health.get('status') != 'ready':
            raise RuntimeError(f'Unexpected health response: {health}')
        evidence = json.dumps({'base_url': base_url, **health}, indent=2) + '\n'
        Path(sys.argv[2]).write_text(evidence)
        print(evidence, end='')
        break
    except (OSError, ValueError, RuntimeError) as error:
        last_error = error
        time.sleep(0.25)
else:
    raise SystemExit(f'Regression server did not become ready: {last_error}')
PY
export PLAYWRIGHT_BASE_URL="$(cat "$temp_dir/base-url")"
npm --prefix frontend run test:ui 2>&1 | tee "$artifacts/playwright.log"

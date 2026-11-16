#!/usr/bin/env python3
"""Build and verify a reproducible macOS source distribution with a prebuilt UI.

No install, build, tests, server, network request or Git mutation is performed.
The caller must finish verification and status documentation before packaging.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import zipfile


ARCHIVE_ROOT = 'Quantum-Forge-Nexus-Lab'
MANIFEST_NAME = 'PACKAGE-MANIFEST.json'
REQUIRED = (
    'start.command', 'launch.py', 'requirements.txt', 'requirements.lock.txt',
    'README.md', 'BUILD_STATUS.md', 'DEVELOPMENT_BACKLOG.md',
    'SCIENTIFIC_VALIDATION.md', 'NEXT_SESSION.md', 'frontend/dist/index.html',
)
EXCLUDED_PARTS = frozenset({
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.cache', '.tox', 'test-results',
    'playwright-report', 'tmp', 'temp', '.DS_Store',
})
START_HERE = '''# Start Quantum Forge Nexus Lab on macOS

This download is an unsigned source distribution with a prebuilt web interface.
It is not a signed, standalone macOS .app. Simulation runs locally on your CPU.

1. Extract the entire ZIP to a writable folder. Keep its files together.
2. Install Python 3.12 if needed. First setup requires internet access to download
   the Python packages. No account, paid service or quantum hardware is required.
3. For a reproducible first setup, open Terminal in this extracted folder and run:

   ```sh
   python3.12 -m venv .venv
   .venv/bin/python -m pip install -r requirements.lock.txt
   ```

4. Double-click `start.command`, or run `./start.command` in that folder.
   Leave its Terminal window open and use http://127.0.0.1:8777 in your browser.
   Ctrl+C in the Terminal stops the local service.

Node.js is not needed to use this download because `frontend/dist` is included.
Node is needed only if you change/rebuild the frontend. If you skip the explicit
setup above, the launcher uses the `python3` on your PATH and installs from
requirements.txt; ensure that interpreter is Python 3.12. Use the locked setup
above for the dependency versions recorded in this package.

Experiment history is created locally in data/experiments.sqlite3. No personal
history, virtual environment or installed dependencies are included. If another
lab is already running on port 8777, the launcher opens that instance; stop it
first when you intend to run this extracted version.

Read BUILD_STATUS.md and SCIENTIFIC_VALIDATION.md for the measured verification
and model limits, DEVELOPMENT_BACKLOG.md for planned work, and NEXT_SESSION.md
for the development handoff. This package may include uncommitted features;
PACKAGE-MANIFEST.json identifies its base commit and working-tree status.

The manifest lists the SHA-256, size and Unix permission mode of every payload
file except the manifest itself. The adjacent .zip.sha256 file hashes the entire
ZIP, including its manifest. These hashes detect corruption, not publisher identity.
'''


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *arguments])


def _excluded(path: PurePosixPath) -> bool:
    name = path.name
    return (bool(EXCLUDED_PARTS.intersection(path.parts))
            or name == '.env' or name.startswith('.env.')
            or name.endswith(('.pyc', '.pyo', '.tsbuildinfo', '.zip', '.zip.sha256'))
            or '.sqlite' in name.lower()
            or path.parts[:3] == ('docs', 'verification', 'regression'))


def _fingerprint(path: Path) -> tuple[int, int, int, int]:
    metadata = path.stat()
    return metadata.st_size, metadata.st_mtime_ns, metadata.st_ino, stat.S_IMODE(metadata.st_mode)


def verify_archive(archive: Path) -> dict:
    """Verify CRC, inventory, SHA-256, sizes and permissions before publication."""
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise ValueError(f'ZIP CRC verification failed: {bad}')
        manifest_path = f'{ARCHIVE_ROOT}/{MANIFEST_NAME}'
        manifest = json.loads(bundle.read(manifest_path))
        inventory = manifest['files']
        expected = {f'{ARCHIVE_ROOT}/{item["path"]}' for item in inventory} | {manifest_path}
        if len(bundle.namelist()) != len(expected) or set(bundle.namelist()) != expected:
            raise ValueError('ZIP file inventory does not match the manifest.')
        for item in inventory:
            member = f'{ARCHIVE_ROOT}/{item["path"]}'
            data = bundle.read(member)
            info = bundle.getinfo(member)
            actual_mode = stat.S_IMODE(info.external_attr >> 16)
            if (hashlib.sha256(data).hexdigest() != item['sha256']
                    or len(data) != item['size'] or actual_mode != int(item['mode'], 8)):
                raise ValueError(f'Payload verification failed: {item["path"]}')
        launch = bundle.getinfo(f'{ARCHIVE_ROOT}/start.command')
        if stat.S_IMODE(launch.external_attr >> 16) != 0o755:
            raise ValueError('start.command is not executable in the ZIP.')
    return manifest


def _zip_info(path: str, mode: int) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(f'{ARCHIVE_ROOT}/{path}', date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def build_archive(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    checksum = output.with_name(output.name + '.sha256')
    if output.suffix.lower() != '.zip':
        raise ValueError('Output must have a .zip extension.')
    listed = _git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    paths = {PurePosixPath(os.fsdecode(name)) for name in listed.split(b'\0') if name}
    paths.update(PurePosixPath(path.relative_to(root).as_posix())
                 for path in (root/'frontend'/'dist').rglob('*') if path.is_file())
    paths = {path for path in paths if not _excluded(path)
             and (root/str(path)).resolve() not in (output, checksum)}
    for required in REQUIRED:
        if PurePosixPath(required) not in paths or not (root/required).is_file():
            raise ValueError(f'Missing required package file: {required}')
    for prefix, extension in [('frontend/public/lab/models/', '.glb'),
                              ('frontend/dist/lab/models/', '.glb'),
                              ('frontend/public/lab/photos/', None),
                              ('frontend/dist/lab/photos/', None)]:
        if not any(str(path).startswith(prefix) and (extension is None or path.suffix == extension) for path in paths):
            raise ValueError(f'Missing required laboratory assets: {prefix}')

    base_commit = _git(root, 'rev-parse', 'HEAD').decode().strip()
    branch = _git(root, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip()
    status_bytes = _git(root, 'status', '--porcelain=v1', '-z')
    status_entries = [os.fsdecode(entry) for entry in status_bytes.split(b'\0') if entry]
    payload = {}
    fingerprints = {}
    for relative in sorted(paths, key=str):
        source = root/str(relative)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Unsafe source path: {relative}')
        if source.is_symlink() or source.resolve() != source:
            raise ValueError(f'Symlinks are not packaged: {relative}')
        if not source.is_file():
            # Git can list a tracked file deleted in the current working tree.
            continue
        before = _fingerprint(source)
        data = source.read_bytes()
        if before != _fingerprint(source):
            raise RuntimeError(f'Source changed while being read: {relative}')
        mode = 0o755 if str(relative) == 'start.command' or before[3] & 0o111 else 0o644
        payload[str(relative)] = (data, mode)
        fingerprints[source] = before
    payload['START-HERE.md'] = (START_HERE.encode(), 0o644)
    # Generated manifest cannot hash itself. The adjacent archive checksum covers it.
    payload.pop(MANIFEST_NAME, None)
    manifest = {
        'schema_version': 1,
        'distribution': 'Quantum Forge Nexus Lab / macOS source with prebuilt frontend',
        'archive_root': ARCHIVE_ROOT,
        'signed_standalone_app': False,
        'source_git': {'base_commit': base_commit, 'branch': branch,
                       'includes_uncommitted_changes': bool(status_entries),
                       'feature_status': 'Uncommitted working-tree snapshot; consult the four status documents.'
                       if status_entries else 'Committed source snapshot; consult the four status documents.',
                       'working_tree_status_porcelain_v1_z_entries': status_entries},
        'reproducibility': 'Sorted entries; fixed ZIP timestamp; normalized 0644/0755 modes; no wall-clock timestamp.',
        'hash_scope': 'Every payload except PACKAGE-MANIFEST.json; adjacent ZIP checksum covers the entire archive.',
        'files': [{'path': path, 'size': len(data), 'mode': f'{mode:04o}',
                   'sha256': hashlib.sha256(data).hexdigest()}
                  for path, (data, mode) in sorted(payload.items())],
    }
    manifest_data = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_archive = temporary_checksum = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.'+output.name+'.', suffix='.tmp', dir=output.parent, delete=False) as temporary:
            temporary_archive = Path(temporary.name)
        with zipfile.ZipFile(temporary_archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for path, (data, mode) in sorted(payload.items()):
                bundle.writestr(_zip_info(path, mode), data, compresslevel=9)
            bundle.writestr(_zip_info(MANIFEST_NAME, 0o644), manifest_data, compresslevel=9)
        verify_archive(temporary_archive)
        for source, before in fingerprints.items():
            if not source.is_file() or _fingerprint(source) != before:
                raise RuntimeError(f'Source changed during packaging: {source.relative_to(root)}')
        if _git(root, 'status', '--porcelain=v1', '-z') != status_bytes:
            raise RuntimeError('Working-tree status changed during packaging; retry after edits finish.')
        digest = hashlib.sha256(temporary_archive.read_bytes()).hexdigest()
        with temporary_archive.open('rb') as verified:
            os.fsync(verified.fileno())
        with tempfile.NamedTemporaryFile(prefix='.'+checksum.name+'.', suffix='.tmp', dir=output.parent, delete=False) as temporary:
            temporary_checksum = Path(temporary.name)
            temporary.write(f'{digest}  {output.name}\n'.encode())
            temporary.flush()
            os.fsync(temporary.fileno())
        # Existing downloads remain intact until all inventory and integrity checks pass.
        os.replace(temporary_archive, output)
        temporary_archive = None
        os.replace(temporary_checksum, checksum)
        temporary_checksum = None
        return {'archive': str(output), 'checksum_file': str(checksum), 'sha256': digest,
                'payload_files': len(manifest['files']), 'archive_bytes': output.stat().st_size,
                'base_commit': base_commit, 'includes_uncommitted_changes': bool(status_entries)}
    finally:
        for temporary in (temporary_archive, temporary_checksum):
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', nargs='?', type=Path,
                        default=root.parent/'Quantum Forge Downloads'/'Quantum-Forge-Nexus-Lab-macOS.zip',
                        help='ZIP output path (default: sibling Quantum Forge Downloads folder)')
    arguments = parser.parse_args()
    try:
        result = build_archive(root, arguments.output)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Packaging failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

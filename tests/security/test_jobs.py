"""Deterministic worker lifecycle races, with real pipes and temporary SQLite."""
import multiprocessing as mp
from multiprocessing.connection import Connection
import os
import threading
import time

import pytest

from backend import jobs
from backend.jobs import BusyError, JobManager
from backend.store import Store


class ControlledProcess:
    """Hold the OS wait boundary open so competing requests can be exercised."""
    def __init__(self, *, target, args, daemon):
        self.join_entered = threading.Event()
        self.release_join = threading.Event()
        self.alive = False
        self.killed = False
        self.block_at = 'join'
        self.pid = 1
        self.sender = Connection(os.dup(args[0].fileno()), readable=False)

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive

    def terminate(self):
        pass  # Force escalation to kill after the first join.

    def join(self, timeout):
        if not self.killed and self.block_at == 'join':
            self.join_entered.set()
            assert self.release_join.wait(5), 'test did not release the controlled process'

    def kill(self):
        if self.block_at == 'kill':
            self.join_entered.set()
            assert self.release_join.wait(5), 'test did not release controlled kill'
        self.killed = True
        self.alive = False
        self.sender.close()


@pytest.fixture
def controlled_manager(tmp_path, monkeypatch):
    context = mp.get_context('spawn')
    monkeypatch.setattr(context, 'Process', ControlledProcess)
    # Memory observations are covered with actual spawned workers in test_api.py.
    monkeypatch.setattr(jobs.psutil, 'Process', lambda pid: type('Memory', (), {
        'memory_info': lambda self: type('RSS', (), {'rss': 0})()
    })())
    manager = JobManager(Store(tmp_path / 'jobs.sqlite3'), timeout_s=.01)
    yield manager
    if manager.active:
        manager.active['process'].release_join.set()
    manager.close()


@pytest.mark.parametrize('block_at', ['join', 'kill'])
def test_cancel_during_watchdog_termination_does_not_block_or_release_slot(controlled_manager, block_at):
    manager = controlled_manager
    with manager.lock:
        first = manager.start('circuit', {})
        old_job = manager.active
        process = old_job['process']
        process.block_at = block_at
    assert process.join_entered.wait(2)
    done = threading.Event()
    outcomes = {}

    def competing_requests():
        outcomes['cancel'] = manager.cancel(first['id'])
        try:
            manager.start('circuit', {})
        except BusyError:
            outcomes['busy'] = True
        done.set()

    contender = threading.Thread(target=competing_requests, daemon=True)
    contender.start()
    try:
        assert done.wait(1), 'cancel/start blocked behind worker join'
        assert outcomes['cancel']['status'] == 'running'
        assert outcomes['busy'] is True
        assert manager.store.get(first['id'])['finished_at'] is None
    finally:
        process.release_join.set()
        contender.join(2)
    deadline = time.monotonic() + 2
    while manager.store.get(first['id'])['status'] == 'running' and time.monotonic() < deadline:
        time.sleep(.01)
    persisted = manager.store.get(first['id'])
    assert persisted['status'] == 'timed_out'
    assert persisted['finished_at']
    assert process.killed
    # Cancellation cannot overwrite a terminal result or dispose of the next job.
    manager.timeout_s = 100
    second = manager.start('circuit', {})
    manager.finish('failed', job=old_job, error='stale monitor decision')
    assert manager.cancel(first['id']) == persisted
    assert manager.active['id'] == second['id']
    manager.active['process'].release_join.set()
    assert manager.cancel(second['id'])['status'] == 'cancelled'


def test_closed_manager_rejects_start_without_persisting_or_spawning(controlled_manager):
    manager = controlled_manager
    manager.close()
    manager.close()
    with pytest.raises(BusyError, match='closed'):
        manager.start('circuit', {})
    assert manager.store.history() == []


def wait_for_status(manager, job_id, status):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        document = manager.store.get(job_id)
        if document['status'] == status:
            return document
        time.sleep(.01)
    assert manager.store.get(job_id)['status'] == status


def test_transient_terminal_persistence_failure_retries_original_result(controlled_manager, monkeypatch):
    import sqlite3

    manager = controlled_manager
    manager.timeout_s = 100
    job = manager.start('circuit', {})
    manager.active['process'].release_join.set()
    update = manager.store.update
    failed = threading.Event()

    def fail_once(run_id, **changes):
        if not failed.is_set():
            failed.set()
            raise sqlite3.OperationalError('temporary database lock')
        return update(run_id, **changes)

    monkeypatch.setattr(manager.store, 'update', fail_once)
    manager.finish('completed', result={'kind': 'circuit', 'answer': 42})
    assert failed.is_set()
    result = wait_for_status(manager, job['id'], 'completed')
    assert result['result'] == {'kind': 'circuit', 'answer': 42}
    with manager.lock:
        assert manager.active is None
    assert manager.thread.is_alive()


@pytest.mark.parametrize('method', ['terminate', 'join', 'kill'])
def test_cleanup_error_retries_without_releasing_live_worker(controlled_manager, monkeypatch, method):
    manager = controlled_manager
    manager.timeout_s = 100
    job = manager.start('circuit', {})
    process = manager.active['process']
    process.release_join.set()
    original = getattr(process, method)
    recovered = threading.Event()

    def unavailable(*args, **kwargs):
        if not recovered.is_set():
            raise OSError('temporary process cleanup failure')
        return original(*args, **kwargs)

    monkeypatch.setattr(process, method, unavailable)
    assert manager.cancel(job['id'])['status'] == 'running'
    assert process.is_alive()
    with pytest.raises(BusyError):
        manager.start('circuit', {})
    recovered.set()
    assert wait_for_status(manager, job['id'], 'cancelled')['finished_at']
    assert not process.is_alive()
    assert manager.thread.is_alive()


def test_kill_without_confirmed_exit_keeps_slot_until_retry(controlled_manager, monkeypatch):
    manager = controlled_manager
    manager.timeout_s = 100
    job = manager.start('circuit', {})
    process = manager.active['process']
    process.release_join.set()
    kill = process.kill
    may_exit = threading.Event()
    monkeypatch.setattr(process, 'kill', lambda: kill() if may_exit.is_set() else None)
    assert manager.cancel(job['id'])['status'] == 'running'
    with pytest.raises(BusyError):
        manager.start('circuit', {})
    may_exit.set()
    wait_for_status(manager, job['id'], 'cancelled')
    assert not process.is_alive()


def test_close_retries_transient_persistence_failure_before_monitor_exits(controlled_manager, monkeypatch):
    import sqlite3

    manager = controlled_manager
    manager.timeout_s = 100
    job = manager.start('circuit', {})
    manager.active['process'].release_join.set()
    update = manager.store.update
    failed = threading.Event()

    def fail_once(run_id, **changes):
        if not failed.is_set():
            failed.set()
            raise sqlite3.OperationalError('temporary database lock')
        return update(run_id, **changes)

    monkeypatch.setattr(manager.store, 'update', fail_once)
    manager.close()
    manager.close()
    assert manager.store.get(job['id'])['status'] == 'interrupted'
    assert manager.active is None
    assert not manager.thread.is_alive()

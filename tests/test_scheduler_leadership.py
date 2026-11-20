"""Only one worker process may run the background scheduler.

Regression: with two gunicorn workers, both ran the hourly connector sweep at
the same moment. Every connector synced twice and the staging container was
killed for exceeding its memory limit, over and over.
"""
import asyncio
import multiprocessing

import pytest

from app.tasks.scheduler import TaskScheduler

fcntl = pytest.importorskip("fcntl")


def _try_lead(lock_path, queue):
    queue.put(TaskScheduler(lock_path=lock_path)._acquire_leadership())


def test_second_scheduler_in_same_container_does_not_lead(tmp_path):
    lock = str(tmp_path / "scheduler.lock")
    first = TaskScheduler(lock_path=lock)
    second = TaskScheduler(lock_path=lock)
    try:
        assert first._acquire_leadership() is True
        assert second._acquire_leadership() is False
    finally:
        first._release_leadership()
        second._release_leadership()


def test_another_process_cannot_lead_while_the_lock_is_held(tmp_path):
    lock = str(tmp_path / "scheduler.lock")
    leader = TaskScheduler(lock_path=lock)
    assert leader._acquire_leadership() is True
    try:
        ctx = multiprocessing.get_context("spawn")
        queue = ctx.Queue()
        proc = ctx.Process(target=_try_lead, args=(lock, queue))
        proc.start()
        proc.join(60)
        assert queue.get(timeout=10) is False
    finally:
        leader._release_leadership()


def test_leadership_passes_on_after_stop(tmp_path):
    lock = str(tmp_path / "scheduler.lock")
    first = TaskScheduler(lock_path=lock)
    second = TaskScheduler(lock_path=lock)
    assert first._acquire_leadership() is True
    first.stop()
    try:
        assert second._acquire_leadership() is True
    finally:
        second._release_leadership()


def test_start_schedules_nothing_when_not_the_leader(tmp_path):
    lock = str(tmp_path / "scheduler.lock")
    leader = TaskScheduler(lock_path=lock)
    follower = TaskScheduler(lock_path=lock)

    async def scenario():
        leader.start()
        follower.start()
        try:
            assert leader.running is True and set(leader.tasks) >= {"connector_sync", "connector_health"}
            assert follower.running is False and follower.tasks == {}
        finally:
            leader.stop()
            follower.stop()

    asyncio.run(scenario())

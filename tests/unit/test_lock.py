import fakeredis
import pytest

from amtaf.lock import BenchBusy, BenchLock


def test_second_run_is_blocked():
    client = fakeredis.FakeRedis()
    with BenchLock(client, "rack1", ttl=30, wait=0.1):
        with pytest.raises(BenchBusy):
            with BenchLock(client, "rack1", ttl=30, wait=0.1):
                pass


def test_released_after_exit():
    client = fakeredis.FakeRedis()
    with BenchLock(client, "rack1", wait=0.1):
        pass
    with BenchLock(client, "rack1", wait=0.1):
        pass


def test_different_benches_do_not_conflict():
    client = fakeredis.FakeRedis()
    with BenchLock(client, "rack1", wait=0.1):
        with BenchLock(client, "rack2", wait=0.1):
            pass

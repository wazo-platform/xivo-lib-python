# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import patch

from cheroot.workers.threadpool import ThreadPool
from cheroot.wsgi import Server
from hamcrest import assert_that, equal_to, none, not_none

from ..wsgi import _REQUIRED_POOL_INTERNALS, DynamicWSGIServer, _compute_adjustment


class TestCherootPoolInternals(unittest.TestCase):
    def test_required_private_attributes_exist(self):
        # DynamicWSGIServer relies on these private cheroot attributes; fail
        # loudly here when a cheroot upgrade renames one.
        pool = ThreadPool(server=None)

        for name in _REQUIRED_POOL_INTERNALS:
            assert_that(hasattr(pool, name), equal_to(True), name)


class TestComputeAdjustment(unittest.TestCase):
    def _compute(self, **kwargs):
        defaults = {
            'threads': 10,
            'idle': 5,
            'qsize': 0,
            'min_threads': 2,
            'max_threads': 50,
            'minspare': 2,
            'maxspare': 8,
        }
        defaults.update(kwargs)
        return _compute_adjustment(**defaults)

    def test_steady_state_does_nothing(self):
        assert_that(self._compute(idle=5, qsize=0), equal_to(0))

    def test_grows_to_maintain_minspare(self):
        assert_that(self._compute(idle=0, qsize=0, minspare=2), equal_to(2))
        assert_that(self._compute(idle=1, qsize=0, minspare=2), equal_to(1))

    def test_grows_by_backlog_on_top_of_minspare(self):
        assert_that(self._compute(idle=0, qsize=5, minspare=2), equal_to(7))

    def test_grows_only_for_backlog_beyond_idle_workers(self):
        assert_that(self._compute(idle=3, qsize=4, minspare=2), equal_to(1))

    def test_backlog_covered_by_idle_workers_does_nothing(self):
        assert_that(self._compute(idle=5, qsize=3, minspare=2), equal_to(0))

    def test_growth_is_capped_by_max_threads(self):
        assert_that(
            self._compute(threads=48, idle=0, qsize=10, max_threads=50),
            equal_to(2),
        )

    def test_growth_at_max_threads_does_nothing(self):
        assert_that(
            self._compute(threads=50, idle=0, qsize=10, max_threads=50),
            equal_to(0),
        )

    def test_negative_max_threads_means_unbounded_growth(self):
        assert_that(
            self._compute(threads=100, idle=0, qsize=10, max_threads=-1),
            equal_to(12),
        )

    def test_growth_is_capped_at_doubling_per_tick(self):
        assert_that(
            self._compute(threads=10, idle=0, qsize=100, max_threads=-1),
            equal_to(10),
        )

    def test_shrinks_one_thread_per_tick_above_maxspare(self):
        assert_that(self._compute(threads=20, idle=12, maxspare=8), equal_to(-1))

    def test_shrink_at_min_threads_does_nothing(self):
        assert_that(
            self._compute(threads=2, idle=2, min_threads=2, maxspare=1),
            equal_to(0),
        )


class TestDynamicWSGIServerEnablement(unittest.TestCase):
    # Instantiating the server does not bind any socket (that happens in
    # prepare()), so building instances in unit tests is safe.

    def _new_server(self, **kwargs):
        def app(environ, start_response):
            return []

        return DynamicWSGIServer(('127.0.0.1', 0), app, **kwargs)

    def test_enabled_when_min_below_max(self):
        server = self._new_server(numthreads=2, max=10)

        assert_that(server._dynamic_enabled, equal_to(True))

    def test_enabled_when_unbounded(self):
        server = self._new_server(numthreads=2, max=-1)

        assert_that(server._dynamic_enabled, equal_to(True))

    def test_disabled_with_info_when_min_equals_max(self):
        with self.assertLogs('xivo.wsgi', level='INFO') as logs:
            server = self._new_server(numthreads=10, max=10)

        assert_that(server._dynamic_enabled, equal_to(False))
        assert_that(logs.records[0].levelname, equal_to('INFO'))

    def test_disabled_with_warning_when_min_above_max(self):
        with self.assertLogs('xivo.wsgi', level='WARNING') as logs:
            server = self._new_server(numthreads=20, max=10)

        assert_that(server._dynamic_enabled, equal_to(False))
        assert_that(logs.records[0].levelname, equal_to('WARNING'))

    def test_minspare_above_maxspare_is_rejected(self):
        with self.assertRaises(ValueError):
            self._new_server(minspare=10, maxspare=8)

    def test_negative_minspare_is_rejected(self):
        with self.assertRaises(ValueError):
            self._new_server(minspare=-1, maxspare=8)

    def test_non_positive_resize_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            self._new_server(resize_interval=0)
        with self.assertRaises(ValueError):
            self._new_server(resize_interval=-5.0)


class TestPrepareStartsMonitor(unittest.TestCase):
    # cheroot's Server.prepare() binds a socket; it is mocked out so these
    # tests only exercise the monitor thread startup logic layered on top.

    def _new_server(self, **kwargs):
        def app(environ, start_response):
            return []

        return DynamicWSGIServer(('127.0.0.1', 0), app, **kwargs)

    def _stop_monitor(self, server):
        server._monitor_stopped.set()
        if server._monitor_thread is not None:
            server._monitor_thread.join()

    def test_prepare_does_not_start_monitor_when_scaling_disabled(self):
        with self.assertLogs('xivo.wsgi', level='INFO'):
            server = self._new_server(numthreads=10, max=10)

        with patch.object(Server, 'prepare'):
            server.prepare()

        assert_that(server._monitor_thread, none())

    def test_prepare_starts_monitor_when_scaling_enabled(self):
        server = self._new_server(numthreads=2, max=10)

        with patch.object(Server, 'prepare'):
            server.prepare()
        self.addCleanup(self._stop_monitor, server)

        assert_that(server._monitor_thread, not_none())
        assert_that(server._monitor_thread.is_alive(), equal_to(True))

    def test_prepare_restarts_monitor_after_a_previous_stop(self):
        server = self._new_server(numthreads=2, max=10)
        server._monitor_stopped.set()

        with patch.object(Server, 'prepare'):
            server.prepare()
        self.addCleanup(self._stop_monitor, server)

        assert_that(server._monitor_stopped.is_set(), equal_to(False))
        assert_that(server._monitor_thread.is_alive(), equal_to(True))


class FakePool:
    def __init__(self, fail_at=None):
        self._threads = []
        self._fail_at = fail_at

    def _spawn_worker(self):
        if self._fail_at is not None and len(self._threads) >= self._fail_at:
            raise RuntimeError("can't start new thread")
        return object()


class TestGrowPool(unittest.TestCase):
    def _new_server(self):
        def app(environ, start_response):
            return []

        return DynamicWSGIServer(('127.0.0.1', 0), app)

    def test_spawns_the_requested_amount(self):
        pool = FakePool()

        self._new_server()._grow_pool(pool, 3)

        assert_that(len(pool._threads), equal_to(3))

    def test_partial_spawn_failure_keeps_started_workers_registered(self):
        pool = FakePool(fail_at=2)

        with self.assertRaises(RuntimeError):
            self._new_server()._grow_pool(pool, 5)

        assert_that(len(pool._threads), equal_to(2))

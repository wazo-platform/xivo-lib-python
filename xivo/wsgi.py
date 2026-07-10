# Copyright 2024-2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any

from cheroot.wsgi import PathInfoDispatcher, Server

logger = logging.getLogger(__name__)

# Patch for WAZO-3846 (https://wazo-dev.atlassian.net/browse/WAZO-3846)
#
# After an OSError, cheroot worker threads would hang and any following
# request opens a file descriptor until the maximum limit is reached. At this
# point the logger outputs 5k lines/second of warnings about reaching the
# limit of file descritors.
#
# Stopping the service when such error occurs avoid flooding the log files.
#
# Check upstream package for any change in the 'serve' function when migrating
# from bookworm to trixie (and subsequent)


class PatchedWSGIServer(Server):  # noqa
    def serve(self) -> None:
        """Serve requests, after invoking :func:`prepare()`."""
        while self.ready and not self.interrupt:
            try:
                self._connections.run(self.expiration_interval)
            except OSError:
                self.error_log(
                    'OS Error while serving an HTTP request',
                    level=logging.ERROR,
                    traceback=True,
                )
                os._exit(os.EX_OSERR)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                self.error_log(
                    'Error in HTTPServer.serve',
                    level=logging.ERROR,
                    traceback=True,
                )
        # raise exceptions reported by any worker threads,
        # such that the exception is raised from the serve() thread.
        if self.interrupt:
            while self._stopping_for_interrupt:
                time.sleep(0.1)
            if self.interrupt:
                raise self.interrupt


# Private cheroot attributes the resize path needs; probed at startup since
# the production cheroot version is not constrained.
_REQUIRED_POOL_INTERNALS = ('_clear_dead_threads', '_spawn_worker', '_threads')


def _compute_adjustment(
    threads: int,
    idle: int,
    qsize: int,
    min_threads: int,
    max_threads: int,
    minspare: int,
    maxspare: int,
) -> int:
    """Decide how to resize a cheroot thread pool.

    Returns the number of threads to add (positive), remove (negative)
    or 0 to leave the pool as is. ``max_threads <= 0`` means unbounded,
    matching cheroot's ``ThreadPool.max`` semantics.
    """
    # Grow for the spare buffer plus the backlog idle workers cannot absorb
    # (qsize is an instantaneous snapshot; the full backlog would overreact).
    wanted = max(minspare - idle, 0) + max(qsize - idle, 0)
    if wanted > 0:
        # At most double per tick: bounds reconnect storms on unbounded pools.
        wanted = min(wanted, max(threads, 1))
        if max_threads > 0:
            wanted = min(wanted, max(max_threads - threads, 0))
        return wanted

    if idle > maxspare and threads > min_threads:
        # One thread per tick: mass shrinks oscillate on bursty load and
        # queue shutdown requests ahead of incoming connections.
        return -1

    return 0


class DynamicWSGIServer(PatchedWSGIServer):
    """A WSGI server whose thread pool grows and shrinks with demand.

    cheroot's ThreadPool exposes grow()/shrink() but never calls them:
    ``numthreads`` workers are spawned at startup and live forever. This
    server keeps ``numthreads`` as the pool minimum, ``max`` as the pool
    maximum, and runs a monitor thread that resizes the pool every
    ``resize_interval`` seconds to keep between ``minspare`` and
    ``maxspare`` idle workers.
    """

    def __init__(
        self,
        *args: Any,
        minspare: int = 2,
        maxspare: int = 8,
        resize_interval: float = 5.0,
        **kwargs: Any,
    ) -> None:
        if minspare < 0 or maxspare < minspare:
            raise ValueError(
                f'expected 0 <= minspare <= maxspare, got {minspare=} {maxspare=}'
            )
        if resize_interval <= 0:
            raise ValueError(f'expected resize_interval > 0, got {resize_interval}')
        super().__init__(*args, **kwargs)
        self._minspare = minspare
        self._maxspare = maxspare
        self._resize_interval = resize_interval
        self._monitor_stopped = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        pool = self.requests
        self._dynamic_enabled = True
        missing_internals = [
            name for name in _REQUIRED_POOL_INTERNALS if not hasattr(pool, name)
        ]
        if missing_internals:
            self._dynamic_enabled = False
            logger.warning(
                'cheroot ThreadPool internals %s are missing: '
                'thread pool scaling disabled',
                missing_internals,
            )
        elif pool.min == pool.max:
            self._dynamic_enabled = False
            logger.info(
                'min_threads == max_threads (%s): thread pool scaling disabled',
                pool.min,
            )
        elif 0 < pool.max < pool.min:
            self._dynamic_enabled = False
            logger.warning(
                'min_threads (%s) > max_threads (%s): thread pool scaling disabled',
                pool.min,
                pool.max,
            )

    def prepare(self) -> None:
        super().prepare()
        if not self._dynamic_enabled:
            return
        # Non-daemon: grown workers inherit this thread's daemon flag, and
        # daemon workers would be killed mid-request at interpreter exit.
        self._monitor_thread = threading.Thread(
            target=self._monitor_pool,
            name='WSGIThreadPoolMonitor',
            daemon=False,
        )
        self._monitor_thread.start()

    def stop(self) -> None:
        self._monitor_stopped.set()
        if self._monitor_thread is not None:
            # No timeout: giving up mid-resize lets pool.stop() race an
            # in-flight grow, hanging shutdown; the monitor exits quickly.
            self._monitor_thread.join()
        super().stop()

    def _monitor_pool(self) -> None:
        while not self._monitor_stopped.wait(self._resize_interval):
            try:
                self._resize_pool()
            except Exception:
                # Best-effort: a stale pool size beats a dead monitor.
                logger.exception('Error while resizing the WSGI thread pool')

    def _resize_pool(self) -> None:
        pool = self.requests
        # cheroot culls dead workers only inside shrink(); cull before
        # measuring so the stats do not freeze on dead threads.
        pool._clear_dead_threads()
        threads = len(pool._threads)
        adjustment = _compute_adjustment(
            threads=threads,
            idle=pool.idle,
            qsize=pool.qsize,
            min_threads=pool.min,
            max_threads=pool.max,
            minspare=self._minspare,
            maxspare=self._maxspare,
        )
        if adjustment > 0:
            self._grow_pool(pool, adjustment)
            logger.info('WSGI thread pool grown: %s -> %s', threads, len(pool._threads))
        elif adjustment < 0:
            pool.shrink(-adjustment)
            logger.info(
                'WSGI thread pool shrink requested: %s -> %s',
                threads,
                threads + adjustment,
            )

    def _grow_pool(self, pool: Any, amount: int) -> None:
        # Not pool.grow(): its wait-until-ready spin wedges forever if a
        # worker dies before becoming ready, and its bulk spawn leaks
        # workers when creation fails partway.
        for _ in range(amount):
            pool._threads.append(pool._spawn_worker())


WSGIServer = PatchedWSGIServer
# cheroot ships no type information, so annotate the re-export to give callers a
# typed callable instead of an untyped-call error.
WSGIPathInfoDispatcher: Callable[..., Any] = PathInfoDispatcher

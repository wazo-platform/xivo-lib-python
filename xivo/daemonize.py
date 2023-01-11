# Copyright 2007-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Transforms a process into a daemon from hell

WARNING: Linux specific module, needs /proc/
"""
from __future__ import annotations

import os
import re
import sys
import errno
import logging
from contextlib import contextmanager
from typing import Generator

SLASH_PROC = os.sep + 'proc'
PROG_SLINK = 'exe'
PROG_CMDLN = 'cmdline'


log = logging.getLogger("xivo.daemonize")  # pylint: disable-msg=C0103


def c14n_prog_name(arg: str) -> str:
    return os.path.basename(re.sub(r'\.py$', '', arg))


def remove_if_stale_pidfile(pidfile: str) -> None:
    """
    @pidfile: PID file to remove if it is staled.

    Exceptions are logged and are not propagated.
    """
    try:
        try:
            pid_maydaemon = int(open(pidfile).readline().strip())
        except OSError as e:
            if e.errno == errno.ENOENT:
                return  # nothing to suppress, so do nothing...
            raise
        # Who are we?
        i_am = c14n_prog_name(sys.argv[0])
        try:
            other_cmdline = (
                open(os.path.join(SLASH_PROC, str(pid_maydaemon), PROG_CMDLN))
                .read()
                .split('\0')
            )
            if len(other_cmdline) and other_cmdline[-1] == "":
                other_cmdline.pop()
        except OSError as e:
            if e.errno == errno.ENOENT:
                # no process with the PID extracted from the
                # pidfile, so no problem to remove the latter
                os.unlink(pidfile)
                return
            raise
        # Check the whole command line of the other process
        if i_am in map(c14n_prog_name, other_cmdline):
            log.warning(
                "A pidfile %r already exists (contains pid %d) and the "
                "correponding process command line contains our own name %r",
                pidfile,
                pid_maydaemon,
                i_am,
            )
            return
        # It may not be us, but we must be quite sure about that so also try
        # to validate with the name of the executable.
        full_pgm = lock_pgm = None
        try:
            full_pgm = os.readlink(
                os.path.join(SLASH_PROC, str(pid_maydaemon), PROG_SLINK)
            )
            lock_pgm = os.path.basename(full_pgm)
        except OSError as e:
            if e.errno == errno.EACCES:
                # We consider it's ok not being able to access
                # "/proc/<pid>/exe" if we could previously access
                # "/proc/<pid>/cmdline", because if we do not have
                # the needed permissions to run the daemon this will
                # be catched latter (potentially when creating our
                # own pidfile)
                lock_pgm = None
            else:
                raise
        if i_am == lock_pgm:
            log.warning(
                "A pidfile %r already exists (contains pid %d) and an "
                "executable with our name %r is runnning with that pid.",
                pidfile,
                pid_maydaemon,
                i_am,
            )
            return
        # Ok to remove the previously existing pidfile now.
        log.info(
            "A pidfile %r already exists (contains pid %d) but the "
            "corresponding process does not seem to match with our own name %r.  "
            "Will remove the pidfile.",
            pidfile,
            pid_maydaemon,
            i_am,
        )
        log.info("Splitted command line of the other process: %s", other_cmdline)
        if lock_pgm:
            log.info(
                "Name of the executable the other process comes from: %s", full_pgm
            )
        os.unlink(pidfile)
        return
    except Exception:  # pylint: disable-msg=W0703
        log.exception("unexpected error")


def take_file_lock(own_file: str, lock_file: str, own_content: str) -> bool:
    """
    Atomically "move" @own_file to @lock_file if the latter does not exist,
    else just remove @own_file.

    @own_file: filepath of the temporary file that contains our PID
    @lock_file: destination filepath
    @own_content: content of @own_file

    Return True if the lock has been successfully taken, else False.
    (Caller should also be prepared for OSError exceptions)
    """
    try:
        try:
            os.link(own_file, lock_file)
        finally:
            os.unlink(own_file)
    except OSError as e:
        if e.errno == errno.EEXIST:
            log.warning(
                "The lock file %r already exists - won't "
                "overwrite it.  An other instance of ourself "
                "is probably running.",
                lock_file,
            )
            return False
        else:
            raise
    content = open(lock_file).read(len(own_content) + 1)
    if content != own_content:
        log.warning(
            "I thought I successfully took the lock file %r but "
            "it does not contain what was expected.  Somebody is "
            "playing with us.",
            lock_file,
        )
        return False
    return True


def lock_pidfile_or_die(pidfile: str) -> int:
    """
    @pidfile:
        must be a writable path

    Exceptions are logged.

    Returns the PID.
    """
    pid = os.getpid()
    try:
        remove_if_stale_pidfile(pidfile)
        pid_write_file = f'{pidfile}.{pid}'
        fpid = open(pid_write_file, 'w')
        try:
            fpid.write(f"{pid}\n")
        finally:
            fpid.close()
        if not take_file_lock(pid_write_file, pidfile, f"{pid}\n"):
            sys.exit(1)
    except SystemExit:
        raise
    except Exception:
        log.exception("unable to take pidfile")
        sys.exit(1)
    return pid


def unlock_pidfile(pidfile: str) -> None:
    """
    @pidfile:
        path to the pidfile that will be removed if it is not too unsafe
    """
    try:
        pid = f"{os.getpid()}\n"
        content = open(pidfile).read(len(pid) + 1)
        if content == pid:
            os.unlink(pidfile)
        else:
            log.error("can not force unlock the pidfile of others")
    except OSError as e:
        log.error("%s: %s", type(e).__name__, e)


@contextmanager
def pidfile_context(pid_file_name: str) -> Generator[None, None, None]:
    log.debug("Locking PID file...")
    lock_pidfile_or_die(pid_file_name)
    log.debug("PID file locked.")
    try:
        yield
    finally:
        log.debug("Unlocking PID...")
        unlock_pidfile(pid_file_name)
        log.debug("PID file unlocked.")

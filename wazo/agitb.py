# Copyright 2013-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

"""More comprehensive traceback formatting for AGI in Python.

To enable this module, do:

    from agi import AGI
    import agitb
    agi = AGI()
    agitb.enable(agi)

at the top of your script.  The optional arguments to enable() are:

    agi         - the agi handle to write verbose messages to
    display     - if true (default), tracebacks are displayed on the asterisk
                  console (used with the agi option)
    logdir      - if set, tracebacks are written to files in this directory
    context     - number of lines of source code to show for each stack frame

By default, tracebacks are displayed but not saved, and the context is 5 lines.

You may want to add a logdir if you call agitb.enable() before you have
an agi.AGI() handle.

Alternatively, if you have caught an exception and want agitb to display it
for you, call agitb.handler().  The optional argument to handler() is a
3-item tuple (etype, evalue, etb) just like the value of sys.exc_info().
If you do not pass anything to handler() it will use sys.exc_info().

This script was adapted from Ka-Ping Yee's cgitb.

Modification by Proformatique:
        PyDoc of enable() corrected. (it was the same as in cgitb)
"""
from __future__ import annotations

__author__ = 'Matthew Nicholson'
# original __version__ = '0.1.0'
__version__ = "$Revision$ $Date$"

import inspect
import keyword
import linecache
import os
import pydoc
import sys
import tempfile
import time
import tokenize
import traceback
import types
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, NewType, TextIO

if TYPE_CHECKING:
    from xivo.agi import AGI

Undefined = NewType('Undefined', list[str])

__UNDEF__ = Undefined([])  # a special sentinel object


class ExceptionInfo(NamedTuple):
    type: type[BaseException]
    value: BaseException
    traceback: types.TracebackType | None


def lookup(
    name: str, frame: types.FrameType, lcals: dict[str, Any]
) -> tuple[str | None, list[str] | Undefined]:
    """Find the value for a given name in the given environment."""
    if name in lcals:
        return 'local', lcals[name]
    if name in frame.f_globals:
        return 'global', frame.f_globals[name]
    if '__builtins__' in frame.f_globals:
        builtins = frame.f_globals['__builtins__']
        if isinstance(builtins, dict):
            if name in builtins:
                return 'builtin', builtins[name]
        else:
            if hasattr(builtins, name):
                return 'builtin', getattr(builtins, name)
    return None, __UNDEF__


def scanvars(
    reader: Callable[[], str], frame: types.FrameType, lcals: dict[str, Any]
) -> list[tuple[str, str | None, list[str] | Undefined]]:
    """Scan one logical line of Python and look up values of variables used."""

    xvars: list[tuple[str, str | None, list[str] | Undefined]] = []
    lasttoken: str | None = None
    parent: list[str] | Undefined | None = None
    prefix = ''
    value: list[str] | Undefined = __UNDEF__

    for ttype, token, start, end, line in tokenize.generate_tokens(reader):
        if ttype == tokenize.NEWLINE:
            break
        if ttype == tokenize.NAME and token not in keyword.kwlist:
            if lasttoken == '.':
                if parent is not __UNDEF__:
                    value = getattr(parent, token, __UNDEF__)
                    xvars.append((prefix + token, prefix, value))
            else:
                where, value = lookup(token, frame, lcals)
                xvars.append((token, where, value))
        elif token == '.':
            prefix += (lasttoken or '') + '.'
            parent = value
        else:
            parent, prefix = None, ''
        lasttoken = token
    return xvars


def get_frames_from_traceback(
    tb: types.TracebackType | None, context: int
) -> list[str]:
    if tb is None:
        return []

    frames = []
    records = inspect.getinnerframes(tb, context)
    for frame, filen, lnum, func, lines, index in records:
        filen = filen and os.path.abspath(filen) or '?'
        args, varargs, varkw, lcals = inspect.getargvalues(frame)
        call = ''
        if func != '?':
            call = (
                'in '
                + func
                + inspect.formatargvalues(
                    args,
                    varargs,
                    varkw,
                    lcals,
                    formatvalue=lambda v: '=' + pydoc.text.repr(v),  # type: ignore[call-arg]
                )
            )

        highlight = {}

        def reader(lnum: list[int] = [lnum]) -> str:
            highlight[lnum[0]] = 1
            try:
                return linecache.getline(filen, lnum[0])
            finally:
                lnum[0] += 1

        xvars = scanvars(reader, frame, lcals)

        rows = [f' {filen} {call}']
        if index is not None:
            i = lnum - index
            for line in lines or []:
                rows.append(f'{i:5d} {line.rstrip()}')
                i += 1

        done, dump = {}, []
        for name, where, value in xvars:
            if name in done:
                continue
            done[name] = 1
            if value is not __UNDEF__:
                if where == 'global':
                    name = 'global ' + name
                elif where == 'local':
                    name = name
                else:
                    name = (where or '') + name.split('.')[-1]
                dump.append(f'{name} = {pydoc.text.repr(value)}')  # type: ignore[call-arg]
            else:
                dump.append(name + ' undefined')

        rows.append('\n'.join(dump))
        frames.append('\n{}\n'.format('\n'.join(rows)))
    return frames


def text(value: ExceptionInfo, context: int = 5) -> str:
    """Return a plain text document describing a given traceback."""
    etype: str | type[BaseException] = value[0]
    evalue, etb = value[1:]
    if isinstance(etype, type):
        etype = etype.__name__
    pyver = f'Python {sys.version.split()[0]}: {sys.executable}'
    date = time.ctime(time.time())
    head = (
        f"{str(etype)}\n{pyver}\n{date}\n"
        + '''
A problem occurred in a Python script.  Here is the sequence of
function calls leading up to the error, in the order they occurred.
'''
    )

    frames = get_frames_from_traceback(etb, context)

    exception = [f'{str(etype)}: {str(evalue)}']
    if isinstance(evalue, type):
        for name in dir(evalue):
            value_repr = pydoc.text.repr(getattr(evalue, name))  # type: ignore[call-arg]
            exception.append(f'\n{" " * 4}{name} = {value_repr}')

    return (
        head
        + ''.join(frames)
        + ''.join(exception)
        + f'''

The above is a description of an error in a Python program.  Here is
the original traceback:

{''.join(traceback.format_exception(*value))}
'''
    )


class Hook:
    """A hook to replace `sys.excepthook` that sends detailed tracebacks to
    Asterisk via agi.verbose() calls."""

    def __init__(
        self,
        display: int = 1,
        logdir: str | None = None,
        context: int = 5,
        filen: TextIO | None = None,
        agi: AGI | None = None,
    ) -> None:
        self.display = display  # send tracebacks to browser if true
        self.logdir = logdir  # log tracebacks to files if not None
        self.context = context  # number of source code lines per frame
        self.file = filen or sys.stderr  # place to send the output
        self.agi = agi

    def __call__(
        self,
        etype: type[BaseException],
        evalue: BaseException,
        etb: types.TracebackType | None,
    ) -> None:
        self.handle(ExceptionInfo(etype, evalue, etb))

    def handle(self, info: ExceptionInfo | None = None) -> None:
        if not info:
            info = ExceptionInfo(*sys.exc_info())

        try:
            doc = text(info, self.context)
        except Exception:  # just in case something goes wrong
            doc = ''.join(traceback.format_exception(*info))

        if self.display:
            if self.agi:  # print to agi
                for line in doc.split('\n'):
                    self.agi.verbose(line, 4)
            else:
                self.file.write(doc + '\n')

        if self.agi:
            self.agi.verbose('A problem occurred in a python script', 4)
        else:
            self.file.write('A problem occurred in a python script\n')

        if self.logdir is not None:
            (fd, path) = tempfile.mkstemp(suffix='.txt', dir=self.logdir)
            try:
                filen = os.fdopen(fd, 'w')
                filen.write(doc)
                filen.close()
                msg = f'{path} contains the description of this error.'
            except Exception:
                msg = f'Tried to save traceback to {path}, but failed.'

            if self.agi:
                self.agi.verbose(msg, 4)
            else:
                self.file.write(msg + '\n')

        try:
            self.file.flush()
        except Exception:
            pass


handler = Hook().handle


def enable(
    agi: AGI | None = None,
    display: int = 1,
    logdir: str | None = None,
    context: int = 5,
) -> None:
    """Install an exception handler that can send exceptions to agi.verbose

    The optional argument 'display' can be set to 0 to suppress sending the
    traceback to the Asterisk verbose logs, and 'logdir' can be set to a
    directory to cause tracebacks to be written to files there."""
    except_hook = Hook(display=display, logdir=logdir, context=context, agi=agi)
    sys.excepthook = except_hook

    global handler
    handler = except_hook.handle

# -*- coding: utf-8 -*-
# Copyright 2013-2019 The Wazo Authors  (see the AUTHORS file)
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

__author__ = 'Matthew Nicholson'
# original __version__ = '0.1.0'
__version__ = "$Revision$ $Date$"

import keyword
import inspect
import linecache
import os
import pydoc
import sys
import tempfile
import time
import traceback
import tokenize
import types


__UNDEF__ = []  # a special sentinel object


def lookup(name, frame, lcals):
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


def scanvars(reader, frame, lcals):
    """Scan one logical line of Python and look up values of variables used."""

    xvars, lasttoken, parent, prefix, value = [], None, None, '', __UNDEF__
    for ttype, token, start, end, line in tokenize.generate_tokens(
        reader
    ):  # pylint: disable-msg=W0612
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
            prefix += lasttoken + '.'
            parent = value
        else:
            parent, prefix = None, ''
        lasttoken = token
    return xvars


def text(value, context=5):
    """Return a plain text document describing a given traceback."""

    etype, evalue, etb = value
    if isinstance(etype, types.ClassType):
        etype = etype.__name__
    pyver = 'Python ' + sys.version.split()[0] + ': ' + sys.executable
    date = time.ctime(time.time())
    head = (
        "%s\n%s\n%s\n" % (str(etype), pyver, date)
        + '''
A problem occurred in a Python script.  Here is the sequence of
function calls leading up to the error, in the order they occurred.
'''
    )

    frames = []
    records = inspect.getinnerframes(etb, context)
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
                    formatvalue=lambda value: '=' + pydoc.text.repr(value),
                )
            )

        highlight = {}

        def reader(lnum=[lnum]):
            highlight[lnum[0]] = 1
            try:
                return linecache.getline(filen, lnum[0])
            finally:
                lnum[0] += 1

        xvars = scanvars(reader, frame, lcals)

        rows = [' %s %s' % (filen, call)]
        if index is not None:
            i = lnum - index
            for line in lines:
                num = '%5d ' % i
                rows.append(num + line.rstrip())
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
                    name = where + name.split('.')[-1]
                dump.append('%s = %s' % (name, pydoc.text.repr(value)))
            else:
                dump.append(name + ' undefined')

        rows.append('\n'.join(dump))
        frames.append('\n%s\n' % '\n'.join(rows))

    exception = ['%s: %s' % (str(etype), str(evalue))]
    if isinstance(evalue, types.InstanceType):
        for name in dir(evalue):
            value = pydoc.text.repr(getattr(evalue, name))
            exception.append('\n%s%s = %s' % (" " * 4, name, value))

    return (
        head
        + ''.join(frames)
        + ''.join(exception)
        + '''

The above is a description of an error in a Python program.  Here is
the original traceback:

%s
'''
        % ''.join(traceback.format_exception(etype, evalue, etb))
    )


class Hook:
    """A hook to replace sys.excepthook that sends detailed tracebacks to
    Asterisk via agi.verbose() calls."""

    def __init__(self, display=1, logdir=None, context=5, filen=None, agi=None):
        self.display = display  # send tracebacks to browser if true
        self.logdir = logdir  # log tracebacks to files if not None
        self.context = context  # number of source code lines per frame
        self.file = filen or sys.stderr  # place to send the output
        self.agi = agi

    def __call__(self, etype, evalue, etb):
        self.handle((etype, evalue, etb))

    def handle(self, info=None):
        info = info or sys.exc_info()

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
                msg = '%s contains the description of this error.' % path
            except Exception:
                msg = 'Tried to save traceback to %s, but failed.' % path

            if self.agi:
                self.agi.verbose(msg, 4)
            else:
                self.file.write(msg + '\n')

        try:
            self.file.flush()
        except Exception:
            pass


handler = Hook().handle


def enable(agi=None, display=1, logdir=None, context=5):
    """Install an exception handler that can send exceptions to agi.verbose

    The optional argument 'display' can be set to 0 to suppress sending the
    traceback to the Asterisk verbose logs, and 'logdir' can be set to a
    directory to cause tracebacks to be written to files there."""
    except_hook = Hook(display=display, logdir=logdir, context=context, agi=agi)
    sys.excepthook = except_hook

    global handler
    handler = except_hook.handle

"""
To use this library please see the example :

    agi = AGI()

    try:
        agi.appexec('backgrounder', 'demo-congrats')
    except AGIAppError:
        agi.verbose("Handled exception for missing application backgrounder")

    agi.set_variable('foo', 'bar')
    agi.get_variable('foo')

    try:
        agi.get_variable('foobar')
    except AGIAppError:
        agi.verbose("Handled exception for missing variable foobar")

    try:
        agi.database_put('foo', 'bar', 'foobar')
        agi.database_put('foo', 'baz', 'foobaz')
        agi.database_put('foo', 'bat', 'foobat')
        v = agi.database_get('foo', 'bar')
        v = agi.database_get('bar', 'foo')
        agi.database_del('foo', 'bar')
        agi.database_deltree('foo')
    except AGIDBError:
        agi.verbose("Handled exception for missing database entry bar:foo")

    agi.hangup()
"""

from __future__ import annotations

__version__ = "$Revision$ $Date$"
__license__ = """
    Copyright 2007-2023 The Wazo Authors  (see the AUTHORS file)
    Copyright (C) 2004 Karl Putland
    Upstream Original Author: Karl Putland <kputland@users.sourceforge.net>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Modifications by Proformatique from pyst-0.2:
#     - AGI._quote does escaping
#     - small optimization in AGI.send_command()
#     - DEBUG_PASSTHROUGH in AGI.get_result() so that scripts can be tested
# 	as if 200 is returned to all AGI commands.
#     - removed stderr
#     - removed double quoting from database_get()
#     - replaced a reference to old style ListType with a call to isinstance(..., list)

import sys
import pprint
import re
import signal
from types import FrameType
from typing import TextIO, Union, TYPE_CHECKING, Dict, Tuple, List

if TYPE_CHECKING:
    from typing import Literal


Digits = Union[List[Union[str, int]], str]
Result = Dict[str, Tuple[str, str]]

DEFAULT_TIMEOUT = 2000  # 2sec timeout used as default for functions that take timeouts
DEFAULT_RECORD = 20000  # 20sec record time

re_code = re.compile(r'(^\d*)\s*(.*)')
re_kv = re.compile(r'(?P<key>\w+)=(?P<value>[^\s]+)\s*(?:\((?P<data>.*)\))*')

__all__ = [
    'AGIException',
    'AGIError',
    'AGIUnknownError',
    'AGIAppError',
    'AGIHangup',
    'AGISIGHUPHangup',
    'AGISIGPIPEHangup',
    'AGIResultHangup',
    'AGIDBError',
    'AGIUsageError',
    'AGIInvalidCommand',
    'AGI',
]


class AGIException(Exception):
    pass


class AGIError(AGIException):
    pass


class AGIUnknownError(AGIError):
    pass


class AGIAppError(AGIError):
    pass


# there are several types of hangups we can detect
# they all are derived from AGIHangup
class AGIHangup(AGIAppError):
    pass


class AGISIGHUPHangup(AGIHangup):
    pass


class AGISIGPIPEHangup(AGIHangup):
    pass


class AGIResultHangup(AGIHangup):
    pass


class AGIDBError(AGIAppError):
    pass


class AGIUsageError(AGIError):
    pass


class AGIInvalidCommand(AGIError):
    pass


class AGI:
    """
    This class encapsulates communication between Asterisk and a python script.
    It handles encoding commands to Asterisk and parsing responses from
    Asterisk.
    """

    def __init__(self) -> None:
        self._got_sighup = False
        signal.signal(signal.SIGHUP, self._handle_sighup)  # handle SIGHUP
        self.env: dict[str, str] = {}
        self._get_agi_env()
        self.DEBUG_PASSTHROUGH = 0

    def _get_agi_env(self) -> None:
        while 1:
            line = sys.stdin.readline().strip()
            if line == '':
                # blank line signals end
                break
            key_data = line.split(':', 1)
            key = key_data[0].strip()
            if key:
                if len(key_data) > 1:
                    self.env[key] = key_data[1].strip()
                else:
                    self.env[key] = ""

    @staticmethod
    def _quote(string: str | int) -> str:
        return '"%s"' % (
            str(string).replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        )

    def _handle_sighup(self, _signum: int, _frame: FrameType | None) -> None:
        """Handle the SIGHUP signal"""
        # pylint: disable-msg=W0613
        self._got_sighup = True

    def test_hangup(self) -> None:
        """This function throws AGIHangup if we have received a SIGHUP"""
        if self._got_sighup:
            raise AGISIGHUPHangup("Received SIGHUP from Asterisk")

    def execute(self, command: str, *args: str | int) -> Result:
        self.test_hangup()
        try:
            self.send_command(command, *args)
            return self.get_result()
        except OSError as e:
            if e.errno == 32:
                # Broken Pipe * let us go
                raise AGISIGPIPEHangup("Received SIGPIPE")
            else:
                raise

    @staticmethod
    def send_command(command: str, *args: str | int) -> None:
        """Send a command to Asterisk"""
        command = ' '.join([command.strip()] + [str(a) for a in args]).strip() + "\n"
        sys.stdout.write(command)
        sys.stdout.flush()

    def get_result(self, stdin: TextIO = sys.stdin) -> Result:
        """Read the result of a command from Asterisk"""
        code = 0
        response = ''
        result = {'result': ('', '')}
        line = stdin.readline().strip()
        m = re_code.search(line)
        if m:
            raw_code, response = m.groups()
            if self.DEBUG_PASSTHROUGH:
                try:
                    code = int(raw_code)
                except ValueError:
                    code = 200
            else:
                code = int(raw_code)

        if code == 200:
            for key, value, data in re_kv.findall(response):
                result[key] = (value, data)

                # If user hangs up... we get 'hangup' in the data
                if data == 'hangup':
                    raise AGIResultHangup("User hung up during execution")

                if key == 'result' and value == '-1':
                    raise AGIAppError("Error executing application, or hangup")
            return result
        elif code == 510:
            raise AGIInvalidCommand(response)
        elif code == 520:
            usage = [line]
            line = stdin.readline().strip()
            while line[:3] != '520':
                usage.append(line)
                line = stdin.readline().strip()
            usage.append(line)
            raise AGIUsageError('%s\n' % '\n'.join(usage))
        else:
            raise AGIUnknownError(code, 'Unhandled code or undefined response')

    def _process_digit_list(self, digits: Digits) -> str:
        if isinstance(digits, list):
            digits = ''.join(map(str, digits))
        return self._quote(digits)

    def answer(self) -> None:
        """
        Answer channel if not already in answer state.
        """
        self.execute('ANSWER')['result'][0]  # pylint: disable-msg=W0104

    @staticmethod
    def code_to_char(code: str) -> str:
        """
        Return chr(int(code))
        Raise FastAGIError on error
        """
        if code == '0':
            return ''
        else:
            try:
                return chr(int(code))
            except (TypeError, ValueError):
                raise AGIError('Unable to convert result to char: %s' % code)

    def wait_for_digit(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Wait for up to 'timeout' milliseconds for a channel to receive a DTMF
        digit.  Return digit dialed.
        Throw AGIError on channel failure.
        """
        res = self.execute('WAIT FOR DIGIT', timeout)['result'][0]
        return self.code_to_char(res)

    def send_text(self, text: str = '') -> None:
        """
        Send the given text on a channel.  Most channels do not support the
        transmission of text.
        Throw AGIError on error/hangup.
        """
        self.execute('SEND TEXT', self._quote(text))['result'][0]

    def receive_char(self, timeout: int = DEFAULT_TIMEOUT) -> str:
        """
        Receive a character of text on a channel.  Specify timeout to be the
        maximum time to wait for input in milliseconds, or 0 for infinite.
        Most channels do not support the reception of text.
        """
        res = self.execute('RECEIVE CHAR', timeout)['result'][0]
        return self.code_to_char(res)

    def tdd_mode(self, mode: Literal['on', 'off'] = 'off') -> None:
        """
        Enable/Disable TDD transmission/reception on a channel.
        Throw AGIAppError if channel is not TDD-capable.
        """
        res = self.execute('TDD MODE', mode)['result'][0]
        if res == '0':
            raise AGIAppError('Channel %s is not TDD-capable')

    def stream_file(
        self, filename: str, escape_digits: Digits = '', sample_offset: int = 0
    ) -> str:
        """
        Send the given file, allowing playback to be interrupted by the given digits, if any.
        If sample offset is provided then the audio will seek to sample
        offset before play starts.  Return digit if one was pressed.
        Throw AGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        response = self.execute('STREAM FILE', filename, escape_digits, sample_offset)
        res = response['result'][0]
        return self.code_to_char(res)

    def control_stream_file(
        self,
        filename: str,
        escape_digits: Digits = '',
        skipms: int = 3000,
        fwd: str = '',
        rew: str = '',
        pause: str = '',
    ):
        """
        Send the given file, allowing playback to be interrupted by the given digits, if any.
        If sample offset is provided then the audio will seek to sample
        offset before play starts.  Return digit if one was pressed.
        Throw AGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        response = self.execute(
            'CONTROL STREAM FILE',
            self._quote(filename),
            escape_digits,
            self._quote(skipms),
            self._quote(fwd),
            self._quote(rew),
            self._quote(pause),
        )
        res = response['result'][0]
        return self.code_to_char(res)

    def send_image(self, filename: str) -> None:
        """
        Send the given image on a channel.  Most channels do not support the
        transmission of images.   Image names should not include extensions.
        Throw AGIError on channel failure
        """
        res = self.execute('SEND IMAGE', filename)['result'][0]
        if res != '0':
            raise AGIAppError(
                'Channel failure on channel %s' % self.env.get('agi_channel', 'UNKNOWN')
            )

    def say_digits(self, digits: Digits, escape_digits: Digits = '') -> str:
        """
        Say a given digit string, returning early if any of the given DTMF digits
        are received on the channel
        Throw AGIError on channel failure
        """
        digits = self._process_digit_list(digits)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY DIGITS', digits, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_number(self, number: Digits, escape_digits: Digits = '') -> str:
        """
        Say a given digit string, returning early if any of the given DTMF digits
        are received on the channel.
        Throw AGIError on channel failure
        """
        number = self._process_digit_list(number)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY NUMBER', number, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_alpha(self, characters: str, escape_digits: Digits = '') -> str:
        """
        Say a given character string, returning early if any of the given DTMF
        digits are received on the channel.
        Throw AGIError on channel failure
        """
        characters = self._process_digit_list(characters)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY ALPHA', characters, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_phonetic(self, characters: str, escape_digits: Digits = '') -> str:
        """
        Phonetically say a given character string, returning early if any of
        the given DTMF digits are received on the channel.
        Throw AGIError on channel failure
        """
        characters = self._process_digit_list(characters)
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY PHONETIC', characters, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_date(self, seconds: int | str, escape_digits: Digits = '') -> str:
        """
        agi.say_date(seconds, escape_digits='') --> digit
        Say a given date, returning early if any of the given DTMF digits are
        pressed.  The date should be in seconds since the UNIX Epoch
        (Jan 1, 1970 00:00:00)
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY DATE', seconds, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_time(self, seconds: int | str, escape_digits: Digits = '') -> str:
        """
        agi.say_time(seconds, escape_digits='') --> digit
        Say a given time, returning early if any of the given DTMF digits are
        pressed.  The time should be in seconds since the UNIX Epoch
        (Jan 1, 1970 00:00:00)
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute('SAY TIME', seconds, escape_digits)['result'][0]
        return self.code_to_char(res)

    def say_datetime(
        self,
        seconds: int | str,
        escape_digits: Digits = '',
        format_string: str = '',
        zone: str = '',
    ) -> str:
        """
        Say a given date in the format_string specified (see voicemail.conf), returning
        early if any of the given DTMF digits are pressed.  The date should be
        in seconds since the UNIX Epoch (Jan 1, 1970 00:00:00).
        """
        escape_digits = self._process_digit_list(escape_digits)
        if format_string:
            format_string = self._quote(format_string)
        result = self.execute(
            'SAY DATETIME', seconds, escape_digits, format_string, zone
        )
        return self.code_to_char(result['result'][0])

    def get_data(
        self, filename: str, timeout: int = DEFAULT_TIMEOUT, max_digits: int = 255
    ) -> str:
        """
        agi.get_data(filename, timeout=DEFAULT_TIMEOUT, max_digits=255) --> digits
        Stream the given file and receive dialed digits
        """
        result = self.execute('GET DATA', filename, timeout, max_digits)
        return result['result'][0]

    def get_option(
        self, filename: str, escape_digits: Digits = '', timeout: int = 0
    ) -> str:
        """
        agi.get_option(filename, escape_digits='', timeout=0) --> digit
        Send the given file, allowing playback to be interrupted by the given
        digits, if any.  escape_digits is a string '12345' or a list of
        ints [1,2,3,4,5] or strings ['1','2','3'] or mixed [1,'2',3,'4']
        Return digit if one was pressed.
        Throw AGIError if the channel was disconnected.  Remember, the file
        extension must not be included in the filename.
        """
        escape_digits = self._process_digit_list(escape_digits)
        if timeout:
            response = self.execute('GET OPTION', filename, escape_digits, timeout)
        else:
            response = self.execute('GET OPTION', filename, escape_digits)

        res = response['result'][0]
        return self.code_to_char(res)

    def set_context(self, context: str) -> None:
        """
        Set the context for continuation upon exiting the application.
        No error appears to be produced.  Do not set exten or priority.

        The caller must specify a valid context.
        """
        self.execute('SET CONTEXT', context)

    def set_extension(self, extension: str) -> None:
        """
        Set the extension for continuation upon exiting the application.
        No error appears to be produced.  Do not set context or priority.

        The caller must specify a valid extension.
        """
        self.execute('SET EXTENSION', extension)

    def set_priority(self, priority: int | str) -> None:
        """
        Set the priority for continuation upon exiting the application.
        No error appears to be produced.  Do not set exten or context.

        The caller must specify a valid priority.
        """
        self.execute('set priority', priority)

    def goto_on_exit(
        self, context: str = '', extension: str = '', priority: str | int = ''
    ) -> None:
        context = context or self.env['agi_context']
        extension = extension or self.env['agi_extension']
        priority = priority or self.env['agi_priority']
        self.set_context(context)
        self.set_extension(extension)
        self.set_priority(priority)

    def record_file(
        self,
        filename: str,
        file_format: str = 'gsm',
        escape_digits: Digits = '#',
        timeout: int = DEFAULT_RECORD,
        offset: int = 0,
        beep: str = 'beep',
    ) -> str:
        """
        Record to a file until a given dtmf digit in the sequence is received.
        The file_format will specify what kind of file will be recorded.  The
        timeout is the maximum record time in milliseconds, or -1 for no
        timeout.  Offset samples is optional, and if provided will seek to the
        offset without exceeding the end of the file.
        """
        escape_digits = self._process_digit_list(escape_digits)
        res = self.execute(
            'RECORD FILE',
            self._quote(filename),
            file_format,
            escape_digits,
            timeout,
            offset,
            beep,
        )['result'][0]
        return self.code_to_char(res)

    def set_autohangup(self, secs: int | str) -> None:
        """
        Cause the channel to automatically hangup at <time> seconds in the
        future.  Of course, it can be hung up before then as well. Setting to
        0 will cause the auto-hangup feature to be disabled on this channel.
        """
        self.execute('SET AUTOHANGUP', secs)

    def hangup(self, channel: str = '') -> None:
        """
        Hang up the specified channel.
        If no channel name is given, hang up the current channel
        """
        self.execute('HANGUP', channel)

    def appexec(self, application: str, options: str = '') -> str:
        """
        Execute <application> with given <options>.
        Return what is returned by the application, or -2 on failure to find
        application
        """
        result = self.execute('EXEC', application, self._quote(options))
        res = result['result'][0]
        if res == '-2':
            raise AGIAppError('Unable to find application: %s' % application)
        return res

    def set_callerid(self, number: str) -> None:
        """
        Change the callerid of the current channel.
        """
        self.execute('SET CALLERID', number)

    def channel_status(self, channel: str = '') -> int:
        """
        agi.channel_status(channel='') --> int
        Return the status of the specified channel.  If no channel name is
        given then return the status of the current channel.

        Return values:
        0 Channel is down and available
        1 Channel is down, but reserved
        2 Channel is off hook
        3 Digits (or equivalent) have been dialed
        4 Line is ringing
        5 Remote end is ringing
        6 Line is up
        7 Line is busy
        """
        try:
            result = self.execute('CHANNEL STATUS', channel)
        except AGIHangup:
            raise
        except AGIAppError:
            result = {'result': ('-1', '')}

        return int(result['result'][0])

    def set_variable(self, name: str, value: str | int):
        """
        Set a channel variable.
        """
        self.execute('SET VARIABLE', self._quote(name), self._quote(value))

    def get_variable(self, name: str) -> str:
        """
        Get a channel variable.

        This function returns the value of the indicated channel variable.  If
        the variable is not set, an empty string is returned.
        """
        try:
            result = self.execute('GET VARIABLE', self._quote(name))
        except AGIResultHangup:
            result = {'result': ('1', 'hangup')}

        return result['result'][1]

    def get_full_variable(self, name: str, channel: str | None = None) -> str:
        """
        Get a channel variable.

        This function returns the value of the indicated channel variable.
        If the variable is not set, an empty string is returned.
        """
        try:
            if channel:
                result = self.execute(
                    'GET FULL VARIABLE', self._quote(name), self._quote(channel)
                )
            else:
                result = self.execute('GET FULL VARIABLE', self._quote(name))

        except AGIResultHangup:
            result = {'result': ('1', 'hangup')}

        return result['result'][1]

    def verbose(self, message: str, level: int = 1) -> None:
        """
        Send <message> to the console via verbose message system.
        <level> is the the verbose level (1-4)
        """
        self.execute('VERBOSE', self._quote(message), level)

    def database_get(self, family: str, key: str) -> str:
        """
        Retrieve an entry in the Asterisk database for a given family and key.
        Return 0 if <key> is not set.  Return 1 if <key> is set and return the
        variable in parentheses
        example return code: 200 result=1 (testvariable)
        """
        result = self.execute('DATABASE GET', self._quote(family), self._quote(key))
        res, value = result['result']
        if res == '0':
            raise AGIDBError(f'Key not found in database: family={family}, key={key}')
        if res == '1':
            return value
        raise AGIError(
            f'Unknown exception for : family={family}, key={key}, result={pprint.pformat(result)}'
        )

    def database_put(self, family: str, key: str, value: str) -> None:
        """
        Add or update an entry in the Asterisk database for a given family,
        key, and value.
        """
        result = self.execute(
            'DATABASE PUT', self._quote(family), self._quote(key), self._quote(value)
        )
        res, value = result['result']
        if res == '0':
            raise AGIDBError(
                f'Unable to put value in database: family={family}, key={key}, value={value}'
            )

    def database_del(self, family: str, key: str) -> None:
        """
        Delete an entry in the Asterisk database for a given family and key.
        """
        result = self.execute('DATABASE DEL', self._quote(family), self._quote(key))
        res, _ = result['result']  # pylint: disable-msg=W0612
        if res == '0':
            raise AGIDBError(
                f'Unable to delete from database: family={family}, key={key}'
            )

    def database_deltree(self, family: str, key: str = '') -> None:
        """
        Delete a family or specific keytree with in a family in the Asterisk
        database.
        """
        result = self.execute('DATABASE DELTREE', self._quote(family), self._quote(key))
        res, _ = result['result']  # pylint: disable-msg=W0612
        if res == '0':
            raise AGIDBError(
                f'Unable to delete tree from database: family={family}, key={key}'
            )

    def noop(self) -> None:
        """
        Do nothing
        """
        self.execute('NOOP')

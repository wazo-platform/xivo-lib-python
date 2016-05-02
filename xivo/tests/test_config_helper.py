# -*- coding: utf-8 -*-

# Copyright (C) 2014-2016 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from operator import itemgetter
import os.path
import random
import string
import tempfile
import unittest

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import contains
from hamcrest import equal_to
from hamcrest import has_entry
from hamcrest import is_not
from hamcrest import raises
from mock import patch
from mock import Mock
from mock import ANY
from yaml.parser import ParserError

from ..config_helper import ConfigParser
from ..config_helper import ErrorHandler
from ..config_helper import PrintErrorHandler
from ..config_helper import get_xivo_uuid
from ..config_helper import set_xivo_uuid
from ..config_helper import UUIDNotFound

XIVO_UUID = '08c56466-8f29-45c7-9856-92bf1ba89b82'


def _none_existent_filename():
    while True:
        filename = '{}-{}'.format(
            os.path.dirname(__file__),
            ''.join(random.choice(string.ascii_lowercase) for _ in range(3)))
        if not os.path.exists(filename):
            return filename


def _new_tmp_dir():
    while True:
        suffix = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))
        dirname = os.path.join(tempfile.gettempdir(), suffix)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
            tempfile.tempdir = dirname
            break
    return dirname


class TestPrintErrorHandler(unittest.TestCase):

    def setUp(self):
        self.error_handler = PrintErrorHandler()
        self.name = 'foobar'
        self.e = EnvironmentError((42, 'Bah'))

    @patch('six.moves.builtins.print')
    def test_on_parse_config_file_env_error(self, mocked_print):
        self.error_handler.on_parse_config_file_env_error(self.name, self.e)

        printed_message = mocked_print.call_args_list[0]
        assert_that(printed_message.startswith('Could not read config file'))

    @patch('six.moves.builtins.print')
    def test_on_parse_config_dir_env_error(self, mocked_print):
        self.error_handler.on_parse_config_dir_env_error(self.name, self.e)

        printed_message = mocked_print.call_args_list[0]
        assert_that(printed_message.startswith('Could not read config dir'))


class TestParseConfigFile(unittest.TestCase):

    def setUp(self):
        self.error_handler = Mock(ErrorHandler)
        self.parser = ConfigParser(self.error_handler)

    def test_exec_tag(self):
        file_to_read = """\
        foo: bar
        bar: baz
        """
        other_file = tempfile.NamedTemporaryFile('w+t')
        other_file.write(file_to_read)
        other_file.seek(0)

        config_file_content = """\
        !exec
        command: cat {}
        """.format(other_file.name)
        config_file = tempfile.NamedTemporaryFile('w+t')
        config_file.write(config_file_content)
        config_file.seek(0)

        result = self.parser.parse_config_file(config_file.name)

        assert_that(result, equal_to({'foo': 'bar',
                                      'bar': 'baz'}))

    def test_exec_tag_command_not_found(self):
        config_file_content = """\
        !exec
        command: pouelle /tmp/test
        """
        config_file = tempfile.NamedTemporaryFile('w+t')
        config_file.write(config_file_content)
        config_file.seek(0)

        result = self.parser.parse_config_file(config_file.name)

        assert_that(result, equal_to({}))

    def test_exec_tag_empty_result(self):
        file_to_read = """\
        """
        other_file = tempfile.NamedTemporaryFile('w+t')
        other_file.write(file_to_read)
        other_file.seek(0)

        config_file_content = """\
        !exec
        command: cat {}
        """.format(other_file.name)
        config_file = tempfile.NamedTemporaryFile('w+t')
        config_file.write(config_file_content)
        config_file.seek(0)

        result = self.parser.parse_config_file(config_file.name)

        assert_that(result, equal_to({}))

    def test_empty_dict_when_no_file_or_directory(self):
        no_such_file = _none_existent_filename()

        result = self.parser.parse_config_file(no_such_file)

        assert_that(result, equal_to({}))
        self.error_handler.on_parse_config_file_env_error.assert_called_once_with(no_such_file, ANY)

    def test_invalid_yaml_raises(self):
        content = """ \
        test: [:one :two :3]'
        """

        f = tempfile.NamedTemporaryFile('w+t')
        f.writelines(content.split('\n'))
        f.seek(0)

        self.assertRaises(ParserError, self.parser.parse_config_file, f.name)

    def test_with_valid_yaml(self):
        content = """ \
        test: value
        """

        f = tempfile.NamedTemporaryFile('w+t')
        f.writelines(content.split('\n'))
        f.seek(0)

        res = self.parser.parse_config_file(f.name)

        assert_that(res, equal_to({'test': 'value'}))

    def test_empty_yaml_file(self):
        f = tempfile.NamedTemporaryFile()
        f.writelines('')
        f.seek(0)

        res = self.parser.parse_config_file(f.name)

        assert_that(res, equal_to({}))


class TestParseConfigDir(unittest.TestCase):

    def setUp(self):
        self.error_handler = Mock(ErrorHandler)
        self.parser = ConfigParser(self.error_handler)

    def test_no_such_directory(self):
        dirname = _none_existent_filename()

        result = self.parser.parse_config_dir(dirname)

        assert_that(result, contains())
        self.error_handler.on_parse_config_dir_env_error.assert_called_once_with(dirname, ANY)

    def test_with_only_valid_configs(self):
        dirname = _new_tmp_dir()

        f1 = tempfile.NamedTemporaryFile('w+t', suffix='.yml')
        f1.writelines('test: one')
        f1.seek(0)
        f2 = tempfile.NamedTemporaryFile('w+t', suffix='.yml')
        f2.writelines('test: two')
        f2.seek(0)

        res = self.parser.parse_config_dir(dirname)

        sorted_files = sorted([{'file': f1.name,
                                'content': {'test': 'one'}},
                               {'file': f2.name,
                                'content': {'test': 'two'}}], key=itemgetter('file'))
        expected = [entry['content'] for entry in sorted_files]
        assert_that(res, contains(*expected))

    def test_that_valid_configs_are_returned_when_one_fails(self):
        dirname = _new_tmp_dir()

        f1 = tempfile.NamedTemporaryFile('w+t', suffix='.yml')
        f1.writelines('test: one')
        f1.seek(0)
        f2 = tempfile.NamedTemporaryFile('w+t', suffix='.yml')
        f2.writelines('test: [:one :two]')
        f2.seek(0)

        res = self.parser.parse_config_dir(dirname)

        assert_that(res, contains({'test': 'one'}))
        self.error_handler.on_parse_config_dir_parse_exception.assert_called_once_with(os.path.basename(f2.name), ANY)

    def test_ignore_dot_files(self):
        dirname = _new_tmp_dir()
        filename = os.path.join(dirname, '.foobar')

        with open(filename, 'w') as fobj:
            fobj.write('test: one\n')

        try:
            res = self.parser.parse_config_dir(dirname)

            assert_that(res, is_not(contains({'test': 'one'})))
        finally:
            os.unlink(filename)

    def test_ignore_not_yaml_files(self):
        dirname = _new_tmp_dir()
        filename = os.path.join(dirname, 'foobar.yml.dpkg-old')

        with open(filename, 'w') as fobj:
            fobj.write('test: two\n')

        try:
            res = self.parser.parse_config_dir(dirname)

            assert_that(res, is_not(contains({'test': 'two'})))
        finally:
            os.unlink(filename)


class TestReadConfigFileHierarchy(unittest.TestCase):

    def setUp(self):
        self.error_handler = Mock(ErrorHandler)
        self.parser = ConfigParser(self.error_handler)

    def test_that_the_main_config_file_is_read(self):
        self.parser.parse_config_file = Mock()
        self.parser.parse_config_file.return_value = {'extra_config_files': '/path/to/extra',
                                                      'sentinel': 'from_main_file',
                                                      'main_file_only': True}
        self.parser.parse_config_dir = Mock()
        self.parser.parse_config_dir.return_value = [{'sentinel': 'from_extra_config'}]
        cli_and_default_config = {
            'config_file': '/path/to/config.yml',
            'extra_config_files': '/original/path/to/extra',
            'sentinel': 'from_default',
        }

        config = self.parser.read_config_file_hierarchy(cli_and_default_config)

        self.parser.parse_config_file.assert_called_once_with('/path/to/config.yml')
        self.parser.parse_config_dir.assert_called_once_with('/path/to/extra')

        assert_that(config['sentinel'], equal_to('from_extra_config'))
        assert_that(config['main_file_only'], equal_to(True))


class TestGetXiVOUUID(unittest.TestCase):

    @patch('xivo.config_helper.os.getenv', return_value=False)
    def test_given_no_uuid_then_raise_error(self, getenv):
        assert_that(calling(get_xivo_uuid).with_args(Mock()),
                    raises(UUIDNotFound))

    @patch('xivo.config_helper.os.getenv', return_value=XIVO_UUID)
    def test_given_uuid_then_return_uuid(self, getenv):
        result = get_xivo_uuid(Mock())

        assert_that(result, equal_to(XIVO_UUID))


class TestSetXiVOUUID(unittest.TestCase):
    @patch('xivo.config_helper.os.getenv', return_value=False)
    def test_given_no_uuid_then_raise_error(self, getenv):
        assert_that(calling(set_xivo_uuid).with_args({}, Mock()),
                    raises(UUIDNotFound))

    @patch('xivo.config_helper.os.getenv', return_value=XIVO_UUID)
    def test_given_uuid_then_set_uuid(self, getenv):
        config = {}
        set_xivo_uuid(config, Mock())

        assert_that(config, has_entry('uuid', XIVO_UUID))

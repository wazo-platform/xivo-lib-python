# -*- coding: utf-8 -*-

# Copyright (C) 2014 Avencall
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

from mock import patch, sentinel as s
from unittest import TestCase

from xivo import wsgi


@patch('signal.signal')
@patch('xivo.wsgi.WSGIServer')
class TestWSGI(TestCase):

    def test_run_starts_wsgi_server_with_app(self, wsgi_init, _signal):
        server = wsgi_init.return_value

        wsgi.run(s.app)

        wsgi_init.assert_called_once_with(s.app)
        server.run.assert_called_once_with()

    def test_run_passes_kwargs_to_wsgi_server(self, wsgi_init, _signal):
        kwargs = {
            'bindAddress': s.socket,
            'debug': True
        }

        wsgi.run(s.app, **kwargs)

        wsgi_init.assert_called_once_with(s.app, **kwargs)

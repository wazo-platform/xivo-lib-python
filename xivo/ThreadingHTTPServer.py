# -*- coding: utf8 -*-
"""Threaded HTTP Server

Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)

"""

__version__ = "$Revision$ $Date$"
__license__ = """
    Copyright (c) 2001, 2002, 2003, 2004 Python Software Foundation;
    Copyright 2007-2019 The Wazo Authors  (see the AUTHORS file)
                                        All Rights Reserved

    Under PSF LICENSE AGREEMENT FOR PYTHON
    See the following URI for the full license:
        http://www.python.org/download/releases/2.4.4/license/
"""

from six.moves import socketserver


class ThreadingHTTPServer(socketserver.ThreadingTCPServer):
    """
    Same as HTTPServer, but derives from ThreadingTCPServer instead of
    TCPServer so that each http handler instance runs in its own thread.
    """

    allow_reuse_address = 1  # Seems to make sense in testing environment

    def server_bind(self):
        """Override server_bind to store the server name."""
        socketserver.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socketserver.socket.getfqdn(host)
        self.server_port = port


__all__ = ['ThreadingHTTPServer']

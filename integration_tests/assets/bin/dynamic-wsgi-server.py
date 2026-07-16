#!/usr/bin/env python3
# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import logging
from time import sleep

from flask import Flask
from flask_restful import Api, Resource

from xivo import wsgi

logging.basicConfig(level=logging.INFO)

app = Flask('dynamic-wsgi-server')
api = Api(app)


class SlowResource(Resource):
    def get(self) -> str:
        sleep(3)
        return 'done'


def main() -> None:
    api.add_resource(SlowResource, '/slow')
    bind_addr = ('0.0.0.0', 8080)
    wsgi_app = wsgi.WSGIPathInfoDispatcher({'/': app})
    server = wsgi.DynamicWSGIServer(
        bind_addr,
        wsgi_app,
        server_name='dynamic-wsgi-server',
        numthreads=2,
        max=6,
        minspare=1,
        maxspare=2,
        resize_interval=1.0,
    )
    server.start()


if __name__ == '__main__':
    main()

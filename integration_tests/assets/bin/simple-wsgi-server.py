#!/usr/bin/env python3
# Copyright 2018-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from time import sleep

from flask import Flask
from flask_restful import Api, Resource

from xivo import wsgi

app = Flask('simple-wsgi-server')
api = Api(app)


class BasicResource(Resource):
    def get(self) -> int:
        sleep(200)
        return 200


def main() -> None:
    api.add_resource(BasicResource, '/resource')
    bind_addr = ('0.0.0.0', 8080)
    wsgi_app = wsgi.WSGIPathInfoDispatcher({'/': app})
    server = wsgi.WSGIServer(
        bind_addr,
        wsgi_app,
        server_name='simple-wsgi-server',
        numthreads=1,
    )
    server.start()


if __name__ == '__main__':
    main()

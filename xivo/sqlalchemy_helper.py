# Copyright 2018-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy.pool import Pool


def handle_db_restart():
    # http://stackoverflow.com/questions/34828113/flask-sqlalchemy-losing-connection-after-restarting-of-db-server
    @event.listens_for(Pool, "checkout")
    def ping_connection(dbapi_connection, connection_record, connection_proxy):
        del connection_record
        del connection_proxy

        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT 1")
        except BaseException:
            # raise DisconnectionError - pool will try
            # connecting again up to three times before raising.
            raise exc.DisconnectionError()
        cursor.close()

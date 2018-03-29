# -*- coding: utf-8 -*-
# Copyright (C) 2016 Avencall
# SPDX-License-Identifier: GPL-3.0+


def db_user_exists(cursor, user):
    cursor.execute("""SELECT 1 FROM pg_roles WHERE rolname=%s""", (user,))
    row = cursor.fetchone()
    return row and row[0] == 1


def create_db_user(cursor, user, password):
    sql = 'CREATE ROLE "{}" WITH LOGIN PASSWORD %s'.format(user)
    cursor.execute(sql, (password,))


def db_exists(cursor, name):
    cursor.execute("""SELECT count(datname) FROM pg_catalog.pg_database WHERE datname=%s""", (name,))
    row = cursor.fetchone()
    return row and row[0] > 0


def create_db(cursor, db_name, owner):
    sql = """CREATE DATABASE "{}" WITH OWNER "{}" ENCODING 'UTF8'""".format(db_name, owner)
    cursor.execute(sql)


def create_db_extensions(cursor, extensions):
    sql = 'CREATE EXTENSION IF NOT EXISTS "{}"'
    for extension in extensions:
        cursor.execute(sql.format(extension))

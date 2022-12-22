# Copyright 2016-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later


def db_user_exists(cursor, user):
    cursor.execute("""SELECT 1 FROM pg_roles WHERE rolname=%s""", (user,))
    row = cursor.fetchone()
    return row and row[0] == 1


def create_db_user(cursor, user, password):
    sql = f'CREATE ROLE "{user}" WITH LOGIN PASSWORD %s'
    cursor.execute(sql, (password,))


def db_exists(cursor, name):
    cursor.execute(
        """SELECT count(datname) FROM pg_catalog.pg_database WHERE datname=%s""",
        (name,),
    )
    row = cursor.fetchone()
    return row and row[0] > 0


def create_db(cursor, db_name, owner):
    sql = f"""CREATE DATABASE "{db_name}" WITH OWNER "{owner}" ENCODING 'UTF8'"""
    cursor.execute(sql)


def create_db_extensions(cursor, extensions):
    sql = 'CREATE EXTENSION IF NOT EXISTS "{}"'
    for extension in extensions:
        cursor.execute(sql.format(extension))

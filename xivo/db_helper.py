# -*- coding: utf-8 -*-

# Copyright (C) 2016 Avencall
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

# Copyright 2016-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2


def db_user_exists(cursor: psycopg2.cursor, user: str) -> bool:
    cursor.execute("""SELECT 1 FROM pg_roles WHERE rolname=%s""", (user,))
    row = cursor.fetchone()
    return bool(row and row[0] == 1)


def create_db_user(cursor: psycopg2.cursor, user: str, password: str) -> None:
    sql = f'CREATE ROLE "{user}" WITH LOGIN PASSWORD %s'
    cursor.execute(sql, (password,))


def db_exists(cursor: psycopg2.cursor, name: str) -> bool:
    cursor.execute(
        """SELECT count(datname) FROM pg_catalog.pg_database WHERE datname=%s""",
        (name,),
    )
    row = cursor.fetchone()
    return bool(row and row[0] > 0)


def create_db(cursor: psycopg2.cursor, db_name: str, owner: str) -> None:
    sql = f"""CREATE DATABASE "{db_name}" WITH OWNER "{owner}" ENCODING 'UTF8'"""
    cursor.execute(sql)


def create_db_extensions(cursor: psycopg2.cursor, extensions: Sequence[str]) -> None:
    sql = 'CREATE EXTENSION IF NOT EXISTS "{}"'
    for extension in extensions:
        cursor.execute(sql.format(extension))

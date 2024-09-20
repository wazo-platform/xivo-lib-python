# Copyright 2014-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import get_type_hints

from xivo.typing_utils import JSON


class TestAnnotations:
    # the relevant test coverage relies on the mypy linter checking those annotations,
    # not on runtime tests
    a: JSON = dict(name="hello")
    b: JSON = 2
    c: JSON = [1, 2, 3]
    d: JSON = "hello"
    e: JSON = True
    f: JSON = 3.14
    g: JSON = None
    h: JSON = [a, b, c, d, e, f, g]
    i: JSON = {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "g": g}

    def test_annotations(self):
        annots = get_type_hints(self.__class__)
        assert all(t is JSON for t in annots.values())

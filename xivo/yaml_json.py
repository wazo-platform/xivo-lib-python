# -*- coding: utf-8 -*-
# Copyright (C) 2008-2015 Avencall
# SPDX-License-Identifier: GPL-3.0+


def stringify_keys(obj):
    """
    In YAML, it is possible to code a dictionary with integers keys.
    In JSON, it is not.
    This function returns a *deep* copy of @obj except that integer keys are
    replaced by their decimal representation, ex:

    >>> stringify_keys([{'vs_0001': {0: 'static_0001'}}, 12])
    [{'vs_0001': {'0': 'static_0001'}}, 12]
    """
    if isinstance(obj, list):
        return map(stringify_keys, obj)
    elif isinstance(obj, dict):
        return dict(((str(k), stringify_keys(v)) for k, v in obj.iteritems()))
    else:
        return obj


if __name__ == '__main__':
    import doctest
    doctest.testmod()

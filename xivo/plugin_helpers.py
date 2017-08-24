# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging

from six import iteritems
from stevedore.named import NamedExtensionManager

logger = logging.getLogger(__name__)


def enabled_names(plugins_dict):
    return [name for name, enabled in iteritems(plugins_dict) if enabled]


def on_load_failure(_, entrypoint, exception):
    logger.exception('There is an error with this module: %s', entrypoint)


def load_plugin(ext, *load_args, **load_kwargs):
    logger.debug('Loading dynamic plugin: %s', ext.name)
    ext.obj.load(*load_args, **load_kwargs)


def load(namespace, names, dependencies):
    names = enabled_names(names)
    logger.debug('Enabled plugins: %s', names)
    manager = NamedExtensionManager(
        namespace,
        names,
        name_order=True,
        on_load_failure_callback=on_load_failure,
        invoke_on_load=True
    )

    manager.map(load_plugin, dependencies)

    return manager

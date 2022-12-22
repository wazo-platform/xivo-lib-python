# Copyright 2017-2022 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from collections import OrderedDict
from functools import partial
from stevedore.named import NamedExtensionManager

logger = logging.getLogger(__name__)


def enabled_names(plugins_dict):
    return [name for name, enabled in plugins_dict.items() if enabled]


def on_load_failure(manager, entrypoint, exception):
    logger.exception(
        'Error in plugin namespace "%s" when loading module: "%s"',
        manager.namespace,
        entrypoint,
    )


def on_missing_entrypoints(namespace, missing_names):
    logger.error(
        'Error in plugin namespace "%s": the entrypoint is missing for plugins: %s',
        namespace,
        missing_names,
    )


def load_plugin(ext, *load_args, **load_kwargs):
    logger.debug('Loading dynamic plugin: %s', ext.name)
    return ext.obj.load(*load_args, **load_kwargs)


def load(namespace, names, dependencies):
    names = enabled_names(names)
    logger.debug('Enabled plugins for namespace "%s": %s', namespace, names)
    if not names:
        logger.info('no enabled plugins')
        return

    manager = NamedExtensionManager(
        namespace,
        names,
        name_order=True,
        on_load_failure_callback=on_load_failure,
        on_missing_entrypoints_callback=partial(on_missing_entrypoints, namespace),
        invoke_on_load=True,
    )

    manager.map(load_plugin, dependencies)

    return manager


def from_list(enabled_names):
    return OrderedDict((name, True) for name in enabled_names)

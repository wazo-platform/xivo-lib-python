# Copyright 2017-2023 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
from abc import abstractmethod
from collections.abc import Sequence
from functools import partial
from typing import Any, Protocol, TypeVar

from stevedore.extension import Extension
from stevedore.named import NamedExtensionManager

logger = logging.getLogger(__name__)

Self = TypeVar('Self', bound="Plugin")


class Plugin(Protocol):
    @abstractmethod
    def load(self: Self, dependencies: dict[str, Any]) -> Self:
        ...


def enabled_names(plugins_dict: dict[str, bool]) -> list[str]:
    return [name for name, enabled in plugins_dict.items() if enabled]


def on_load_failure(
    manager: NamedExtensionManager, entrypoint: str, exception: Exception
) -> None:
    logger.exception(
        'Error in plugin namespace "%s" when loading module: "%s"',
        manager.namespace,
        entrypoint,
    )


def on_missing_entrypoints(namespace: str, missing_names: set[str]) -> None:
    logger.error(
        'Error in plugin namespace "%s": the entrypoint is missing for plugins: %s',
        namespace,
        missing_names,
    )


def load_plugin(ext: Extension, *load_args: Any, **load_kwargs: Any) -> Plugin:
    logger.debug('Loading dynamic plugin: %s', ext.name)
    return ext.obj.load(*load_args, **load_kwargs)


def load(
    namespace: str, names: dict[str, bool], dependencies: dict[str, Any]
) -> NamedExtensionManager | None:
    enabled_plugins = enabled_names(names)
    logger.debug('Enabled plugins for namespace "%s": %s', namespace, enabled_plugins)
    if not enabled_plugins:
        logger.info('no enabled plugins')
        return None

    manager = NamedExtensionManager(
        namespace,
        enabled_plugins,
        name_order=True,
        on_load_failure_callback=on_load_failure,
        on_missing_entrypoints_callback=partial(on_missing_entrypoints, namespace),
        invoke_on_load=True,
    )

    manager.map(load_plugin, dependencies)

    return manager


def from_list(enabled_names: Sequence[str]) -> dict[str, bool]:
    return {name: True for name in enabled_names}

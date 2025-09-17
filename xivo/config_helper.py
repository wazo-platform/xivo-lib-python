# Copyright 2014-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Generator
from functools import partial
from logging import Logger
from typing import Any

import yaml

from .chain_map import AccumulatingListChainMap, ChainMap


class _YAMLExecLoader(yaml.SafeLoader):
    pass


class _YAMLExecTag(yaml.YAMLObject):
    yaml_tag = '!exec'
    yaml_loader = _YAMLExecLoader

    @classmethod
    def from_yaml(
        cls, loader: yaml.SafeLoader | yaml.Loader | yaml.BaseLoader, node: yaml.Node
    ) -> dict[str, Any] | None:
        with open(os.devnull) as devnull:
            for key, value in node.value:
                if key.value == 'command':
                    return yaml.safe_load(
                        subprocess.check_output(value.value.split(' '), stderr=devnull)
                    )


class ErrorHandler:
    def on_parse_config_file_env_error(
        self, config_file_name: str, e: Exception
    ) -> None:
        pass

    def on_parse_config_dir_env_error(self, directory_name: str, e: Exception) -> None:
        pass

    def on_parse_config_dir_parse_exception(self, filename: str, e: Exception) -> None:
        pass


class PrintErrorHandler(ErrorHandler):
    def on_parse_config_file_env_error(
        self, config_file_name: str, e: Exception
    ) -> None:
        print(
            f'Could not read config file {config_file_name}: {e}',
            file=sys.stderr,
        )

    def on_parse_config_dir_env_error(self, directory_name: str, e: Exception) -> None:
        print(
            f'Could not read config dir {directory_name}: {e}',
            file=sys.stderr,
        )

    def on_parse_config_dir_parse_exception(self, filename: str, e: Exception) -> None:
        print(f'Could not read config file {filename}: {e}', file=sys.stderr)


class ConfigParser:
    def __init__(self, error_handler: ErrorHandler = PrintErrorHandler()) -> None:
        self._error_handler = error_handler

    def parse_config_file(self, config_file_name: str) -> dict[str, Any]:
        try:
            with open(config_file_name) as config_file:
                data = yaml.load(config_file, Loader=_YAMLExecLoader)
            return data if data else {}
        except OSError as e:
            self._error_handler.on_parse_config_file_env_error(config_file_name, e)
            return {}

    def parse_config_dir(self, directory_name: str) -> list[dict[str, Any]]:
        """
        Reads all files in directory_name and returns a list of dictionaries containing
        the parsed yaml content from these files.

        Invalid files are ignored and a message is sent to stderr
        """
        full_path = partial(os.path.join, directory_name)
        try:
            extra_config_filenames = os.listdir(directory_name)
        except OSError as e:
            self._error_handler.on_parse_config_dir_env_error(directory_name, e)
            return []

        def _config_generator() -> Generator[dict[str, Any]]:
            for filename in sorted(extra_config_filenames):
                if filename.startswith('.'):
                    continue
                if not filename.endswith('.yml'):
                    continue

                try:
                    yield self.parse_config_file(full_path(filename))
                except Exception as e:
                    self._error_handler.on_parse_config_dir_parse_exception(filename, e)

        return list(_config_generator())

    def read_config_file_hierarchy(
        self,
        original_config: dict[str, Any],
        config_file_key: str = 'config_file',
        extra_config_dir_key: str = 'extra_config_files',
    ) -> ChainMap:
        """
        Read a config file and an extra config directory, then return a dictionary
        containing the config read, aggregated by the following priority:

        1. extra config directory (in alphabetical order)
        2. config file

        The config file name is taken from original_config[config_file_key].
        The extra config directory name is taken from
        config_file[extra_config_dir_key] else original_config[extra_config_dir_key].
        """

        main_config_filename = original_config[config_file_key]
        main_config = self.parse_config_file(main_config_filename)
        extra_config_file_directory = ChainMap(main_config, original_config)[
            extra_config_dir_key
        ]
        configs = self.parse_config_dir(extra_config_file_directory)
        configs.append(main_config)

        return ChainMap(*configs)

    def read_config_file_hierarchy_accumulating_list(
        self, original_config: dict[str, Any]
    ) -> AccumulatingListChainMap:
        main_config_filename = original_config['config_file']
        main_config = self.parse_config_file(main_config_filename)
        extra_config_file_directory = AccumulatingListChainMap(
            main_config, original_config
        )['extra_config_files']
        configs = self.parse_config_dir(extra_config_file_directory)
        configs.append(main_config)

        return AccumulatingListChainMap(*configs)


class UUIDNotFound(RuntimeError):
    def __init__(self) -> None:
        super().__init__('XIVO_UUID environment variable is not set')


def get_xivo_uuid(logger: Logger) -> str:
    xivo_uuid = os.getenv('XIVO_UUID')
    if not xivo_uuid:
        logger.error('undefined environment variable XIVO_UUID')
        raise UUIDNotFound()
    return xivo_uuid


def set_xivo_uuid(config: dict[str, Any], logger: Logger) -> None:
    config['uuid'] = get_xivo_uuid(logger)


_config_parser = ConfigParser()

parse_config_file = _config_parser.parse_config_file
parse_config_dir = _config_parser.parse_config_dir
read_config_file_hierarchy = _config_parser.read_config_file_hierarchy
read_config_file_hierarchy_accumulating_list = (
    _config_parser.read_config_file_hierarchy_accumulating_list
)

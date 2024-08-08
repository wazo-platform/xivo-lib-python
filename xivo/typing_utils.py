from __future__ import annotations

from typing import Union

from typing_extensions import TypeAlias

JSON: TypeAlias = Union[str, int, float, bool, None, list['JSON'], dict[str, 'JSON']]

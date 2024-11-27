# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from typing import NamedTuple

from conda_store_server.plugins.types.lock import LockPlugin


class TypeLockPlugin(NamedTuple):
    """
    Return type to use when defining a conda store lock plugin hook.

    :param name: plugin name (e.g., ``my-nice-lock-plugin``).
    :param synopsis: a brief description of the plugin
    :param backend: Type that will be instantiated as the lock backend.
    """

    name: str
    synopsis: str
    backend: type[LockPlugin]

# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pluggy

from collections.abc import Iterable
from conda_store_server.plugins.types import LockPlugin

spec_name = "conda-store-server"

hookspec = pluggy.HookspecMarker(spec_name)

hookimpl = pluggy.HookimplMarker(spec_name)


class CondaStoreSpecs:
    """Conda Store hookspecs"""

    @hookspec
    def lock_plugins(self) -> Iterable[LockPlugin]:
        """Lock spec"""
        yield from ()

# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server._internal.server.views.api import router_api  # noqa
from conda_store_server._internal.server.views.conda_store_ui import (  # noqa
    router_conda_store_ui,
)
from conda_store_server._internal.server.views.metrics import router_metrics  # noqa
from conda_store_server._internal.server.views.registry import router_registry  # noqa
from conda_store_server._internal.server.views.ui import router_ui  # noqa

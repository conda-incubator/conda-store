# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server._internal.plugins.lock.conda_lock import conda_lock
from conda_store_server._internal.plugins.lock.other_lock import other_lock

BUILTIN_PLUGINS = [conda_lock, other_lock]

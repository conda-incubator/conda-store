# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from conda_store_server._internal.server.app import CondaStoreServer

main = CondaStoreServer.launch_instance

if __name__ == "__main__":
    main()

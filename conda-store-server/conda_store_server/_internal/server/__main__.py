# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os

import uvicorn

import conda_store_server

from conda_store_server._internal.server.app import CondaStoreServer


main = CondaStoreServer.launch_instance

if __name__ == "__main__":
    server = main()
    uvicorn.run(
        "conda_store_server._internal.server.app:CondaStoreServer.create_webserver",
        host=server.address,
        port=server.port,
        workers=1,
        proxy_headers=server.behind_proxy,
        forwarded_allow_ips=("*" if server.behind_proxy else None),
        reload=server.reload,
        reload_dirs=(
            [os.path.dirname(conda_store_server.__file__)] if server.reload else []
        ),
        factory=True,
    )

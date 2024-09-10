# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json

from pathlib import Path

from fastapi.openapi.utils import get_openapi

from conda_store_server._internal.server import app as server_app


def gen_openapi_json():
    cs_server = server_app.CondaStoreServer()
    cs_server.initialize()
    app = cs_server.init_fastapi_app()
    filepath = Path(__file__).parent / "../static/openapi.json"

    with open(filepath, "w") as f:
        json.dump(
            get_openapi(
                title=app.title,
                version=app.version,
                openapi_version=app.openapi_version,
                description=app.description,
                routes=app.routes,
            ),
            f,
        )


if __name__ == "__main__":
    gen_openapi_json()

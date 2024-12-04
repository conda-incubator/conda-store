# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import pathlib

from conda_store_server._internal import action, schema, utils


@action.action
def action_save_lockfile(
    context,
    specification: schema.LockfileSpecification,
):
    # Note: this calls dict on specification so that the version field is
    # part of the output
    lockfile = specification.model_dump()["lockfile"]
    lockfile_filename = pathlib.Path.cwd() / "conda-lock.yaml"

    with lockfile_filename.open("w") as f:
        json.dump(lockfile, f, cls=utils.CustomJSONEncoder)

    return lockfile

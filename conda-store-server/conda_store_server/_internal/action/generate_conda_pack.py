# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import pathlib

import conda_pack

from conda_store_server._internal import action


@action.action
def action_generate_conda_pack(
    context,
    conda_prefix: pathlib.Path,
    output_filename: pathlib.Path,
):
    conda_pack.pack(
        prefix=str(conda_prefix),
        output=str(output_filename),
        ignore_missing_files=True,
    )

import pathlib

import conda_pack
from conda_store_server import action


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

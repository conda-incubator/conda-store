import pathlib

from conda_store_server import action


@action.action
def action_generate_conda_docker(
    context,
    conda_prefix: pathlib.Path,
    default_docker_image: str,
    container_registry,
    output_image_name: str,
    output_image_tag: str,
):
    raise RuntimeError(
        "Generating Docker images is currently not supported, see "
        "https://github.com/conda-incubator/conda-store/issues/666"
    )

    # Import is inside the function because conda_docker is only available on
    # Linux
    from conda_docker.conda import (
        build_docker_environment_image,
        conda_info,
        fetch_precs,
        find_user_conda,
        precs_from_environment_prefix,
    )

    user_conda = find_user_conda()
    info = conda_info(user_conda)
    download_dir = info["pkgs_dirs"][0]
    precs = precs_from_environment_prefix(str(conda_prefix), download_dir, user_conda)
    records = fetch_precs(download_dir, precs)
    base_image = container_registry.pull_image(default_docker_image)
    image = build_docker_environment_image(
        base_image=base_image,
        output_image=f"{output_image_name}:{output_image_tag}",
        records=records,
        default_prefix=info["env_vars"]["CONDA_ROOT"],
        download_dir=download_dir,
        user_conda=user_conda,
        channels_remap=info.get("channels_remap", []),
        layering_strategy="single",
    )
    return image

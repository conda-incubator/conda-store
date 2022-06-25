import os
import re
import tempfile
import time
import asyncio

import click

from conda_store import api, runner, utils, exception


async def parse_build(conda_store_api: api.CondaStoreAPI, uri: str):
    if re.fullmatch("(.+)/(.*):(.*)", uri):
        namespace, name, build_id = re.fullmatch("(.+)/(.*):(.*)", uri).groups()
        build = await conda_store_api.get_build(build_id)
        environment = await conda_store_api.get_environment(build_id)
        if build["environment_id"] != environment["id"]:
            raise exception.CondaStoreError(
                f"build {build_id} does not belong to environment {namespace}/{name}"
            )
        build_id = int(build_id)
    elif re.fullmatch("(.+)/(.*)", uri):
        namespace, name = re.fullmatch("(.+)/(.*)", uri).groups()
        environment = await conda_store_api.get_environment(namespace, name)
        build_id = environment["current_build_id"]
    if re.fullmatch(r"\d+", uri):  # build_id
        build_id = int(uri)

    return build_id


@click.group()
@click.option(
    "--conda-store-url",
    default="http://localhost:5000",
    envvar="CONDA_STORE_URL",
    help="Conda-Store base url including prefix",
)
@click.option(
    "--auth",
    envvar="CONDA_STORE_AUTH",
    type=click.Choice(["none", "token", "basic"], case_sensitive=False),
    help="Conda-Store authentication to use",
    default="none",
)
@click.option(
    "--no-verify-ssl",
    envvar="CONDA_STORE_NO_VERIFY",
    is_flag=True,
    default=False,
    help="Disable tls verification on API requests",
)
@click.pass_context
def cli(ctx, conda_store_url: str, auth: str, no_verify_ssl: bool):
    ctx.ensure_object(dict)
    ctx.obj["CONDA_STORE_API"] = api.CondaStoreAPI(
        conda_store_url=conda_store_url,
        verify_ssl=not no_verify_ssl,
        auth=auth,
    )


@cli.command(name="info")
@click.pass_context
@utils.coro
async def get_permissions(ctx):
    """Get current permissions and default namespace"""
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        data = await conda_store.get_permissions()

    utils.console.print(
        f"Default namespace is [bold]{data['primary_namespace']}[/bold]"
    )

    columns = {
        "Namespace": "namespace",
        "Name": "name",
        "Permissions": "permissions",
    }

    rows = []
    for key, value in data["entity_permissions"].items():
        namespace, name = key.split("/")
        rows.append(
            {
                "namespace": namespace,
                "name": name,
                "permissions": " ".join(_ for _ in value),
            }
        )

    utils.output_table("Permissions", columns, rows)


@cli.command(name="download")
@click.argument("uri")
@click.option(
    "--artifact",
    default="lockfile",
    type=click.Choice(["logs", "yaml", "lockfile", "archive"], case_sensitive=False),
)
@click.option(
    "--output-filename",
    help="Output filename for given download. build-{build_id}.{extension yaml|lock|tar.gz|image}",
)
@click.pass_context
@utils.coro
async def download(ctx, uri: str, artifact: str, output_filename: str = None):
    """Download artifacts for given build

    URI in format '<build-id>', '<namespace>/<name>', '<namespace>/<name>:<build-id>'
    """
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await parse_build(conda_store, uri)

        content = await conda_store.download(build_id, artifact)
        if output_filename is None:
            if artifact == "yaml":
                extension = "yaml"
            elif artifact == "lockfile":
                extension = "lock"
            elif artifact == "archive":
                extension = "tar.gz"
            elif artifact == "docker":
                extension = "image"
            output_filename = f"build-{build_id}.{extension}"

        with open(output_filename, "wb") as f:
            f.write(content)

        print(os.path.abspath(output_filename), end="")


@cli.command("wait")
@click.option(
    "--timeout",
    type=int,
    default=10 * 60,
    help="Time to wait for build to complete until reporting an error. Default 10 minutes",
)
@click.option(
    "--interval",
    type=int,
    default=10,
    help="Time to wait between polling for build status.Default 10 seconds",
)
@click.pass_context
@utils.coro
async def wait_environment(ctx, uri: str, timeout: int, interval: int):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await parse_build(conda_store, uri)

    start_time = time.time()
    while (start_time - time.time()) < timeout:
        build = await conda_store.get_build(build_id)
        if build["status"] == "COMPLETED":
            return
        elif build["status"] == "FAILED":
            raise exception.CondaStoreError(f"Build {build_id} failed")
        await asyncio.sleep(interval)

    raise exception.CondaStoreError(
        f"Build {build_id} failed to complete in {timeout} seconds"
    )


@cli.command("run")
@click.option(
    "--artifact",
    default="archive",
    type=click.Choice(["yaml", "lockfile", "archive"], case_sensitive=False),
    help="Artifact type to use for execution. Conda-Pack is the default format",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching builds for fast execution",
)
@click.argument("uri")
@click.argument("command", nargs=-1)
@click.pass_context
@utils.coro
async def run_environment(ctx, uri: str, no_cache: bool, command: str, artifact: str):
    """Execute given environment specified as a URI with COMMAND

    URI in format '<build-id>', '<namespace>/<name>', '<namespace>/<name>:<build-id>'\n
    COMMAND is a list of arguments to execute in given environment
    """
    if len(command) == 0:
        command = ["python"]

    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await parse_build(conda_store, uri)

        if no_cache:
            with tempfile.TemporaryDirectory() as tmpdir:
                await runner.run_build(conda_store, tmpdir, build_id, command, artifact)
        else:
            directory = os.path.join(
                tempfile.gettempdir(), "conda-store", str(build_id)
            )
            os.makedirs(directory, exist_ok=True)
            await runner.run_build(conda_store, directory, build_id, command, artifact)

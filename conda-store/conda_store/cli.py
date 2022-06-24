import os
import re
import tempfile

import click
from rich.panel import Panel
from rich.pretty import Pretty

from conda_store import api, runner, utils


async def parse_build(conda_store_api: api.CondaStoreAPI, uri: str):
    if re.fullmatch(r"\d+", uri):  # build_id
        build_id = int(uri)
    elif re.fullmatch("(.+)/(.*)", uri):
        namespace, name = uri.split("/")
        environment = await conda_store_api.get_environment(namespace, name)
        build_id = environment["current_build_id"]
    return build_id


@click.group()
@click.option(
    "--conda-store-url", default="http://localhost:5000", help="Conda-Store url"
)
@click.option("--auth", type=click.Choice(["token", "basic"], case_sensitive=False))
@click.option("--no-verify-ssl", is_flag=True, default=False)
@click.pass_context
def cli(ctx, conda_store_url: str, auth: str, no_verify_ssl: bool):
    ctx.ensure_object(dict)
    ctx.obj["CONDA_STORE_API"] = api.CondaStoreAPI(
        conda_store_url=os.environ.get("CONDA_STORE_URL", conda_store_url),
        verify_ssl=False
        if "CONDA_STORE_NO_VERIFY" in os.environ
        else not no_verify_ssl,
        auth=os.environ.get("CONDA_STORE_AUTH", auth),
    )


@cli.command(name="info")
@click.pass_context
@utils.coro
async def get_permissions(ctx):
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
@click.option("--output-filename")
@click.pass_context
@utils.coro
async def download(ctx, uri: str, artifact: str, output_filename: str = None):
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


@cli.command("run")
@click.argument("uri")
@click.option("--cache", type=bool, default=True)
@click.option("--command", default="python")
@click.option(
    "--artifact",
    default="archive",
    type=click.Choice(["yaml", "lockfile", "archive"], case_sensitive=False),
)
@click.pass_context
@utils.coro
async def run_environment(ctx, uri: str, cache: bool, command: str, artifact: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await parse_build(conda_store, uri)

        if not cache:
            with tempfile.TemporaryDirectory() as tmpdir:
                await runner.run_build(conda_store, tmpdir, build_id, command, artifact)
        else:
            directory = os.path.join(
                tempfile.gettempdir(), "conda-store", str(build_id)
            )
            os.makedirs(directory, exist_ok=True)
            await runner.run_build(conda_store, directory, build_id, command, artifact)

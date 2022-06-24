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


# ================== LIST ====================
@cli.group(name="list")
def list_group():
    pass


@list_group.command(name="namespace")
@click.option(
    "--output",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
)
@click.pass_context
@utils.coro
async def list_namespace(ctx, output: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        namespaces = await conda_store.list_namespaces()

    if output == "table":
        utils.output_table("Environments", {"Name": "name", "Id": "id"}, namespaces)
    elif output == "json":
        utils.output_json(namespaces)


@list_group.command(name="environment")
@click.option(
    "--output",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
)
@click.pass_context
@utils.coro
async def list_environment(ctx, output: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        environments = await conda_store.list_environments()

    if output == "table":
        utils.output_table(
            "Environments",
            {"Namespace": "namespace.name", "Name": "name", "Id": "id"},
            environments,
        )
    elif output == "json":
        utils.output_json(environments)


@list_group.command(name="build")
@click.option(
    "--output",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
)
@click.pass_context
@utils.coro
async def list_build(ctx, output: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        environments = await conda_store.list_builds()

    for environment in environments:
        environment["size"] = utils.sizeof_fmt(environment["size"])

    if output == "table":
        utils.output_table(
            "Buidls",
            {
                "Id": "id",
                "Environment Id": "environment_id",
                "Size": "size",
                "Status": "status",
            },
            environments,
        )
    elif output == "json":
        utils.output_json(environments)


# ================== CREATE ========================
@cli.group()
def create():
    pass


@create.command(name="namespace")
@click.argument("namespace")
@click.pass_context
@utils.coro
async def create_namespace(ctx, namespace: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        await conda_store.create_namespace(namespace)

    utils.console.print(f"Successfully created namespace {namespace}")


@create.command(name="environment")
@click.argument("specification", type=click.File("r"))
@click.option("--namespace", type=str)
@click.pass_context
@utils.coro
async def create_environment(ctx, namespace: str, specification):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await conda_store.create_environment(namespace, specification.read())

    utils.console.print(
        f"Successfully created environment in namespace {namespace} build id {build_id}"
    )


# ==================== DELETE =======================
@cli.group()
def delete():
    pass


@delete.command(name="namespace")
@click.argument("namespace")
@click.pass_context
@utils.coro
async def delete_namespace(ctx, namespace: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        await conda_store.delete_namespace(namespace)

    utils.console.print(f"Successfully deleted namespace {namespace}")


@delete.command(name="environment")
@click.argument("namespace")
@click.argument("name")
@click.pass_context
@utils.coro
async def delete_environment(ctx, namespace: str, name: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        await conda_store.delete_environment(namespace, name)

    utils.console.print(f"Successfully deleted environment {namespace}/{name}")


# ========================= GET ============================
@cli.group()
def get():
    pass


@get.command(name="build")
@click.argument("build-id", type=int)
@click.pass_context
@utils.coro
async def get_build(ctx, build_id: int):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build = await conda_store.get_build(build_id)

    utils.console.print(
        Panel(
            "\n".join(
                [
                    f"Status: {build['status']}",
                    f"Size: {utils.sizeof_fmt(build['size'])}",
                    f"Scheduled {build['scheduled_on']}",
                    f"Started {build['started_on']}",
                    f"Ended {build['ended_on']}",
                ]
            ),
            title="Build Info",
        )
    )

    utils.console.print(
        Panel(Pretty(build["specification"]["spec"]), title="Specification")
    )


# ================= GENERAL =================
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

import asyncio
import datetime
import os
import re
import tempfile
import time
from typing import List

import click
from conda_store import __version__, api, exception, runner, utils
from ruamel.yaml import YAML


async def parse_build(conda_store_api: api.CondaStoreAPI, uri: str):
    if re.fullmatch("(.+)/(.*):(.*)", uri):
        namespace, name, build_id = re.fullmatch("(.+)/(.*):(.*)", uri).groups()
        build = await conda_store_api.get_build(build_id)
        environment = await conda_store_api.get_environment(namespace, name)
        if build["environment_id"] != environment["id"]:
            raise exception.CondaStoreError(
                f"build {build_id} does not belong to environment {namespace}/{name}"
            )
        build_id = int(build_id)
    elif re.fullmatch("(.+)/(.*)", uri):
        namespace, name = re.fullmatch("(.+)/(.*)", uri).groups()
        environment = await conda_store_api.get_environment(namespace, name)
        build_id = environment["current_build_id"]
    elif re.fullmatch(r"\d+", uri):  # build_id
        build_id = int(uri)
    else:
        raise exception.CondaStoreError(f"unable to parse uri={uri}")

    return build_id


@click.group()
@click.option(
    "--conda-store-url",
    default="http://localhost:8080",
    envvar="CONDA_STORE_URL",
    help="conda-store base url including prefix",
)
@click.option(
    "--auth",
    envvar="CONDA_STORE_AUTH",
    type=click.Choice(["none", "token", "basic"], case_sensitive=False),
    help="conda-store authentication to use",
    default="none",
)
@click.option(
    "--no-verify-ssl",
    envvar="CONDA_STORE_NO_VERIFY",
    is_flag=True,
    default=False,
    help="Disable tls verification on API requests",
)
@click.version_option(__version__)
@click.pass_context
def cli(ctx, conda_store_url: str, auth: str, no_verify_ssl: bool):
    ctx.ensure_object(dict)
    ctx.obj["CONDA_STORE_API"] = api.CondaStoreAPI(
        conda_store_url=conda_store_url,
        verify_ssl=not no_verify_ssl,
        auth_type=auth,
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
    utils.console.print(f"Authenticated [bold]{data['authenticated']}[/bold]")

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


@cli.command(name="token")
@click.option("--namespace", help="Primary namespace to assign to new token")
@click.option("--expiration", type=int, help="Seconds from now for token to expire")
@click.option(
    "--permission",
    help="Permission to assign to token in form <namespace>/<name>:<role1>,<role2>,...",
    multiple=True,
)
@click.pass_context
@utils.coro
async def get_token(ctx, namespace: str, expiration: int, permission: List[str]):
    role_bindings = {}
    for p in permission:
        namespace_name, roles = p.split(":")
        roles = roles.split(",")
        role_bindings[namespace_name] = roles

    if expiration:
        expiration = str(
            datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(seconds=expiration)
        )

    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        print(
            await conda_store.create_token(
                primary_namespace=namespace,
                expiration=expiration,
                role_bindings=role_bindings,
            ),
            end="",
        )


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
@click.argument("uri")
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
@click.option(
    "--artifact",
    type=click.Choice(
        ["build", "lockfile", "yaml", "archive", "docker"], case_sensitive=False
    ),
    default="build",
    help="Choice of artifact to wait for. Default is 'build' which indicates the environment was built.",
)
@click.pass_context
@utils.coro
async def wait_environment(ctx, uri: str, timeout: int, interval: int, artifact: str):
    """Wait for given URI to complete or fail building

    URI in format '<build-id>', '<namespace>/<name>', '<namespace>/<name>:<build-id>'
    """
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        build_id = await parse_build(conda_store, uri)

        start_time = time.time()
        while (time.time() - start_time) < timeout:
            build = await conda_store.get_build(build_id)
            build_artifact_types = set(
                _["artifact_type"] for _ in build["build_artifacts"]
            )

            if artifact == "build" and build["status"] == "COMPLETED":
                return
            elif artifact == "build" and build["status"] == "FAILED":
                raise exception.CondaStoreError(f"Build {build_id} failed")
            elif artifact == "lockfile" and "LOCKFILE" in build_artifact_types:
                return
            elif artifact == "yaml" and "YAML" in build_artifact_types:
                return
            elif artifact == "archive" and "CONDA_PACK" in build_artifact_types:
                return
            elif artifact == "docker" and "DOCKER_MANIFEST" in build_artifact_types:
                return
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


@cli.command("solve")
@click.argument("filename", type=click.File("r"))
@click.option(
    "--output",
    default="table",
    type=click.Choice(["json", "table"]),
    help="Output format to display solve. Default table.",
)
@click.pass_context
@utils.coro
async def solve_environment(ctx, filename, output: str):
    """Remotely solve given environment.yaml"""
    yaml = YAML(typ="safe")
    data = yaml.load(filename)

    def _get_pip(data):
        for _ in data.get("dependencies", []):
            if isinstance(_, dict):
                return _.get("pip", [])
        return []

    arguments = {
        "channels": data.get("channels", []),
        "conda": [_ for _ in data.get("dependencies", []) if isinstance(_, str)],
        "pip": _get_pip(data),
    }

    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        packages = await conda_store.solve_environment(**arguments)

    total_size = 0
    for package in packages:
        total_size += package["size"]
        package["size"] = utils.sizeof_fmt(package["size"])

    if output == "table":
        utils.output_table(
            "Packages",
            {
                "Name": "name",
                "Version": "version",
                "Channel": "channel_id",
                "Size": "size",
            },
            packages,
        )
        utils.console.print(f"Total Size: {utils.sizeof_fmt(total_size)}")
    elif output == "json":
        utils.output_json(packages)


# ================= LIST ==================
@cli.group("list")
def list_group():
    pass


@list_group.command("namespace")
@click.option(
    "--output",
    default="table",
    type=click.Choice(["json", "table"]),
    help="Output format to display builds. Default table.",
)
@click.pass_context
@utils.coro
async def list_namespace(ctx, output: str):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        namespaces = await conda_store.list_namespaces()

    if output == "table":
        utils.output_table("Namespaces", {"Id": "id", "Name": "name"}, namespaces)
    elif output == "json":
        utils.output_json(namespaces)


@list_group.command("build")
@click.option(
    "--status",
    # see conda_store_server.schema.BuildStatus
    type=click.Choice(["QUEUED", "BUILDING", "COMPLETED", "FAILED"]),
    help="Filter builds which have given status",
)
@click.option(
    "--artifact",
    # see conda_store_server.schema.BuildArtifactType
    type=click.Choice(
        [
            "DIRECTORY",
            "LOCKFILE",
            "LOGS",
            "YAML",
            "CONDA_PACK",
            "DOCKER_BLOB",
            "DOCKER_MANIFEST",
        ]
    ),
    help="Filter builds which have given artifact",
)
@click.option(
    "--package",
    help="Filter builds which have given package (can be used multiple times)",
    multiple=True,
)
@click.option(
    "--output",
    default="table",
    type=click.Choice(["json", "table"]),
    help="Output format to display builds. Default table.",
)
@click.pass_context
@utils.coro
async def list_build(ctx, output: str, status: str, artifact: str, package: List[str]):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        builds = await conda_store.list_builds(
            status=status,
            artifact=artifact,
            packages=package,
        )

    for build in builds:
        build["size"] = utils.sizeof_fmt(build["size"])

    if output == "table":
        utils.output_table(
            "Builds", {"Id": "id", "Size": "size", "Status": "status"}, builds
        )
    elif output == "json":
        utils.output_json(builds)


@list_group.command("environment")
@click.option(
    "--status",
    # see conda_store_server.schema.BuildStatus
    type=click.Choice(["QUEUED", "BUILDING", "COMPLETED", "FAILED"]),
    help="Filter environments which have given status",
)
@click.option(
    "--artifact",
    # see conda_store_server.schema.BuildArtifactType
    type=click.Choice(
        [
            "DIRECTORY",
            "LOCKFILE",
            "LOGS",
            "YAML",
            "CONDA_PACK",
            "DOCKER_BLOB",
            "DOCKER_MANIFEST",
        ]
    ),
    help="Filter environments which have given artifact",
)
@click.option(
    "--package",
    help="Filter environments which have given package (can be used multiple times)",
    multiple=True,
)
@click.option(
    "--output",
    default="table",
    type=click.Choice(["json", "table"]),
    help="Output format to display builds. Default table.",
)
@click.pass_context
@utils.coro
async def list_environment(
    ctx, output: str, status: str, artifact: str, package: List[str]
):
    async with ctx.obj["CONDA_STORE_API"] as conda_store:
        builds = await conda_store.list_environments(
            status=status,
            artifact=artifact,
            packages=package,
        )

    if output == "table":
        utils.output_table(
            "Environments",
            {"Id": "id", "Namespace Id": "namespace.id", "Name": "name"},
            builds,
        )
    elif output == "json":
        utils.output_json(builds)

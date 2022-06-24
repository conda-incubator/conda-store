from typing import List, Dict
from functools import wraps
import json
import sys
import os
import io
import re
import tempfile
import tarfile
import subprocess
import shlex

import click
import asyncio
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.pretty import Pretty

from conda_store import api, exception, runner


console = Console()
error_console = Console(stderr=True, style="bold red")


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return asyncio.run(f(*args, **kwargs))
        except exception.CondaStoreError as e:
            error_console.print(e.args[0])
            sys.exit(1)

    return wrapper


def flatten(d: Dict):
    _d = {}
    for key, value in d.items():
        if isinstance(value, dict):
            for _key, _value in flatten(value).items():
                _d[f"{key}.{_key}"] = _value
        else:
            _d[key] = value
    return _d


def lookup(d: Dict, key: str):
    _d = d
    keys = key.split('.')
    for key in keys:
        _d = _d[key]
    return _d


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def timedelta_fmt(td):
    """
    Returns a humanized string representing timedelta
    """

    def plural(unit, word):
        if unit > 1:
            return word + 's'
        return word

    years = td.days // 365
    months = td.days // 30
    days = td.days
    hours = td.seconds / 3600
    minutes = td.seconds % 60
    seconds = td.seconds

    if years > 0:
        return f"{years} {plural(years, 'year')}"
    elif months > 0:
        return f"{months} {plural(months, 'month')}"
    elif days > 0:
        return f"{days} {plural(days, 'day')}"
    elif hours > 0:
        return f"{hours} {plural(hours, 'hour')}"
    elif minutes > 0:
        return f"{minutes} {plural(minutes, 'minute')}"
    elif seconds > 0:
        return f"{seconds} {plural(seconds, 'second')}"


async def parse_build(conda_store_api: api.CondaStoreAPI, uri: str):
    if re.fullmatch('\d+', uri): # build_id
        build_id = int(uri)
    elif re.fullmatch('(.+)/(.*)', uri):
        namespace, name = uri.split('/')
        environment = await conda_store_api.get_environment(namespace, name)
        build_id = environment['current_build_id']
    return build_id


def output_json(data, **kwargs):
    print(json.dumps(data, **kwargs), end="")


def output_table(title: str, columns: Dict[str, str], rows: List[Dict]):
    table = Table(title=title)
    for column in columns.keys():
        table.add_column(column)

    for row in rows:
        table.add_row(*[str(lookup(row, key)) for key in columns.values()])

    console.print(table)


@click.group()
@click.option('--conda-store-url', default="http://localhost:5000", help="Conda-Store url")
@click.option('--auth', type=click.Choice(['token', 'basic'], case_sensitive=False))
@click.option('--no-verify-ssl', is_flag=True, default=False)
@click.pass_context
def cli(ctx, conda_store_url: str, auth: str, no_verify_ssl: bool):
    ctx.ensure_object(dict)
    ctx.obj['CONDA_STORE_API'] = api.CondaStoreAPI(
        conda_store_url=os.environ.get("CONDA_STORE_URL", conda_store_url),
        verify_ssl=False if "CONDA_STORE_NO_VERIFY" in os.environ else not no_verify_ssl,
        auth=os.environ.get("CONDA_STORE_AUTH", auth))


@cli.command(name="info")
@click.pass_context
@coro
async def get_permissions(ctx):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        data = await conda_store.get_permissions()

    console.print(f"Default namespace is [bold]{data['primary_namespace']}[/bold]")

    columns = {
        "Namespace": "namespace",
        "Name": "name",
        "Permissions": "permissions",
    }

    rows = []
    for key, value in data["entity_permissions"].items():
        namespace, name = key.split("/")
        rows.append({
            "namespace": namespace,
            "name": name,
            "permissions": " ".join(_ for _ in value)
        })

    output_table("Permissions", columns, rows)


@cli.group()
def namespace():
    pass


@namespace.command(name="list")
@click.option('--output', default='table', type=click.Choice(['table', 'json'], case_sensitive=False))
@click.pass_context
@coro
async def namespace_list(ctx, output: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        namespaces = await conda_store.list_namespaces()

    if output == "table":
        output_table("Environments", {"Name": "name", "Id": "id"}, namespaces)
    elif output == "json":
        output_json(namespaces)


@namespace.command(name="create")
@click.argument("namespace")
@click.pass_context
@coro
async def namespace_create(ctx, namespace: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        await conda_store.create_namespace(namespace)

    console.print(f"Successfully created namespace {namespace}")


@namespace.command(name="delete")
@click.argument("namespace")
@click.pass_context
@coro
async def namespace_delete(ctx, namespace: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        await conda_store.delete_namespace(namespace)

    console.print(f"Successfully deleted namespace {namespace}")


@cli.group()
def environment():
    pass


@environment.command(name="list")
@click.option('--output', default='table', type=click.Choice(['table', 'json'], case_sensitive=False))
@click.pass_context
@coro
async def environment_list(ctx, output: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        environments = await conda_store.list_environments()

    if output == "table":
        output_table("Environments", {"Namespace": "namespace.name", "Name": "name", "Id": "id"}, environments)
    elif output == "json":
        output_json(environments)


@environment.command(name="create")
@click.argument("specification", type=click.File('r'))
@click.option("--namespace", type=str)
@click.pass_context
@coro
async def namespace_create(ctx, namespace: str, specification):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        build_id = await conda_store.create_environment(namespace, specification.read())

    console.print(f"Successfully created environment in namespace {namespace} build id {build_id}")


@environment.command(name="delete")
@click.argument("namespace")
@click.argument("name")
@click.pass_context
@coro
async def namespace_delete(ctx, namespace: str, name: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        await conda_store.delete_environment(namespace, name)

    console.print(f"Successfully deleted environment {namespace}/{name}")


@cli.group()
def build():
    pass


@build.command(name="list")
@click.option('--output', default='table', type=click.Choice(['table', 'json'], case_sensitive=False))
@click.pass_context
@coro
async def build_list(ctx, output: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        environments = await conda_store.list_builds()

    for environment in environments:
        environment["size"] = sizeof_fmt(environment["size"])

    if output == "table":
        output_table("Buidls", {"Id": "id", "Environment Id": "environment_id", "Size": "size", "Status": "status"}, environments)
    elif output == "json":
        output_json(environments)


@build.command(name="get")
@click.argument("build-id", type=int)
@click.pass_context
@coro
async def build_get(ctx, build_id: int):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        build = await conda_store.get_build(build_id)

    console.print(Panel("\n".join([
        f"Status: {build['status']}",
        f"Size: {sizeof_fmt(build['size'])}",
        f"Scheduled {build['scheduled_on']}",
        f"Started {build['started_on']}",
        f"Ended {build['ended_on']}",
    ]), title="Build Info"))

    console.print(
        Panel(
            Pretty(build['specification']['spec']),
            title="Specification"
        )
    )


@cli.command(name="download")
@click.argument("uri")
@click.option("--artifact", default="lockfile", type=click.Choice(['logs', 'yaml', 'lockfile', 'archive'], case_sensitive=False))
@click.option("--output-filename")
@click.pass_context
@coro
async def download(ctx, uri: str, artifact: str, output_filename: str = None):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
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
@click.option("--artifact", default="archive", type=click.Choice(['yaml', 'lockfile', 'archive'], case_sensitive=False))
@click.pass_context
@coro
async def run_environment(ctx, uri: str, cache: bool, command: str, artifact: str):
    async with ctx.obj['CONDA_STORE_API'] as conda_store:
        build_id = await parse_build(conda_store, uri)

        if not cache:
            with tempfile.TemporaryDirectory() as tmpdir:
                await runner.run_build(conda_store, tmpdir, build_id, command, artifact)
        else:
            directory = os.path.join(
                tempfile.gettempdir(),
                "conda-store", str(build_id))
            os.makedirs(directory, exist_ok=True)
            await runner.run_build(conda_store, directory, build_id, command, artifact)

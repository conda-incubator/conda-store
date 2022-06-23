from typing import List, Dict
from functools import wraps
import json
import sys
import os

import click
import asyncio
from rich.console import Console
from rich.table import Table

from conda_store import api, exception


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
@click.pass_context
def cli(ctx, conda_store_url: str):
    ctx.ensure_object(dict)
    ctx.obj['CONDA_STORE_URL'] = os.environ.get("CONDA_STORE_URL", conda_store_url)


@cli.command(name="info")
@click.pass_context
@coro
async def get_permissions(ctx):
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
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
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
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
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
        await conda_store.create_namespace(namespace)

    console.print(f"Successfully created namespace {namespace}")


@namespace.command(name="delete")
@click.argument("namespace")
@click.pass_context
@coro
async def namespace_delete(ctx, namespace: str):
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
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
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
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
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
        build_id = await conda_store.create_environment(namespace, specification.read())

    console.print(f"Successfully created environment in namespace {namespace} build id {build_id}")


@environment.command(name="delete")
@click.argument("namespace")
@click.argument("name")
@click.pass_context
@coro
async def namespace_delete(ctx, namespace: str, name: str):
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
        await conda_store.delete_environment(namespace, name)

    console.print(f"Successfully deleted environment {namespace}/{name}")


@cli.command("run")
@click.argument("namespace")
@click.argument("name")
@click.pass_context
@coro
async def run_environment(ctx, namespace: str, name: str):
    async with api.CondaStoreAPI(ctx.obj['CONDA_STORE_URL']) as conda_store:
        build_id = await conda_store.get_environment(namespace, name)

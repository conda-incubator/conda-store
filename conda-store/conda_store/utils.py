import asyncio
import functools
import json
import sys
from typing import Dict, List

from conda_store import exception
from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True, style="bold red")


def coro(f):
    @functools.wraps(f)
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
    keys = key.split(".")
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
            return word + "s"
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


def output_json(data, **kwargs):
    print(json.dumps(data, **kwargs), end="")


def output_table(title: str, columns: Dict[str, str], rows: List[Dict]):
    table = Table(title=title)
    for column in columns.keys():
        table.add_column(column)

    for row in rows:
        table.add_row(*[str(lookup(row, key)) for key in columns.values()])

    console.print(table)


def ensure_slash(*args):
    """Concatenate a series of stringable args, then append a trailing slash if there isn't one.

    This is to help reduce redirects, as that can cause the authorization token to be dropped between redirect
    """
    str_url = ""
    for arg in args:
        str_url += str(arg)
    if str_url[-1] != "/":
        str_url += "/"
    return str_url

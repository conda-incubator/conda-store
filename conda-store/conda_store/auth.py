import aiohttp
import yarl
from conda_store import utils


async def none_authentication(verify_ssl: bool = True):
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )


async def token_authentication(api_token: str, verify_ssl: bool = True):
    return aiohttp.ClientSession(
        headers={"Authorization": f"Bearer {api_token}"},
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )


async def basic_authentication(
    conda_store_url, username, password, verify_ssl: bool = True
):
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
        cookie_jar=aiohttp.CookieJar(treat_as_secure_origin=conda_store_url),
    )

    response = await session.post(
        utils.ensure_slash(yarl.URL(conda_store_url) / "login"),
        json={
            "username": username,
            "password": password,
        },
    )
    response.raise_for_status()
    return session

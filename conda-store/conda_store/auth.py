import aiohttp
import yarl


async def none_authentication(verify_ssl: bool = True):
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )


async def token_authentication(api_token: str, verify_ssl: bool = True):
    return aiohttp.ClientSession(
        headers={"Authorization": f"token {api_token}"},
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )


async def basic_authentication(
    conda_store_url, username, password, verify_ssl: bool = True
):
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )

    await session.post(
        yarl.URL(conda_store_url) / "login",
        json={
            "username": username,
            "password": password,
        },
    )

    return session

import aiohttp


async def token_authentication(api_token: str, verify_ssl: bool = True):
    return aiohttp.ClientSession(
        headers={"Authorization": f"token {api_token}"},
        connector=aiohttp.TCPConnector(ssl=None if verify_ssl else False),
    )

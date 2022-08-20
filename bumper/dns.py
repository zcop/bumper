from aiohttp import AsyncResolver


def get_resolver_with_public_nameserver() -> AsyncResolver:
    # requires aiodns
    return AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])


async def resolve(host: str) -> str:
    hosts = await get_resolver_with_public_nameserver().resolve(host)
    return hosts[0]["host"]

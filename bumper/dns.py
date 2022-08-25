"""Dns module."""
from aiohttp import AsyncResolver


def get_resolver_with_public_nameserver() -> AsyncResolver:
    """Get resolver."""
    # requires aiodns
    return AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])


async def resolve(host: str) -> str:
    """Resolve host."""
    hosts = await get_resolver_with_public_nameserver().resolve(host)
    return hosts[0]["host"]  # type:ignore[no-any-return]

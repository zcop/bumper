"""Global auth plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from ... import auth_util
from .. import WebserverPlugin


class GlobalAuthPlugin(WebserverPlugin):
    """Global auth plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/global/auth/getAuthCode",
                auth_util.get_authcode,
            ),
        ]

"""User plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.web import auth_util

from ... import WebserverPlugin
from . import BASE_URL


class UserPlugin(WebserverPlugin):
    """User plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}user/checkLogin",
                auth_util.login,
            ),
        ]

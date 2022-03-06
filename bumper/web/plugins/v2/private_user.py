"""Private user module."""
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from ... import auth_util
from .. import WebserverPlugin


class PrivateUserPlugin(WebserverPlugin):
    """Private user plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/checkLogin",
                auth_util.login,
            ),
        ]

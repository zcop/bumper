"""Global plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.web.images import get_bot_image

from .. import WebserverPlugin


class GlobalPlugin(WebserverPlugin):
    """Global plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/global/{year}/{month}/{day}/{id}",
                get_bot_image,
            ),
        ]

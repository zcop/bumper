"""Rapp plugin module."""
from typing import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from .. import WebserverPlugin


async def _handle_map_get(_: Request) -> Response:
    body = {
        "code": 0,
        "data": {"data": {"name": "My Home"}, "tag": None},
        "message": "success",
    }

    return web.json_response(body)


class RappPlugin(WebserverPlugin):
    """Rapp plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route("*", "/rapp/sds/user/data/map/get", _handle_map_get),
        ]

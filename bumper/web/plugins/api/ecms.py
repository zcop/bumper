"""Ecms plugin module."""

from typing import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from .. import WebserverPlugin


async def _handle_ad_res(_: Request) -> Response:
    body = {"code": 0, "data": [], "message": "success", "success": True}
    return web.json_response(body)


class EcmsPlugin(WebserverPlugin):
    """Ecms plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/ecms/app/ad/res",
                _handle_ad_res,
            ),
        ]

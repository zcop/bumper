"""Message plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class MessagePlugin(WebserverPlugin):
    """Message plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}message/hasMoreUnReadMsg",
                _handle_has_more_unread_message,
            ),
        ]


async def _handle_has_more_unread_message(_: Request) -> Response:
    return get_success_response({"moreUnReadMsg": "N"})

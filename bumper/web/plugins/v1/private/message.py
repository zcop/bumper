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
                f"{BASE_URL}message/hasUnreadMsg",
                _handle_has_unread_message,
            ),
            web.route(
                "*",
                f"{BASE_URL}message/getMsgList",
                _handle_get_msg_list,
            ),
        ]


async def _handle_has_unread_message(_: Request) -> Response:
    return get_success_response("N")


async def _handle_get_msg_list(_: Request) -> Response:
    return get_success_response({"hasNextPage": 0, "items": []})

"""Neng plugin module."""
from typing import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from .. import WebserverPlugin


async def _handle_neng_has_unread_message(_: Request) -> Response:
    # EcoVacs Home
    body = {"code": 0, "data": {"hasUnRead": True}}
    return web.json_response(body)


async def handle_neng_get_share_msgs(_: Request) -> Response:
    """Return shared messages."""
    # EcoVacs Home
    body = {"code": 0, "data": {"hasNext": False, "msgs": []}}

    # share msg response
    # {
    #     "code": 0,
    #     "data": {
    #         "hasNext": False,
    #         "msgs": [
    #         {
    #             "action": "shareDevice",
    #             "deviceName": "DEEBOT 900 Series",
    #             "did": "DID",
    #             "icon": "https://portal-ww.ecouser.net/api/pim/file/get/5ba4a2cb6c2f120001c32839",
    #             "id": "0154d03a-294e-4b99-a6df-fc2dbf4146d5",
    #             "isRead": False,
    #             "message": "User user@gmail.com sent you the sharing invitation of DEEBOT 900 Series.",
    #             "mid": "ls1ok3",
    #             "resource": "grU0",
    #             "shareStatus": "sharing",
    #             "ts": 1578206187412
    #         }
    #         ]
    #     }
    #     }

    return web.json_response(body)


async def handle_neng_get_list(_: Request) -> Response:
    """Get messages."""
    # EcoVacs Home
    body = {"code": 0, "data": {"hasNext": False, "msgs": []}}

    # Sample Message
    #     {
    # "id": "5da0ac9d636aec5107627ac4",
    # "ts": 1570811036877,
    # "did": "bot did",
    # "cid": "ls1ok3",
    # "name": "DEEBOT 900 Series",
    # "icon": "https://portal-ww.ecouser.net/api/pim/file/get/5ba4a2cb6c2f120001c32839",
    # "eventTypeId": "5aab824bb62ce30001f9a702",
    # "title": "DEEBOT is off the floor.",
    # "body": "DEEBOT is off the floor. Please put it back.",
    # "read": false,
    # "UILogicId": "D_900",
    # "type": "web",
    # "url": "https://portal-ww.ecouser.net/api/pim/eventdetail.html?id=5ba21e44aed83800015b9ca8" # Off the floor instructions
    # }

    return web.json_response(body)


class NengPlugin(WebserverPlugin):
    """Neng plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/neng/message/hasUnreadMsg",
                _handle_neng_has_unread_message,
            ),
            web.route(
                "*",
                "/neng/message/getShareMsgs",
                handle_neng_get_share_msgs,
            ),
            web.route(
                "*",
                "/neng/message/getlist",
                handle_neng_get_list,
            ),
        ]

import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis

from ... import WebserverPlugin


class MessagePlugin(WebserverPlugin):
    """Message plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/message/hasUnreadMsg",
                self.handle_hasUnreadMessage,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/message/getMsgList",
                self.handle_getMsgList,
            ),
        ]

    async def handle_hasUnreadMessage(self, request):  # EcoVacs Home
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": "N",
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

    async def handle_getMsgList(self, request):  # EcoVacs Home
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": {"hasNextPage": 0, "items": []},
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

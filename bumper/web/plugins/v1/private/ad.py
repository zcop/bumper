"""Ad plugin module."""
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis

from ... import WebserverPlugin


class AdPlugin(WebserverPlugin):
    """Ad plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/ad/getAdByPositionType",
                self.handle_getAdByPositionType,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/ad/getBootScreen",
                self.handle_getBootScreen,
            ),
        ]

    async def handle_getAdByPositionType(self, request):  # EcoVacs Home
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": None,
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

    async def handle_getBootScreen(self, request):  # EcoVacs Home
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": None,
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

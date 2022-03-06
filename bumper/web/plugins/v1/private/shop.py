"""Shop plugin module."""
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis

from ... import WebserverPlugin


class ShopPlugin(WebserverPlugin):
    """Shop plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/shop/getCnWapShopConfig",
                self.handle_getCnWapShopConfig,
            ),
        ]

    async def handle_getCnWapShopConfig(self, request):  # EcoVacs Home
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": {
                    "myShopShowFlag": "N",
                    "myShopUrl": "",
                    "shopIndexShowFlag": "N",
                    "shopIndexUrl": "",
                },
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

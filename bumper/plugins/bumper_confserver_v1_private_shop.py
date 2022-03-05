#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timedelta

from aiohttp import web

import bumper
from bumper import plugins
from bumper.models import *
from bumper.util import get_current_time_as_millis


class v1_private_shop(plugins.ConfServerApp):
    def __init__(self):
        self.name = "v1_private_shop"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v1"

        self.routes = [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/shop/getCnWapShopConfig",
                self.handle_getCnWapShopConfig,
                name="v1_shop_getCnWapShopConfig",
            ),
        ]

    async def handle_getCnWapShopConfig(self, request):  # EcoVacs Home
        try:
            body = {
                "code": bumper.RETURN_API_SUCCESS,
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

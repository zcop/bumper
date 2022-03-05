#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timedelta

from aiohttp import web

import bumper
from bumper import plugins
from bumper.models import *
from bumper.util import get_current_time_as_millis


class v1_private_campaign(plugins.ConfServerApp):
    def __init__(self):
        self.name = "v1_private_campaign"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v1"

        self.routes = [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/campaign/homePageAlert",
                self.handle_homePageAlert,
                name="v1_campaign_homePageAlert",
            ),
        ]

    async def handle_homePageAlert(self, request):
        try:
            nextAlert = convert_to_millis(
                (datetime.now() + timedelta(hours=12)).timestamp()
            )

            body = {
                "code": bumper.RETURN_API_SUCCESS,
                "data": {
                    "clickSchemeUrl": None,
                    "clickWebUrl": None,
                    "hasCampaign": "N",
                    "imageUrl": None,
                    "nextAlertTime": nextAlert,
                    "serverTime": get_current_time_as_millis(),
                },
                "msg": "操作成功",
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

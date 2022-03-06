"""Campaign plugin module."""
import logging
from datetime import datetime, timedelta
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import convert_to_millis, get_current_time_as_millis

from ... import WebserverPlugin


class CampaignPlugin(WebserverPlugin):
    """Campaign plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/campaign/homePageAlert",
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
                "code": RETURN_API_SUCCESS,
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

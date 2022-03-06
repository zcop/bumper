"""user setting plugin module."""

import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis

from ... import WebserverPlugin


class UserSettingPlugin(WebserverPlugin):
    """User setting plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/userSetting/getSuggestionSetting",
                self.handle_getSuggestionSetting,
            ),
        ]

    async def handle_getSuggestionSetting(self, request):
        try:

            body = {
                "code": RETURN_API_SUCCESS,
                "data": {
                    "acceptSuggestion": "Y",
                    "itemList": [
                        {
                            "name": "Aktionen/Angebote/Ereignisse",
                            "settingKey": "MARKETING",
                            "val": "Y",
                        },
                        {
                            "name": "Benutzerbefragung",
                            "settingKey": "QUESTIONNAIRE",
                            "val": "Y",
                        },
                        {
                            "name": "Produkt-Upgrade/Hilfe für Benutzer",
                            "settingKey": "INTRODUCTION",
                            "val": "Y",
                        },
                    ],
                },
                "msg": "操作成功",
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

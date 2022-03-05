import logging

from aiohttp import web

import bumper
from bumper import plugins
from bumper.util import get_current_time_as_millis


class v1_private_userSetting(plugins.ConfServerApp):
    def __init__(self):

        self.name = "v1_private_userSetting"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v1"

        self.routes = [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/userSetting/getSuggestionSetting",
                self.handle_getSuggestionSetting,
                name="v1_userSetting_getSuggestionSetting",
            ),
        ]

    async def handle_getSuggestionSetting(self, request):
        try:

            body = {
                "code": bumper.RETURN_API_SUCCESS,
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

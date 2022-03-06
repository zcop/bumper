import logging

from aiohttp import web

from bumper import plugins
from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis


class v1_private_message(plugins.ConfServerApp):
    def __init__(self):
        self.name = "v1_private_message"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v1"

        self.routes = [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/message/hasUnreadMsg",
                self.handle_hasUnreadMessage,
                name="v1_message_hasUnreadMsg",
            ),
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/message/getMsgList",
                self.handle_getMsgList,
                name="v1_message_getMsgList",
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

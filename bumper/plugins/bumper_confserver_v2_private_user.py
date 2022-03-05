
from aiohttp import web

from bumper import plugins
from bumper.rest import auth_util


class v2_private_user(plugins.ConfServerApp):
    def __init__(self):

        self.name = "v2_private_user"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v2"

        self.routes = [
            web.route(
                "*",
                "/private/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/checkLogin",
                auth_util.login,
                name="v2_user_checkLogin",
            ),
        ]

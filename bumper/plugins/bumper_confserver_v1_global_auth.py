#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timedelta

from aiohttp import web

import bumper
from bumper import plugins
from bumper.models import *
from bumper.rest import auth_util


class v1_global_auth(plugins.ConfServerApp):
    def __init__(self):
        self.name = "v1_global_auth"
        self.plugin_type = "sub_api"
        self.sub_api = "api_v1"

        self.routes = [
            web.route(
                "*",
                "/global/auth/getAuthCode",
                auth_util.get_authcode,
                name="v1_global_auth_getAuthCode",
            ),
        ]

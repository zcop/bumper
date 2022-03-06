"""Api appsvr plugin module."""
import json
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

import bumper
from bumper.plugins import WebserverPlugin, WebserverSubApi


# pylint: disable=no-self-use
class ApiAppsvrPlugin(WebserverPlugin):
    """Api appsvr plugin."""

    sub_api = WebserverSubApi.API

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/appsvr/app.do",
                self._handle_appsvr_app,
            ),
            web.route(
                "*",
                "/appsvr/service/list",
                self._handle_appsvr_service_list,
            ),
            web.route(
                "*",
                "/appsvr/oauth_callback",
                self._handle_appsvr_oauth_callback,
            ),
        ]

    async def _handle_appsvr_app(self, request: Request) -> Response:
        if request.method == "GET":
            # Skip GET for now
            return web.json_response({"result": "fail", "todo": "result"})

        try:
            if request.content_type == "application/x-www-form-urlencoded":
                postbody = await request.post()
            else:
                postbody = json.loads(await request.text())

            todo = postbody["todo"]

            if todo == "GetGlobalDeviceList":  # EcoVacs Home
                bots = bumper.db_get().table("bots").all()
                devices = []
                for bot in bots:
                    if bot["class"] != "":
                        device = bumper.include_EcoVacsHomeProducts_info(bot)
                        # Happens if the bot isn't on the EcoVacs Home list
                        if device is not None:
                            devices.append(device)

                body = {
                    "code": 0,
                    "devices": devices,
                    "ret": "ok",
                    "todo": "result",
                }

                return web.json_response(body)
        except Exception:  # pylint: disable=broad-except
            logging.error("Unexpected exception occurred", exc_info=True)

        raise HTTPInternalServerError

    async def _handle_appsvr_service_list(self, _: Request) -> Response:
        try:
            # original urls comment out as they are sub sub domain, which the current certificate is not valid
            # using url, where the certs is valid
            # data = {
            #     "account": "users-base.dc-eu.ww.ecouser.net",
            #     "jmq": "jmq-ngiot-eu.dc.ww.ecouser.net",
            #     "lb": "lbo.ecouser.net",
            #     "magw": "api-app.dc-eu.ww.ecouser.net",
            #     "msgcloud": "msg-eu.ecouser.net:5223",
            #     "ngiotLb": "jmq-ngiot-eu.area.ww.ecouser.net",
            #     "rop": "api-rop.dc-eu.ww.ecouser.net"
            # }

            data = {
                "account": "users-base.ecouser.net",
                "jmq": "jmq-ngiot-eu.ecouser.net",
                "lb": "lbo.ecouser.net",
                "magw": "api-app.ecouser.net",
                "msgcloud": "msg-eu.ecouser.net:5223",
                "ngiotLb": "jmq-ngiot-eu.ecouser.net",
                "rop": "api-rop.ecouser.net",
            }

            body = {"code": 0, "data": data, "ret": "ok", "todo": "result"}

            return web.json_response(body)
        except Exception:  # pylint: disable=broad-except
            logging.error("Unexpected exception occurred", exc_info=True)

        raise HTTPInternalServerError

    async def _handle_appsvr_oauth_callback(self, request: Request) -> Response:
        try:
            token = bumper.token_by_authcode(request.query["code"])
            oauth = bumper.user_add_oauth(token["userid"])
            body = {
                "code": 0,
                "data": oauth.toResponse(),
                "ret": "ok",
                "todo": "result",
            }

            return web.json_response(body)

        except Exception:  # pylint: disable=broad-except
            logging.error("Unexpected exception occurred", exc_info=True)

        raise HTTPInternalServerError

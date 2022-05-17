"""Appsvr plugin module."""
import copy
import json
import logging
from typing import Any, Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef
from amqtt.session import Session

import bumper
from bumper.db import db_get, token_by_authcode, user_add_oauth

from .. import WebserverPlugin
from .pim import get_product_iot_map


class AppsvrPlugin(WebserverPlugin):
    """Appsvr plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/appsvr/app.do",
                _handle_appsvr_app,
            ),
            web.route(
                "*",
                "/appsvr/service/list",
                _handle_appsvr_service_list,
            ),
            web.route(
                "*",
                "/appsvr/oauth_callback",
                _handle_appsvr_oauth_callback,
            ),
        ]


async def _handle_appsvr_app(request: Request) -> Response:
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
            bots = db_get().table("bots").all()
            devices = []
            for bot in bots:
                if bot["class"] != "":
                    device = _include_product_iot_map_info(bot)
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


def _include_product_iot_map_info(bot: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(bot)

    for botprod in get_product_iot_map()[0]:
        if botprod["classid"] == result["class"]:
            result["UILogicId"] = botprod["product"]["UILogicId"]
            result["ota"] = botprod["product"]["ota"]
            result["icon"] = botprod["product"]["iconUrl"]
            result["model"] = botprod["product"]["model"]
            result["pip"] = botprod["product"]["_id"]
            result["deviceName"] = botprod["product"]["name"]
            result["materialNo"] = botprod["product"]["materialNo"]
            result["product_category"] = (
                "DEEBOT"
                if botprod["product"]["name"].startswith("DEEBOT")
                else "UNKNOWN"
            )
            # bot["updateInfo"] = {
            #     "changeLog": "",
            #     "needUpdate": False
            # }
            # bot["service"] = {
            #     "jmq": "jmq-ngiot-eu.dc.ww.ecouser.net",
            #     "mqs": "api-ngiot.dc-as.ww.ecouser.net"
            # }

            result["status"] = (
                1 if bot["mqtt_connection"] or bot["xmpp_connection"] else 0
            )

            # mqtt_connection is not always set correctly, therefore workaround until fixed properly
            session: Session
            for (session, _) in bumper.mqtt_server.broker._sessions.values():
                did = session.client_id.split("@")[0]
                if did == bot["did"] and session.transitions.state == "connected":
                    result["status"] = 1

            break
    return result


async def _handle_appsvr_service_list(_: Request) -> Response:
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


async def _handle_appsvr_oauth_callback(request: Request) -> Response:
    try:
        token = token_by_authcode(request.query["code"])
        oauth = user_add_oauth(token["userid"])
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

"""Appsvr plugin module."""
import copy
import json
import logging
from collections.abc import Iterable
from typing import Any

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
                "/appsvr/app/config",
                _handle_appsvr_app_config,
            ),
            web.route(
                "*",
                "/appsvr/improve/accept",
                _handle_appsvr_improve_accept,
            ),
            web.route(
                "*",
                "/appsvr/notice/home",
                _handle_appsvr_notice_home,
            ),
            web.route(
                "*",
                "/appsvr/oauth_callback",
                _handle_appsvr_oauth_callback,
            ),
            web.route(
                "*",
                "/appsvr/service/list",
                _handle_appsvr_service_list,
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

        if todo == "GetGlobalDeviceList":
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
        if todo == "GetCodepush":
            return web.json_response(
                {
                    "code": 0,
                    "data": {"extend": {}, "type": "microsoft", "url": ""},
                    "ret": "ok",
                    "todo": "result",
                }
            )
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
        if token:
            oauth = user_add_oauth(token["userid"])
            if oauth:
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


async def _handle_appsvr_improve_accept(_: Request) -> Response:
    return web.json_response({"code": 0})


async def _handle_appsvr_notice_home(_: Request) -> Response:
    return web.json_response({"code": 0, "data": [], "ret": "ok", "todo": "result"})


async def _handle_appsvr_app_config(_: Request) -> Response:
    body = {
        "todo": "result",
        "ret": "ok",
        "code": 0,
        "data": [
            {
                "resId": "614d73873d80d1deed8be299",
                "code": "codepush_config",
                "name": "",
                "description": "",
                "type": "jsonObject",
                "content": {
                    "netDiagno": {
                        "deploymentKey": {
                            "production": "1YhT34XSJJ-iUPtrBsi-zXA1LPCyAtLjsEW7IU",
                            "staging": "Cqn5Kl-UYcru2RYKN9xJvMHaA7lWAmd7d-vli",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "robotDiscovery": {
                        "deploymentKey": {
                            "production": "z94xCOc2FnBqdw6IJMFvMoWFLALxVNGsK0wHuJ",
                            "staging": "w3nVjj2mBV1JdO8tBO2JcU8EL4W6nBrv8KOVo",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "language": {
                        "deploymentKey": {
                            "production": "mQ7b_ImAD5t_hapi17Dt_CK0ZU1nArKrTYdCTI",
                            "staging": "IPbEkwK4wD9MCzWtncXQ8C0lDdLQxOMn13Owg",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "winbot": {
                        "deploymentKey": {
                            "production": "QEdpHlrNp1ANHhYFbEJ63dYo1bcsZCShQ9H938",
                            "staging": "uYmbjPDsvnfIBjjY9pM0PdESrZX8_QxMpm-bH",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "beluga": {
                        "deploymentKey": {
                            "production": "vhaH5f2nNpKiXPFDhVq6yf4gr6xFGAOKoMGTFT",
                            "staging": "RT1aLYD7YwQms9vs539Qn5GjRlExVWeMTOHeF",
                        },
                        "version": "1.0.0",
                    },
                    "hwPush": {
                        "deploymentKey": {
                            "production": "4cPMrbntK2vbs-KRgsrJq4HI0W-hrTHP1BMTKq",
                            "staging": "dXgPCPco60Fc_JlZ5S_bS0ZanhlaNiU9elFaj",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "t10More": {
                        "deploymentKey": {
                            "production": "RSYAx668chaf0tpKvf1kJNaVJmDzi4g83wsg78",
                            "staging": "yQeevYX5q1yVhr_dH0VwKNJ3x3iDBSxJ-E91G",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "test20": {
                        "deploymentKey": {
                            "production": "n1MBCZHFWVi3PFdxg-u6N7yF6CStEXtlKms3O",
                            "staging": "vCmfAvE-g-OkOvLm8ckIfjLwf1c9a-fBGI6u2",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "at90": {
                        "deploymentKey": {
                            "production": "1W2Lw4KvqTz0D-UMxzfZSEcv2yWpoD7SZyGzb4",
                            "staging": "bokwAmqkL-svCnwI8Fd1pGSHBSf-aBoXWtNyi",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "bruceMore": {
                        "deploymentKey": {
                            "production": "P5sN80W6TdO5nQ63CJWvtTgnu-BKYqxQmf8IEi",
                            "staging": "1FXFufgsGXUcHc2F7eLWPPDXDsVySG9sj5VKc",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "furniture": {
                        "deploymentKey": {
                            "production": "VKfJlwYCG58sJN3FfCjYGqRd2M81HCIn2kOBrw",
                            "staging": "M7lyba6OXxVBG_KrkIgbv569Jnwz6V1gdk0oA",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "bruce3dRes": {
                        "deploymentKey": {
                            "production": "uOtNaTLAbWAFiQhovEqW4nyhvUbSxFNF92vdiV",
                            "staging": "4mm6F3Jak4JtMwO2AMHlbTHElUOMWZd_IzL5P",
                            "current": "production",
                        },
                        "version": "2.1.4",
                    },
                    "t10H5": {
                        "deploymentKey": {
                            "production": "mackERM5dTh8cqiAk9MEBuRhdgLEytf1emmE4H",
                            "staging": "f93aQ5QrspoyG5vYvPTICrfmS65YJVNFuNJ0o",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "x1proH5": {
                        "deploymentKey": {
                            "production": "Wt3wZa8Hs69dbZgtNXsiNVcda9P-GBSBDm4lDw",
                            "staging": "UvSn3tgPRYfmhwT7YOwP4WO5Us6HKC-sq91HS",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                    "andyproH5": {
                        "deploymentKey": {
                            "production": "SmTGB14wfXJnTZ0iHh03tEq83S9j6vK_B0zI9s",
                            "staging": "zhiPemGhbl0FV3V8_kBY9luOBgLd55YwYuImG",
                            "current": "production",
                        },
                        "version": "1.0.0",
                    },
                },
            }
        ],
    }

    return web.json_response(body)

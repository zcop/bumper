"""Users plugin module."""
import json
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper import bumper_announce_ip
from bumper.db import bot_remove, bot_set_nick, check_authcode, db_get, loginByItToken

from .. import WebserverPlugin


class UsersPlugin(WebserverPlugin):
    """Users plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/users/user.do",
                self._handle_usersapi,
            ),
        ]

    async def _handle_usersapi(self, request):
        if not request.method == "GET":  # Skip GET for now
            try:

                body = {}
                postbody = {}
                if request.content_type == "application/x-www-form-urlencoded":
                    postbody = await request.post()

                else:
                    postbody = json.loads(await request.text())

                todo = postbody["todo"]
                if todo == "FindBest":
                    service = postbody["service"]
                    if service == "EcoMsgNew":
                        srvip = bumper_announce_ip
                        srvport = 5223
                        logging.info(
                            "Announcing EcoMsgNew Server to bot as: {}:{}".format(
                                srvip, srvport
                            )
                        )
                        msgserver = {"ip": srvip, "port": srvport, "result": "ok"}
                        msgserver = json.dumps(msgserver)
                        msgserver = msgserver.replace(
                            " ", ""
                        )  # bot seems to be very picky about having no spaces, only way was with text

                        return web.json_response(text=msgserver)

                    elif service == "EcoUpdate":
                        srvip = "47.88.66.164"  # EcoVacs Server
                        srvport = 8005
                        logging.info(
                            "Announcing EcoUpdate Server to bot as: {}:{}".format(
                                srvip, srvport
                            )
                        )
                        body = {"result": "ok", "ip": srvip, "port": srvport}

                elif todo == "loginByItToken":
                    if "userId" in postbody:
                        if check_authcode(postbody["userId"], postbody["token"]):
                            body = {
                                "resource": postbody["resource"],
                                "result": "ok",
                                "todo": "result",
                                "token": postbody["token"],
                                "userId": postbody["userId"],
                            }
                    else:  # EcoVacs Home LoginByITToken
                        loginToken = loginByItToken(postbody["token"])
                        if not loginToken == {}:
                            body = {
                                "resource": postbody["resource"],
                                "result": "ok",
                                "todo": "result",
                                "token": loginToken["token"],
                                "userId": loginToken["userid"],
                            }
                        else:
                            body = {"result": "fail", "todo": "result"}

                elif todo == "GetDeviceList":
                    body = {
                        "devices": db_get().table("bots").all(),
                        "result": "ok",
                        "todo": "result",
                    }

                elif todo == "SetDeviceNick":
                    bot_set_nick(postbody["did"], postbody["nick"])
                    body = {"result": "ok", "todo": "result"}

                elif todo == "AddOneDevice":
                    bot_set_nick(postbody["did"], postbody["nick"])
                    body = {"result": "ok", "todo": "result"}

                elif todo == "DeleteOneDevice":
                    bot_remove(postbody["did"])
                    body = {"result": "ok", "todo": "result"}

                return web.json_response(body)

            except Exception as e:
                logging.exception(f"{e}")

        # Return fail for GET
        body = {"result": "fail", "todo": "result"}
        return web.json_response(body)

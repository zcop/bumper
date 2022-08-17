"""Lg plugin module."""
import json
import logging
import random
import string
import xml.etree.ElementTree as ET
from typing import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

import bumper
from bumper.db import bot_get
from bumper.models import ERR_COMMON

from .. import WebserverPlugin


async def _handle_lg_log(request: Request) -> Response:
    # EcoVacs Home
    randomid = "".join(random.sample(string.ascii_letters, 6))

    try:
        json_body = json.loads(await request.text())

        did = json_body["did"]

        botdetails = bot_get(did)
        if botdetails:
            if "cmdName" not in json_body:
                if "td" in json_body:
                    json_body["cmdName"] = json_body["td"]

            if "toId" not in json_body:
                json_body["toId"] = did

            if "toType" not in json_body:
                json_body["toType"] = botdetails["class"]

            if "toRes" not in json_body:
                json_body["toRes"] = botdetails["resource"]

            if "payloadType" not in json_body:
                json_body["payloadType"] = "x"

            if "payload" not in json_body:
                # json_body["payload"] = ""
                if json_body["td"] == "GetCleanLogs":
                    json_body["td"] = "q"
                    json_body["payload"] = '<ctl count="30"/>'

        if did != "":
            bot = bot_get(did)
            if bot and bot["company"] == "eco-ng":
                retcmd = await bumper.mqtt_helperbot.send_command(json_body, randomid)
                body = retcmd
                logging.debug("Send Bot - %s", json_body)
                logging.debug("Bot Response - %s", body)
                logs = []
                logsroot = ET.fromstring(retcmd["resp"])
                if logsroot.attrib["ret"] == "ok":
                    for log_line in logsroot:
                        cleanlog = {
                            "ts": log_line.attrib["s"],
                            "area": log_line.attrib["a"],
                            "last": log_line.attrib["l"],
                            "cleanType": log_line.attrib["t"],
                            # imageUrl allows for providing images of cleanings, something to look into later
                            # "imageUrl": "https://localhost:8007",
                        }
                        logs.append(cleanlog)
                    body = {
                        "ret": "ok",
                        "logs": logs,
                    }
                else:
                    body = {"ret": "ok", "logs": []}

                logging.debug("lg logs return: %s", json.dumps(body))
                return web.json_response(body)

            # No response, send error back
            logging.error("No bots with DID: %s connected to MQTT", json_body["toId"])
    except Exception:  # pylint: disable=broad-except
        logging.error("An unknown exception occurred", exc_info=True)

    body = {"id": randomid, "errno": ERR_COMMON, "ret": "fail"}
    return web.json_response(body)


class LgPlugin(WebserverPlugin):
    """Lg plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route("*", "/lg/log.do", _handle_lg_log),
        ]

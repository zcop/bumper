"""Iot plugin module."""
import json
import logging
import random
import string
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

import bumper
from bumper.db import bot_get

from .. import WebserverPlugin


async def _handle_devmanager_bot_command(request: Request) -> Response:
    try:
        json_body = json.loads(await request.text())

        randomid = "".join(random.sample(string.ascii_letters, 4))
        did = ""
        if "toId" in json_body:  # Its a command
            did = json_body["toId"]

        if did != "":
            bot = bot_get(did)
            if bot["company"] == "eco-ng":
                retcmd = await bumper.mqtt_helperbot.send_command(json_body, randomid)
                body = retcmd
                logging.debug(f"Send Bot - {json_body}")
                logging.debug(f"Bot Response - {body}")
                return web.json_response(body)
            else:
                # No response, send error back
                logging.error(
                    "No bots with DID: {} connected to MQTT".format(json_body["toId"])
                )
                body = {
                    "id": randomid,
                    "errno": 500,
                    "ret": "fail",
                    "debug": "wait for response timed out",
                }
                return web.json_response(body)

        else:
            if "td" in json_body:  # Seen when doing initial wifi config
                if json_body["td"] == "PollSCResult":
                    body = {"ret": "ok"}
                    return web.json_response(body)

                if json_body["td"] == "HasUnreadMsg":  # EcoVacs Home
                    body = {"ret": "ok", "unRead": False}
                    return web.json_response(body)

                if json_body["td"] == "PreWifiConfig":  # EcoVacs Home
                    body = {"ret": "ok"}
                    return web.json_response(body)
    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


class IotPlugin(WebserverPlugin):
    """Iot plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/iot/devmanager.do",
                _handle_devmanager_bot_command,
            ),
        ]

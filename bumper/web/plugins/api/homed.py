"""Homed plugin module."""
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from .. import WebserverPlugin


class HomedPlugin(WebserverPlugin):
    """Homed plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "(homed/home/list",
                _handle_home_list,
            ),
        ]


async def _handle_home_list(request: Request) -> Response:
    try:
        body = {
            "code": 0,
            "data": [
                {
                    "createTime": 1650545319746,
                    "createUser": request.query["userid"],
                    "createUserName": request.query["userid"],
                    "firstCreate": False,
                    "homeId": "781a0733923f2240cf304757",
                    "name": "My Home",
                    "type": "own",
                }
            ],
            "message": "success",
        }

        return web.json_response(body)

    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError

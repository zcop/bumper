"""Pim dictionary plugin module."""
import logging
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from bumper.web.plugins import WebserverPlugin


class DictionaryPlugin(WebserverPlugin):
    """Dictionary plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/dictionary/getErrDetail",
                _handle_get_err_detail,
            ),
        ]


async def _handle_get_err_detail(_: Request) -> Response:
    """Get error details."""
    try:
        body = {
            "code": -1,
            "data": [],
            "msg": "This errcode's detail is not exists",
        }
        return web.json_response(body)
    except Exception:  # pylint: disable=broad-except
        logging.error("An exception occurred during handling request.", exc_info=True)
    raise HTTPInternalServerError

"""Global plugin module."""
import logging
import os
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse
from aiohttp.web_routedef import AbstractRouteDef

from bumper import bumper_dir

from .. import WebserverPlugin


# pylint: disable=no-self-use
class GlobalPlugin(WebserverPlugin):
    """Global plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/global/{year}/{month}/{day}/{fileid}",
                self._handle_upload_global_file,
            ),
        ]

    async def _handle_upload_global_file(self, _: Request) -> StreamResponse:
        try:
            return web.FileResponse(
                os.path.join(
                    bumper_dir, "bumper", "web", "images", "robotvac_image.jpg"
                )
            )
        except Exception:  # pylint: disable=broad-except
            logging.error("Unexpected exception occurred", exc_info=True)

        raise HTTPInternalServerError

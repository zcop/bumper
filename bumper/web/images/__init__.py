"""Web image module."""
import logging
import os

from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_request import Request


async def get_bot_image(_: Request) -> FileResponse:
    """Return image of bot."""
    try:
        return FileResponse(
            os.path.join(os.path.dirname(__file__), "robotvac_image.jpg")
        )
    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError

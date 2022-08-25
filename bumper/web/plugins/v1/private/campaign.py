"""Campaign plugin module."""
from collections.abc import Iterable
from datetime import datetime, timedelta

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from bumper.util import convert_to_millis, get_current_time_as_millis

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class CampaignPlugin(WebserverPlugin):
    """Campaign plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}campaign/homePageAlert",
                _handle_home_page_alert,
            ),
        ]


async def _handle_home_page_alert(_: Request) -> Response:
    return get_success_response(
        {
            "clickSchemeUrl": None,
            "clickWebUrl": None,
            "hasCampaign": "N",
            "imageUrl": None,
            "nextAlertTime": convert_to_millis(
                (datetime.now() + timedelta(hours=12)).timestamp()
            ),
            "serverTime": get_current_time_as_millis(),
        }
    )

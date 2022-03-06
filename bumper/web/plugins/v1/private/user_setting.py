"""User setting plugin module."""

from typing import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class UserSettingPlugin(WebserverPlugin):
    """User setting plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}userSetting/getSuggestionSetting",
                _handle_get_suggestion_setting,
            ),
        ]


async def _handle_get_suggestion_setting(_: Request) -> Response:
    return get_success_response(
        {
            "acceptSuggestion": "Y",
            "itemList": [
                {
                    "name": "Aktionen/Angebote/Ereignisse",
                    "settingKey": "MARKETING",
                    "val": "Y",
                },
                {
                    "name": "Benutzerbefragung",
                    "settingKey": "QUESTIONNAIRE",
                    "val": "Y",
                },
                {
                    "name": "Produkt-Upgrade/Hilfe für Benutzer",
                    "settingKey": "INTRODUCTION",
                    "val": "Y",
                },
            ],
        }
    )

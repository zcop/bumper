"""Shop plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class ShopPlugin(WebserverPlugin):
    """Shop plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}shop/getCnWapShopConfig",
                _handle_get_cn_wap_shop_config,
            ),
        ]


async def _handle_get_cn_wap_shop_config(_: Request) -> Response:
    return get_success_response(
        {
            "myShopShowFlag": "N",
            "myShopUrl": "",
            "shopIndexShowFlag": "N",
            "shopIndexUrl": "",
        }
    )

"""Common plugin module."""
from collections.abc import Iterable

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class CommonPlugin(WebserverPlugin):
    """Common plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}common/getBottomNavigateInfoList",
                _handle_get_bottom_navigate_info_list,
            ),
        ]


async def _handle_get_bottom_navigate_info_list(_: Request) -> Response:
    return get_success_response(
        [
            {
                "iconId": "20220630090128_a52665b919e83a96326cfd8d1500989b",
                "iconName": "Roboter",
                "iconType": "ROBOT",
                "defaultImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302010444_8b161f90b4245f740e439fe5eee49de5.png",
                "lightImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302010449_8f17ad41995c874d4fe1028f8c61a233.png",
                "lightNameRgb": "#005EB8",
                "mediaType": None,
                "mediaUrl": "NULL",
                "positionType": "Robot",
                "tabItemActionUrl": None,
            },
            {
                "iconId": "20220630090128_0c7424cf783de485ca15a43fb1f4ddf8",
                "iconName": "Geschäft",
                "iconType": "MALL",
                "defaultImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302010612_7db1c568c734cfb708e55b9f1eb3d71c.png",
                "lightImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302010617_0da5c81774dcf27bb2e37c44a1691d88.png",
                "lightNameRgb": "#005EB8",
                "mediaType": None,
                "mediaUrl": "NULL",
                "positionType": "Store",
                "tabItemActionUrl": "https://www.ecovacs.com/it?utm_source=ecovacsGlobalApp&utm_medium=Appshopclick_IT&utm_campaign=Menu_IT",
            },
            {
                "iconId": "20220630090128_67c33cb9c3120c5448e2cda230a7abd1",
                "iconName": "Mein",
                "iconType": "MINE",
                "defaultImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302011202_a79a79b85247a6dff7e27356de1293bb.png",
                "lightImgUrl": "https://gl-us-pub.ecovacs.com/upload/global/2022/03/02/20220302011209_ff6592b7ae5b286f1bc3df52d9d5e7e3.png",
                "lightNameRgb": "#005EB8",
                "mediaType": None,
                "mediaUrl": "NULL",
                "positionType": "Mine",
                "tabItemActionUrl": None,
            },
        ]
    )

"""User plugin module."""
import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from bumper.db import check_token, user_by_deviceid, user_revoke_token
from bumper.web import auth_util

from ... import WebserverPlugin, get_success_response
from . import BASE_URL


class UserPlugin(WebserverPlugin):
    """User plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                f"{BASE_URL}user/login",
                auth_util.login,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/checkLogin",
                auth_util.login,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/getAuthCode",
                auth_util.get_authcode,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/logout",
                _logout,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/checkAgreement",
                _handle_check_agreement,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/checkAgreementBatch",
                _handle_check_agreement,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/getUserAccountInfo",
                _get_user_account_info,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/getUserMenuInfo",
                _handle_get_user_menu_info,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/changeArea",
                _handle_change_area,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/queryChangeArea",
                _handle_change_area,
            ),
            web.route(
                "*",
                f"{BASE_URL}user/acceptAgreementBatch",
                _handle_accept_agreement_batch,
            ),
        ]


async def _logout(request: Request) -> Response:
    try:
        user_device_id = request.match_info.get("devid", None)
        if user_device_id:
            user = user_by_deviceid(user_device_id)
            if user:
                if check_token(user["userid"], request.query["accessToken"]):
                    # Deactivate old tokens and authcodes
                    user_revoke_token(user["userid"], request.query["accessToken"])

        return get_success_response(None)

    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


async def _get_user_account_info(request: Request) -> Response:
    try:
        user_devid = request.match_info.get("devid", "")
        user = user_by_deviceid(user_devid)
        if user:
            username = f"fusername_{user['userid']}"
            return get_success_response(
                {
                    "email": "null@null.com",
                    "hasMobile": "N",
                    "hasPassword": "Y",
                    "uid": f"fuid_{user['userid']}",
                    "userName": username,
                    "obfuscatedMobile": None,
                    "mobile": None,
                    "loginName": username,
                }
            )

        # Example body
        # {
        # "code": "0000",
        # "data": {
        #     "email": "user@gmail.com",
        #     "hasMobile": "N",
        #     "hasPassword": "Y",
        #     "headIco": "",
        #     "loginName": "user@gmail.com",
        #     "mobile": null,
        #     "mobileAreaNo": null,
        #     "nickname": "",
        #     "obfuscatedMobile": null,
        #     "thirdLoginInfoList": [
        #     {
        #         "accountType": "WeChat",
        #         "hasBind": "N"
        #     }
        #     ],
        #     "uid": "20180719212155_*****",
        #     "userName": "EAY*****"
        # },
        # "msg": "操作成功",
        # "success": true,
        # "time": 1578203898343
        # }
    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


async def _handle_check_agreement(request: Request) -> Response:
    apptype = request.match_info.get("apptype", "")
    data = []
    if "global_" in apptype:
        data = [
            {
                "force": "N",
                "id": "20180804040641_7d746faf18b8cb22a50d145598fe4c90",
                "type": "USER",
                "url": "https://bumper.ecovacs.com/content/agreement?id=20180804040641_7d746faf18b8cb22a50d145598fe4c90&language=EN",  # "https://gl-us-wap.ecovacs.com/content/agreement?id=20180804040641_7d746faf18b8cb22a50d145598fe4c90&language=EN
                "version": "1.01",
            },
            {
                "force": "N",
                "id": "20180804040245_4e7c56dfb7ebd3b81b1f2747d0859fac",
                "type": "PRIVACY",
                "url": "https://bumper.ecovacs.com/content/agreement?id=20180804040245_4e7c56dfb7ebd3b81b1f2747d0859fac&language=EN",  # "https://gl-us-wap.ecovacs.com/content/agreement?id=20180804040245_4e7c56dfb7ebd3b81b1f2747d0859fac&language=EN"
                "version": "1.01",
            },
        ]

    return get_success_response(data)


async def _handle_get_user_menu_info(_: Request) -> Response:
    return get_success_response(
        [
            {
                "menuItems": [
                    {
                        "clickAction": 1,
                        "clickUri": "https://ecovacs.zendesk.com/hc/en-us",
                        "menuIconUrl": "https://gl-us-pub.ecovacs.com/upload/global/2019/12/16/2019121603180741b73907046e742b80e8fe4a90fe2498.png",
                        "menuId": "20191216031849_4d744630f7ad2f5208a4b8051be61d10",
                        "menuName": "Help & Feedback",
                        "paramsJson": "",
                    }
                ],
                "menuPositionKey": "A_FIRST",
            },
            {
                "menuItems": [
                    {
                        "clickAction": 3,
                        "clickUri": "robotShare",
                        "menuIconUrl": "https://gl-us-pub.ecovacs.com/upload/global/2019/12/16/2019121603284185e632ec6c5da10bd82119d7047a1f9e.png",
                        "menuId": "20191216032853_5fac4cc9cbd0e166dfa951485d1d8cc4",
                        "menuName": "Share Robot",
                        "paramsJson": "",
                    }
                ],
                "menuPositionKey": "B_SECOND",
            },
            {
                "menuItems": [
                    {
                        "clickAction": 3,
                        "clickUri": "config",
                        "menuIconUrl": "https://gl-us-pub.ecovacs.com/upload/global/2019/12/16/201912160325324068da4e4a09b8c3973db162e84784d5.png",
                        "menuId": "20191216032545_ebea0fbb4cb02d9c2fec5bdf3371bc2d",
                        "menuName": "Settings",
                        "paramsJson": "",
                    }
                ],
                "menuPositionKey": "C_THIRD",
            },
            {
                "menuItems": [
                    {
                        "clickAction": 1,
                        "clickUri": "https://bumper.ecovacs.com/",
                        "menuIconUrl": "https://gl-us-pub.ecovacs.com/upload/global/2019/12/16/201912160325324068da4e4a09b8c3973db162e84784d5.png",
                        "menuId": "20191216032545_ebea0fbb4cb02d9c2fec5bdf3371bc2c",
                        "menuName": "Bumper Status",
                        "paramsJson": "",
                    }
                ],
                "menuPositionKey": "D_FOURTH",
            },
        ]
    )


async def _handle_change_area(_: Request) -> Response:
    return get_success_response({"isNeedReLogin": "N"})


async def _handle_accept_agreement_batch(_: Request) -> Response:
    return get_success_response(None)

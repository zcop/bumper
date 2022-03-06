import logging
from typing import Iterable

from aiohttp import web
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis
from bumper.web import auth_util

from ... import WebserverPlugin


class UserPlugin(WebserverPlugin):
    """User plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        return [
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/login",
                auth_util.login,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/checkLogin",
                auth_util.login,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/getAuthCode",
                auth_util.get_authcode,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/logout",
                auth_util.logout,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/checkAgreement",
                self.handle_checkAgreement,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/checkAgreementBatch",
                self.handle_checkAgreement,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/getUserAccountInfo",
                auth_util.get_user_account_info,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/getUserMenuInfo",
                self.handle_getUserMenuInfo,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/changeArea",
                self.handle_changeArea,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/queryChangeArea",
                self.handle_changeArea,
            ),
            web.route(
                "*",
                "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/acceptAgreementBatch",
                self.handle_acceptAgreementBatch,
            ),
            # Direct register from app:
            # /{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/user/directRegister
            # Register by email
            # /registerByEmail
        ]

    async def handle_checkAgreement(self, request):
        try:
            apptype = request.match_info.get("apptype", "")
            if "global_" in apptype:
                body = {
                    "code": RETURN_API_SUCCESS,
                    "data": [
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
                    ],
                    "msg": "操作成功",
                    "success": True,
                    "time": get_current_time_as_millis(),
                }
            else:
                body = {
                    "code": RETURN_API_SUCCESS,
                    "data": [],
                    "msg": "操作成功",
                    "time": get_current_time_as_millis(),
                }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

    async def handle_getUserMenuInfo(self, request):
        try:
            apptype = request.match_info.get("apptype", "")
            body = {
                "code": "0000",
                "data": [
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
                ],
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

    async def handle_changeArea(self, request):
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": {"isNeedReLogin": "N"},
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

    async def handle_acceptAgreementBatch(self, request):
        try:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": None,
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        except Exception as e:
            logging.exception(f"{e}")

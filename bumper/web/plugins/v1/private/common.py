"""Common plugin module."""
import json
import logging
import os
from typing import Iterable

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis

from ... import WebserverPlugin


class CommonPlugin(WebserverPlugin):
    """Common plugin."""

    @property
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        base_url = "/{country}/{language}/{devid}/{apptype}/{appversion}/{devtype}/{aid}/common/"
        return [
            web.route(
                "*",
                f"{base_url}checkAPPVersion",
                _handle_check_app_version,
            ),
            web.route(
                "*",
                f"{base_url}checkVersion",
                _handle_check_version,
            ),
            web.route(
                "*",
                f"{base_url}uploadDeviceInfo",
                _handle_upload_device_info,
            ),
            web.route(
                "*",
                f"{base_url}getSystemReminder",
                _handle_get_system_reminder,
            ),
            web.route(
                "*",
                f"{base_url}getConfig",
                _handle_get_config,
            ),
            web.route(
                "*",
                f"{base_url}getAreas",
                _handle_get_areas,
            ),
            web.route(
                "*",
                f"{base_url}getAgreementURLBatch",
                _handle_get_agreement_url_batch,
            ),
            web.route(
                "*",
                f"{base_url}getTimestamp",
                _handle_get_timestamp,
            ),
        ]


async def _handle_check_version(_: Request) -> Response:
    body = {
        "code": RETURN_API_SUCCESS,
        "data": {
            "c": None,
            "img": None,
            "r": 0,
            "t": None,
            "u": None,
            "ut": 0,
            "v": None,
        },
        "msg": "操作成功",
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)


async def _handle_check_app_version(_: Request) -> Response:
    body = {
        "code": RETURN_API_SUCCESS,
        "data": {
            "c": None,
            "downPageUrl": None,
            "img": None,
            "nextAlertTime": None,
            "r": 0,
            "t": None,
            "u": None,
            "ut": 0,
            "v": None,
        },
        "msg": "操作成功",
        "success": True,
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)


async def _handle_upload_device_info(_: Request) -> Response:
    body = {
        "code": RETURN_API_SUCCESS,
        "data": None,
        "msg": "操作成功",
        "success": True,
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)


async def _handle_get_system_reminder(_: Request) -> Response:
    body = {
        "code": RETURN_API_SUCCESS,
        "data": {
            "iosGradeTime": {"iodGradeFlag": "N"},
            "openNotification": {
                "openNotificationContent": None,
                "openNotificationFlag": "N",
                "openNotificationTitle": None,
            },
        },
        "msg": "操作成功",
        "success": True,
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)


async def _handle_get_config(request: Request) -> Response:
    try:
        data = []
        for key in request.query["keys"].split(","):
            data.append({"key": key, "value": "Y"})

        body = {
            "code": RETURN_API_SUCCESS,
            "data": data,
            "msg": "操作成功",
            "success": True,
            "time": get_current_time_as_millis(),
        }

        return web.json_response(body)
    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


async def _handle_get_areas(_: Request) -> Response:
    try:
        with open(os.path.join(os.path.dirname(__file__), "area.json")) as file:
            body = {
                "code": RETURN_API_SUCCESS,
                "data": json.load(file),
                "msg": "操作成功",
                "success": True,
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)
    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


async def _handle_get_agreement_url_batch(_: Request) -> Response:
    body = {
        "code": RETURN_API_SUCCESS,
        "data": [
            {
                "acceptTime": None,
                "force": None,
                "id": "20180804040641_7d746faf18b8cb22a50d145598fe4c90",
                "type": "USER",
                "url": "https://gl-eu-wap.ecovacs.com/content/agreement?id=20180804040641_7d746faf18b8cb22a50d145598fe4c90&language=EN",
                "version": "1.03",
            },
            {
                "acceptTime": None,
                "force": None,
                "id": "20180804040245_4e7c56dfb7ebd3b81b1f2747d0859fac",
                "type": "PRIVACY",
                "url": "https://gl-eu-wap.ecovacs.com/content/agreement?id=20180804040245_4e7c56dfb7ebd3b81b1f2747d0859fac&language=EN",
                "version": "1.03",
            },
        ],
        "msg": "操作成功",
        "success": True,
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)


async def _handle_get_timestamp(_: Request) -> Response:
    time = get_current_time_as_millis()
    body = {
        "code": RETURN_API_SUCCESS,
        "data": {"timestamp": time},
        "msg": "操作成功",
        "success": True,
        "time": time,
    }

    return web.json_response(body)

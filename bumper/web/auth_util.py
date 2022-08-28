"""Auth util module."""
import logging
import uuid
from typing import Any

from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from bumper import db, use_auth
from bumper.db import (
    _db_get,
    user_add,
    user_add_authcode,
    user_add_bot,
    user_add_device,
    user_add_token,
    user_by_device_id,
    user_get,
    user_get_token,
    user_revoke_expired_tokens,
)
from bumper.models import (
    API_ERRORS,
    ERR_TOKEN_INVALID,
    ERR_USER_NOT_ACTIVATED,
    RETURN_API_SUCCESS,
)
from bumper.util import get_current_time_as_millis
from bumper.web.plugins import get_success_response
from bumper.web.server import _LOGGER


def _generate_token(user: dict[str, Any]) -> str:
    """Generate token."""
    token = uuid.uuid4().hex
    user_add_token(user["userid"], token)
    return token


def _generate_authcode(user: dict[str, Any], countrycode: str, token: str) -> str:
    """Generate auth token."""
    tmpauthcode = f"{countrycode}_{uuid.uuid4().hex}"
    user_add_authcode(user["userid"], token, tmpauthcode)
    return tmpauthcode


async def login(request: Request) -> Response:
    """Perform login."""
    try:
        user_devid = request.match_info.get("devid", "")
        countrycode = request.match_info.get("country", "us")
        apptype = request.match_info.get("apptype", "")
        _LOGGER.info("Client with devid %s attempting login", user_devid)
        if use_auth:
            if user_devid != "":
                # Performing basic "auth" using devid, super insecure
                user = user_by_device_id(user_devid)
                if user:
                    if "checkLogin" in request.path:
                        return web.json_response(
                            _check_token(
                                apptype, countrycode, user, request.query["accessToken"]
                            )[1]
                        )

                    # Deactivate old tokens and authcodes
                    user_revoke_expired_tokens(user["userid"])

                    body = {
                        "code": API_ERRORS[RETURN_API_SUCCESS],
                        "data": _get_login_details(
                            apptype, countrycode, user, _generate_token(user)
                        ),
                        "msg": "操作成功",
                        "time": get_current_time_as_millis(),
                    }
                    return web.json_response(body)

            return web.json_response(
                {
                    "code": ERR_USER_NOT_ACTIVATED,
                    "data": None,
                    "msg": "当前密码错误",
                    "time": get_current_time_as_millis(),
                }
            )

        return web.json_response(_auth_any(user_devid, apptype, countrycode, request))
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("An exception occurred", exc_info=True)

    raise HTTPInternalServerError


async def get_authcode(request: Request) -> Response:
    """Get auth code."""
    try:  # pylint: disable=too-many-nested-blocks
        user_devid = request.match_info.get("devid", None)  # Ecovacs
        if not user_devid:
            user_devid = request.query["deviceId"]  # Ecovacs Home

        if user_devid:
            user = user_by_device_id(user_devid)
            if user:
                if "accessToken" in request.query:
                    token = user_get_token(user["userid"], request.query["accessToken"])
                    if token:
                        if "authcode" in token:
                            authcode = token["authcode"]
                        else:
                            authcode = _generate_authcode(
                                user,
                                request.match_info.get("country", "us"),
                                request.query["accessToken"],
                            )

                        data = {
                            "authCode": authcode,
                            "ecovacsUid": request.query["uid"],
                        }

                        return get_success_response(data)

        body = {
            "code": ERR_TOKEN_INVALID,
            "data": None,
            "msg": "当前密码错误",
            "time": get_current_time_as_millis(),
        }

        return web.json_response(body)

    except Exception:  # pylint: disable=broad-except
        logging.error("Unexpected exception occurred", exc_info=True)

    raise HTTPInternalServerError


def _check_token(
    apptype: str, countrycode: str, user: dict[str, Any], token: str
) -> tuple[bool, dict[str, Any]]:
    if db.check_token(user["userid"], token):
        return (
            True,
            {
                "code": RETURN_API_SUCCESS,
                "data": _get_login_details(apptype, countrycode, user, token),
                "msg": "操作成功",
                "time": get_current_time_as_millis(),
            },
        )

    return (
        False,
        {
            "code": ERR_TOKEN_INVALID,
            "data": None,
            "msg": "当前密码错误",
            "time": get_current_time_as_millis(),
        },
    )


def _auth_any(
    devid: str, apptype: str, country: str, request: Request
) -> dict[str, Any]:
    user_devid = devid
    countrycode = country
    user = user_by_device_id(user_devid)
    bots = _db_get().table("bots").all()

    if not user:
        user_add("tmpuser")  # Add a new user
        tmp = user_get("tmpuser")
        assert tmp
        user = tmp

    token = _generate_token(user)
    user_add_device(user["userid"], user_devid)

    for bot in bots:  # Add all bots to the user
        if "did" in bot:
            user_add_bot(user["userid"], bot["did"])
        else:
            _LOGGER.error("No DID for bot: %s", bot)

    if "checkLogin" in request.path:  # If request was to check a token do so
        (success, body) = _check_token(
            apptype, countrycode, user, request.query["accessToken"]
        )
        if success:
            return body

    # Deactivate old tokens and authcodes
    user_revoke_expired_tokens(user["userid"])

    body = {
        "code": RETURN_API_SUCCESS,
        "data": _get_login_details(apptype, countrycode, user, token),
        "msg": "操作成功",
        "time": get_current_time_as_millis(),
    }

    return body


def _get_login_details(
    apptype: str, countrycode: str, user: dict[str, Any], token: str
) -> dict[str, Any]:
    details: dict[str, Any] = {
        "accessToken": token,
        "uid": f"fuid_{user['userid']}",
        "username": f"fusername_{user['userid']}",
        "country": countrycode,
        "email": "null@null.com",
    }

    if "global_" in apptype:
        details.update(
            {"ucUid": details["uid"], "loginName": details["username"], "mobile": None}
        )

    return details

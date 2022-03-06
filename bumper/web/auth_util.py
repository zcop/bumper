"""Auth util module."""
import json
import uuid

from aiohttp import web

from bumper import db, use_auth
from bumper.db import (
    db_get,
    user_add,
    user_add_authcode,
    user_add_bot,
    user_add_device,
    user_add_token,
    user_by_deviceid,
    user_get,
    user_get_token,
    user_revoke_expired_tokens,
    user_revoke_token,
)
from bumper.models import (
    API_ERRORS,
    ERR_TOKEN_INVALID,
    ERR_USER_NOT_ACTIVATED,
    RETURN_API_SUCCESS,
    EcoVacs_Login,
    EcoVacsHome_Login,
)
from bumper.util import get_current_time_as_millis, get_logger

_logger = get_logger("confserver")


def generate_token(user):
    try:
        tmpaccesstoken = uuid.uuid4().hex
        user_add_token(user["userid"], tmpaccesstoken)
        return tmpaccesstoken

    except Exception as e:
        _logger.exception(f"{e}")


def generate_authcode(user, countrycode, token):
    try:
        tmpauthcode = f"{countrycode}_{uuid.uuid4().hex}"
        user_add_authcode(user["userid"], token, tmpauthcode)
        return tmpauthcode

    except Exception as e:
        _logger.exception(f"{e}")


async def login(request):
    try:
        user_devid = request.match_info.get("devid", "")
        countrycode = request.match_info.get("country", "us")
        apptype = request.match_info.get("apptype", "")
        _logger.info(f"client with devid {user_devid} attempting login")
        if use_auth:
            if (
                not user_devid == ""
            ):  # Performing basic "auth" using devid, super insecure
                user = user_by_deviceid(user_devid)
                if "checkLogin" in request.path:
                    check_token(
                        apptype, countrycode, user, request.query["accessToken"]
                    )
                else:
                    if "global_" in apptype:  # EcoVacs Home
                        login_details = EcoVacsHome_Login()
                        login_details.ucUid = "fuid_{}".format(user["userid"])
                        login_details.loginName = "fusername_{}".format(user["userid"])
                        login_details.mobile = None

                    else:
                        login_details = EcoVacs_Login()

                    # Deactivate old tokens and authcodes
                    user_revoke_expired_tokens(user["userid"])

                    login_details.accessToken = generate_token(user)
                    login_details.uid = "fuid_{}".format(user["userid"])
                    login_details.username = "fusername_{}".format(user["userid"])
                    login_details.country = countrycode
                    login_details.email = "null@null.com"

                    body = {
                        "code": API_ERRORS[RETURN_API_SUCCESS],
                        "data": json.loads(login_details.toJSON()),
                        # {
                        #    "accessToken": self.generate_token(tmpuser),  # Generate a token
                        #    "country": countrycode,
                        #    "email": "null@null.com",
                        #    "uid": "fuid_{}".format(tmpuser["userid"]),
                        #    "username": "fusername_{}".format(tmpuser["userid"]),
                        # },
                        "msg": "操作成功",
                        "time": get_current_time_as_millis(),
                    }

                    return web.json_response(body)

            body = {
                "code": ERR_USER_NOT_ACTIVATED,
                "data": None,
                "msg": "当前密码错误",
                "time": get_current_time_as_millis(),
            }

            return web.json_response(body)

        else:
            return web.json_response(
                _auth_any(user_devid, apptype, countrycode, request)
            )

    except Exception as e:
        _logger.exception(f"{e}")


async def get_authcode(request):
    try:
        apptype = request.match_info.get("apptype", "")
        user_devid = request.match_info.get("devid", "")  # Ecovacs
        if user_devid == "":
            user_devid = request.query["deviceId"]  # Ecovacs Home

        if not user_devid == "":
            user = user_by_deviceid(user_devid)
            token = ""
            if user:
                if "accessToken" in request.query:
                    token = user_get_token(user["userid"], request.query["accessToken"])
                if token:
                    authcode = ""
                    if not "authcode" in token:
                        authcode = generate_authcode(
                            user,
                            request.match_info.get("country", "us"),
                            request.query["accessToken"],
                        )
                    else:
                        authcode = token["authcode"]
                    if "global" in apptype:
                        body = {
                            "code": RETURN_API_SUCCESS,
                            "data": {
                                "authCode": authcode,
                                "ecovacsUid": request.query["uid"],
                            },
                            "msg": "操作成功",
                            "success": True,
                            "time": get_current_time_as_millis(),
                        }
                    else:
                        body = {
                            "code": RETURN_API_SUCCESS,
                            "data": {
                                "authCode": authcode,
                                "ecovacsUid": request.query["uid"],
                            },
                            "msg": "操作成功",
                            "time": get_current_time_as_millis(),
                        }
                    return web.json_response(body)

        body = {
            "code": ERR_TOKEN_INVALID,
            "data": None,
            "msg": "当前密码错误",
            "time": get_current_time_as_millis(),
        }

        return web.json_response(body)

    except Exception as e:
        _logger.exception(f"{e}")


def check_token(apptype, countrycode, user, token):
    try:
        if db.check_token(user["userid"], token):

            if "global_" in apptype:  # EcoVacs Home
                login_details = EcoVacsHome_Login()
                login_details.ucUid = "fuid_{}".format(user["userid"])
                login_details.loginName = "fusername_{}".format(user["userid"])
                login_details.mobile = None
            else:
                login_details = EcoVacs_Login()

            login_details.accessToken = token
            login_details.uid = "fuid_{}".format(user["userid"])
            login_details.username = "fusername_{}".format(user["userid"])
            login_details.country = countrycode
            login_details.email = "null@null.com"

            body = {
                "code": RETURN_API_SUCCESS,
                "data": json.loads(login_details.toJSON()),
                # {
                #    "accessToken": self.generate_token(tmpuser),  # Generate a token
                #    "country": countrycode,
                #    "email": "null@null.com",
                #    "uid": "fuid_{}".format(tmpuser["userid"]),
                #    "username": "fusername_{}".format(tmpuser["userid"]),
                # },
                "msg": "操作成功",
                "time": get_current_time_as_millis(),
            }
            return web.json_response(body)

        else:
            body = {
                "code": ERR_TOKEN_INVALID,
                "data": None,
                "msg": "当前密码错误",
                "time": get_current_time_as_millis(),
            }
            return web.json_response(body)

    except Exception as e:
        _logger.exception(f"{e}")


def _auth_any(devid, apptype, country, request):
    try:
        user_devid = devid
        countrycode = country
        user = user_by_deviceid(user_devid)
        bots = db_get().table("bots").all()

        if user:  # Default to user 0
            tmpuser = user
            if "global_" in apptype:  # EcoVacs Home
                login_details = EcoVacsHome_Login()
                login_details.ucUid = "fuid_{}".format(tmpuser["userid"])
                login_details.loginName = "fusername_{}".format(tmpuser["userid"])
                login_details.mobile = None
            else:
                login_details = EcoVacs_Login()

            login_details.accessToken = generate_token(tmpuser)
            login_details.uid = "fuid_{}".format(tmpuser["userid"])
            login_details.username = "fusername_{}".format(tmpuser["userid"])
            login_details.country = countrycode
            login_details.email = "null@null.com"
            user_add_device(tmpuser["userid"], user_devid)
        else:
            user_add("tmpuser")  # Add a new user
            tmpuser = user_get("tmpuser")
            if "global_" in apptype:  # EcoVacs Home
                login_details = EcoVacsHome_Login()
                login_details.ucUid = "fuid_{}".format(tmpuser["userid"])
                login_details.loginName = "fusername_{}".format(tmpuser["userid"])
                login_details.mobile = None
            else:
                login_details = EcoVacs_Login()

            login_details.accessToken = generate_token(tmpuser)
            login_details.uid = "fuid_{}".format(tmpuser["userid"])
            login_details.username = "fusername_{}".format(tmpuser["userid"])
            login_details.country = countrycode
            login_details.email = "null@null.com"
            user_add_device(tmpuser["userid"], user_devid)

        for bot in bots:  # Add all bots to the user
            if "did" in bot:
                user_add_bot(tmpuser["userid"], bot["did"])
            else:
                _logger.error(f"No DID for bot: {bot}")

        if "checkLogin" in request.path:  # If request was to check a token do so
            checkToken = check_token(
                apptype, countrycode, tmpuser, request.query["accessToken"]
            )
            isGood = json.loads(checkToken.text)
            if isGood["code"] == "0000":
                return isGood

        # Deactivate old tokens and authcodes
        user_revoke_expired_tokens(tmpuser["userid"])

        body = {
            "code": RETURN_API_SUCCESS,
            "data": json.loads(login_details.toJSON()),
            # {
            #    "accessToken": self.generate_token(tmpuser),  # Generate a token
            #    "country": countrycode,
            #    "email": "null@null.com",
            #    "uid": "fuid_{}".format(tmpuser["userid"]),
            #    "username": "fusername_{}".format(tmpuser["userid"]),
            # },
            "msg": "操作成功",
            "time": get_current_time_as_millis(),
        }

        return body

    except Exception as e:
        _logger.exception(f"{e}")


def get_user_account_info(request):
    try:
        user_devid = request.match_info.get("devid", "")
        countrycode = request.match_info.get("country", "us")
        apptype = request.match_info.get("apptype", "")
        user = user_by_deviceid(user_devid)

        if "global_" in apptype:  # EcoVacs Home
            login_details = EcoVacsHome_Login()
            login_details.ucUid = "fuid_{}".format(user["userid"])
            login_details.loginName = "fusername_{}".format(user["userid"])
            login_details.mobile = None
        else:
            login_details = EcoVacs_Login()

        login_details.uid = "fuid_{}".format(user["userid"])
        login_details.username = "fusername_{}".format(user["userid"])
        login_details.country = countrycode
        login_details.email = "null@null.com"

        body = {
            "code": RETURN_API_SUCCESS,
            "data": {
                "email": login_details.email,
                "hasMobile": "N",
                "hasPassword": "Y",
                "uid": login_details.uid,
                "userName": login_details.username,
                "obfuscatedMobile": None,
                "mobile": None,
                "loginName": login_details.loginName,
            },
            "msg": "操作成功",
            "time": get_current_time_as_millis(),
        }

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

        return web.json_response(body)

    except Exception as e:
        _logger.exception(f"{e}")


async def logout(request):
    try:
        user_devid = request.match_info.get("devid", "")
        if not user_devid == "":
            user = user_by_deviceid(user_devid)
            if user:
                if db.check_token(user["userid"], request.query["accessToken"]):
                    # Deactivate old tokens and authcodes
                    user_revoke_token(user["userid"], request.query["accessToken"])

        body = {
            "code": RETURN_API_SUCCESS,
            "data": None,
            "msg": "操作成功",
            "time": get_current_time_as_millis(),
        }

        return web.json_response(body)

    except Exception as e:
        _logger.exception(f"{e}")

import asyncio
import json
import os
from unittest import mock

import pytest

import bumper
from bumper import HelperBot, WebServer, WebserverBinding, XMPPServer, db
from bumper.models import ERR_TOKEN_INVALID, RETURN_API_SUCCESS
from tests import HOST, MQTT_PORT, WEBSERVER_PORT


def create_webserver():
    return WebServer(WebserverBinding(HOST, WEBSERVER_PORT, False))


def async_return(result):
    f = asyncio.Future()
    f.set_result(result)
    return f


def remove_existing_db():
    if os.path.exists("tests/tmp.db"):
        os.remove("tests/tmp.db")  # Remove existing db


async def test_webserver_ssl():
    webserver = WebServer(WebserverBinding(HOST, WEBSERVER_PORT, True))
    await webserver.start()


async def test_webserver_no_ssl():
    webserver = WebServer(WebserverBinding(HOST, 11112, False))
    await webserver.start()


@pytest.mark.usefixtures("helper_bot")
async def test_base(webserver_client):
    remove_existing_db()

    # Start XMPP
    xmpp_server = XMPPServer(HOST, 5223)
    bumper.xmpp_server = xmpp_server
    await xmpp_server.start_async_server()

    resp = await webserver_client.get("/")
    assert resp.status == 200

    bumper.xmpp_server.disconnect()


@pytest.mark.usefixtures("helper_bot")
async def test_restartService(webserver_client):
    remove_existing_db()

    # Start XMPP
    xmpp_server = XMPPServer(HOST, 5223)
    bumper.xmpp_server = xmpp_server
    await xmpp_server.start_async_server()

    resp = await webserver_client.get("/restart_Helperbot")
    assert resp.status == 200

    resp = await webserver_client.get("/restart_MQTTServer")
    assert resp.status == 200

    resp = await webserver_client.get("/restart_XMPPServer")
    assert resp.status == 200

    xmpp_server.disconnect()


async def test_RemoveBot(webserver_client):
    resp = await webserver_client.get("/bot/remove/test_did")
    assert resp.status == 200


async def test_RemoveClient(webserver_client):
    resp = await webserver_client.get("/client/remove/test_resource")
    assert resp.status == 200


async def test_login(webserver_client):
    remove_existing_db()

    # Test without user
    resp = await webserver_client.get("/v1/private/us/en/dev_1234/ios/1/0/0/user/login")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    remove_existing_db()

    # Test global_e without user
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/user/login"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Add a user to db and test with existing users
    db.user_add("testuser")
    resp = await webserver_client.get("/v1/private/us/en/dev_1234/ios/1/0/0/user/login")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Add a bot to db that will be added to user
    db.bot_add("sn_123", "did_123", "dev_123", "res_123", "com_123")
    resp = await webserver_client.get("/v1/private/us/en/dev_1234/ios/1/0/0/user/login")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Add a bot to db that doesn't have a did
    newbot = {
        "class": "dev_1234",
        "company": "com_123",
        # "did": self.did,
        "name": "sn_1234",
        "resource": "res_1234",
    }
    db.bot_full_upsert(newbot)

    resp = await webserver_client.get("/v1/private/us/en/dev_1234/ios/1/0/0/user/login")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]


async def test_logout(webserver_client):
    remove_existing_db()

    # Add a token to user and test
    db.user_add("testuser")
    db.user_add_device("testuser", "dev_1234")
    db.user_add_token("testuser", "token_1234")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/logout?accessToken={}".format(
            "token_1234"
        )
    )

    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_checkLogin(webserver_client):
    remove_existing_db()

    # Test without token
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/checkLogin?accessToken={}".format(
            None
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert jsonresp["data"]["accessToken"] != "token_1234"
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Add a user to db and test with existing users
    db.user_add("testuser")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/checkLogin?accessToken={}".format(
            None
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert jsonresp["data"]["accessToken"] != "token_1234"
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Test again using global_e app
    db.user_add("testuser")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/user/checkLogin?accessToken={}".format(
            None
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert jsonresp["data"]["accessToken"] != "token_1234"
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Remove dev from tmpuser
    db.user_remove_device("tmpuser", "dev_1234")

    # Add a token to user and test
    db.user_add("testuser")
    db.user_add_device("testuser", "dev_1234")
    db.user_add_token("testuser", "token_1234")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/checkLogin?accessToken={}".format(
            "token_1234"
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert jsonresp["data"]["accessToken"] == "token_1234"
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]

    # Test again using global_e app
    db.user_add("testuser")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/user/checkLogin?accessToken={}".format(
            "token_1234"
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "accessToken" in jsonresp["data"]
    assert jsonresp["data"]["accessToken"] == "token_1234"
    assert "uid" in jsonresp["data"]
    assert "username" in jsonresp["data"]


async def test_getAuthCode(webserver_client):
    remove_existing_db()

    # Test without user or token
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/getAuthCode?uid={}&accessToken={}".format(
            None, None
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == ERR_TOKEN_INVALID

    # Test as global_e
    resp = await webserver_client.get(
        "/v1/global/auth/getAuthCode?uid={}&deviceId={}".format(None, "dev_1234")
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == ERR_TOKEN_INVALID

    # Add a token to user and test
    db.user_add("testuser")
    db.user_add_device("testuser", "dev_1234")
    db.user_add_token("testuser", "token_1234")
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/getAuthCode?uid={}&accessToken={}".format(
            "testuser", "token_1234"
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "authCode" in jsonresp["data"]
    assert "ecovacsUid" in jsonresp["data"]

    # The above should have added an authcode to token, try again to test with existing authcode
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/getAuthCode?uid={}&accessToken={}".format(
            "testuser", "token_1234"
        )
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS
    assert "authCode" in jsonresp["data"]
    assert "ecovacsUid" in jsonresp["data"]


async def test_checkAgreement(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/user/checkAgreement"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS

    # Test as global_e
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/user/checkAgreement"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_homePageAlert(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/campaign/homePageAlert"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_checkVersion(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/common/checkVersion"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_checkAppVersion(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/common/checkAPPVersion"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_uploadDeviceInfo(webserver_client):
    remove_existing_db()
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/common/uploadDeviceInfo"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_getAdByPositionType(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/ad/getAdByPositionType"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_getBootScreen(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/ad/getBootScreen"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_hasUnreadMsg(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/message/hasUnreadMsg"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_getMsgList(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/message/getMsgList"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_getSystemReminder(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/common/getSystemReminder"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_getCnWapShopConfig(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/shop/getCnWapShopConfig"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_neng_hasUnreadMessage(webserver_client):
    remove_existing_db()

    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "ecoglobe",
            "token": "us_token",
            "userid": "user123",
            "with": "users",
        },
        "count": 20,
    }
    resp = await webserver_client.post("/api/neng/message/hasUnreadMsg", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == 0


async def test_getProductIotMap(webserver_client):
    remove_existing_db()

    resp = await webserver_client.post("/api/pim/product/getProductIotMap")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS


async def test_pim_file(webserver_client):
    resp = await webserver_client.get("/api/pim/file/get/123")
    assert resp.status == 200


async def test_getUsersAPI(webserver_client):
    remove_existing_db()

    resp = await webserver_client.get("/api/users/user.do")
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "fail"


async def test_getUserAccountInfo(webserver_client):
    remove_existing_db()
    db.user_add("testuser")
    db.user_add_device("testuser", "dev_1234")
    db.user_add_token("testuser", "token_1234")
    db.user_add_authcode("testuser", "token_1234", "auth_1234")
    db.user_add_bot("testuser", "did_1234")
    db.bot_add("sn_1234", "did_1234", "class_1234", "res_1234", "com_1234")

    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/global_e/1/0/0/user/getUserAccountInfo"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == "0000"
    assert jsonresp["msg"] == "操作成功"
    assert jsonresp["data"]["userName"] == "fusername_testuser"


async def test_postUsersAPI(webserver_client):
    remove_existing_db()

    # Test FindBest
    postbody = {"todo": "FindBest", "service": "EcoMsgNew"}
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test EcoUpdate
    postbody = {"todo": "FindBest", "service": "EcoUpdate"}
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test loginByItToken - Uses the authcode
    db.user_add("testuser")
    db.user_add_device("testuser", "dev_1234")
    db.user_add_token("testuser", "token_1234")
    db.user_add_authcode("testuser", "token_1234", "auth_1234")
    db.user_add_bot("testuser", "did_1234")
    db.bot_add("sn_1234", "did_1234", "class_1234", "res_1234", "com_1234")
    # Test
    postbody = {
        "country": "US",
        "last": "",
        "realm": "ecouser.net",
        "resource": "dev_1234",
        "todo": "loginByItToken",
        "token": "auth_1234",
        "userId": "testuser",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test as EcoVacs Home (global_e)
    postbody = {
        "country": "US",
        "edition": "ECOGLOBLE",
        "last": "",
        "org": "ECOWW",
        "resource": "dev_1234",
        "todo": "loginByItToken",
        "token": "auth_1234",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test as EcoVacs Home (global_e) & Post Form
    postbody = {
        "country": "US",
        "edition": "ECOGLOBLE",
        "last": "",
        "org": "ECOWW",
        "resource": "dev_1234",
        "todo": "loginByItToken",
        "token": "auth_1234",
    }
    resp = await webserver_client.post("/api/users/user.do", data=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test GetDeviceList
    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "dev_1234",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "todo": "GetDeviceList",
        "userid": "testuser",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test SetDeviceNick
    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "dev_1234",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "todo": "SetDeviceNick",
        "nick": "botnick",
        "did": "did_1234",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test AddOneDevice - Same as set nick for some bots
    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "dev_1234",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "todo": "AddOneDevice",
        "nick": "botnick",
        "did": "did_1234",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"

    # Test DeleteOneDevice - remove bot
    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "dev_1234",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "todo": "DeleteOneDevice",
        "did": "did_1234",
    }
    resp = await webserver_client.post("/api/users/user.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["result"] == "ok"


async def test_appsvr_api(webserver_client):
    remove_existing_db()

    # Test GetGlobalDeviceList
    postbody = {
        "aliliving": False,
        "appVer": "1.1.6",
        "auth": {
            "realm": "ecouser.net",
            "resource": "ECOGLOBLEac5ae987",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "channel": "google_play",
        "defaultLang": "en",
        "lang": "en",
        "platform": "Android",
        "todo": "GetGlobalDeviceList",
        "userid": "testuser",
    }
    resp = await webserver_client.post("/api/appsvr/app.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["ret"] == "ok"

    db.bot_add("sn_1234", "did_1234", "ls1ok3", "res_1234", "eco-ng")

    # Test again with bot added
    resp = await webserver_client.post("/api/appsvr/app.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["ret"] == "ok"


async def test_lg_logs(webserver_client, helper_bot: HelperBot):
    remove_existing_db()
    db.bot_add("sn_1234", "did_1234", "ls1ok3", "res_1234", "eco-ng")
    db.bot_set_mqtt("did_1234", True)
    confserver = create_webserver()

    # Test return get status
    command_getstatus_resp = {
        "id": "resp_1234",
        "resp": "<ctl ret='ok' status='idle'/>",
        "ret": "ok",
    }
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_getstatus_resp)
    )

    # Test GetGlobalDeviceList
    postbody = {
        "auth": {
            "realm": "ecouser.net",
            "resource": "ECOGLOBLEac5ae987",
            "token": "token_1234",
            "userid": "testuser",
            "with": "users",
        },
        "did": "did_1234",
        "resource": "res_1234",
        "td": "GetCleanLogs",
    }
    resp = await webserver_client.post("/api/lg/log.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["ret"] == "ok"


async def test_postLookup(webserver_client):
    remove_existing_db()

    # Test FindBest
    postbody = {"todo": "FindBest", "service": "EcoMsgNew"}
    resp = await webserver_client.post("/lookup.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["result"] == "ok"

    # Test EcoUpdate
    postbody = {"todo": "FindBest", "service": "EcoUpdate"}
    resp = await webserver_client.post("/lookup.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["result"] == "ok"


async def test_devmgr(webserver_client, helper_bot: HelperBot):
    remove_existing_db()
    confserver = create_webserver()

    # Test PollSCResult
    postbody = {"td": "PollSCResult"}
    resp = await webserver_client.post("/api/iot/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"

    # Test HasUnreadMsg
    postbody = {"td": "HasUnreadMsg"}
    resp = await webserver_client.post("/api/iot/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"
    assert test_resp["unRead"] == False

    # Test BotCommand
    db.bot_add("sn_1234", "did_1234", "dev_1234", "res_1234", "eco-ng")
    db.bot_set_mqtt("did_1234", True)
    postbody = {"toId": "did_1234"}

    # Test return get status
    command_getstatus_resp = {
        "id": "resp_1234",
        "resp": "<ctl ret='ok' status='idle'/>",
        "ret": "ok",
    }
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_getstatus_resp)
    )
    resp = await webserver_client.post("/api/iot/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"

    # Test return fail timeout
    command_timeout_resp = {"id": "resp_1234", "errno": "timeout", "ret": "fail"}
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_timeout_resp)
    )
    resp = await webserver_client.post("/api/iot/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "fail"


async def test_dim_devmanager(webserver_client, helper_bot: HelperBot):
    remove_existing_db()
    confserver = create_webserver()

    # Test PollSCResult
    postbody = {"td": "PollSCResult"}
    resp = await webserver_client.post("/api/dim/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"

    # Test HasUnreadMsg
    postbody = {"td": "HasUnreadMsg"}
    resp = await webserver_client.post("/api/dim/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"
    assert test_resp["unRead"] == False

    # Test BotCommand
    db.bot_add("sn_1234", "did_1234", "dev_1234", "res_1234", "eco-ng")
    db.bot_set_mqtt("did_1234", True)
    postbody = {"toId": "did_1234"}

    # Test return get status
    command_getstatus_resp = {
        "id": "resp_1234",
        "resp": "<ctl ret='ok' status='idle'/>",
        "ret": "ok",
    }
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_getstatus_resp)
    )
    resp = await webserver_client.post("/api/dim/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "ok"

    # Test return fail timeout
    command_timeout_resp = {"id": "resp_1234", "errno": "timeout", "ret": "fail"}
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_timeout_resp)
    )
    resp = await webserver_client.post("/api/dim/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "fail"
    assert test_resp["errno"] == "timeout"

    # Set bot not on mqtt
    db.bot_set_mqtt("did_1234", False)
    helper_bot.send_command = mock.MagicMock(
        return_value=async_return(command_getstatus_resp)
    )
    resp = await webserver_client.post("/api/dim/devmanager.do", json=postbody)
    assert resp.status == 200
    text = await resp.text()
    test_resp = json.loads(text)
    assert test_resp["ret"] == "fail"

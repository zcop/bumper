import asyncio
import os
import time

import amqtt
import pytest
from amqtt.mqtt.constants import QOS_0
from testfixtures import LogCapture

import bumper
from tests import HOST, MQTT_PORT


@pytest.mark.usefixtures("mqtt_server")
async def test_helperbot_message():
    with LogCapture() as l:

        # Test broadcast message
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        msg_payload = "<ctl ts='1547822804960' td='DustCaseST' st='0'/>"
        msg_topic_name = "iot/atr/DustCaseST/bot_serial/ls1ok3/wC3g/x"
        await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

        await asyncio.sleep(0.1)

        l.check_present(
            (
                "helperbot",
                "DEBUG",
                "Received Broadcast - Topic: iot/atr/DustCaseST/bot_serial/ls1ok3/wC3g/x - Message: <ctl ts='1547822804960' td='DustCaseST' st='0'/>",
            )
        )  # Check broadcast message was logged
        l.clear()
        await mqtt_helperbot.Client.disconnect()

        # Send command to bot
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        msg_payload = "{}"
        msg_topic_name = "iot/p2p/GetWKVer/helperbot/bumper/helperbot/bot_serial/ls1ok3/wC3g/q/iCmuqp/j"
        await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

        await asyncio.sleep(0.1)

        l.check_present(
            (
                "helperbot",
                "DEBUG",
                "Send Command - Topic: iot/p2p/GetWKVer/helperbot/bumper/helperbot/bot_serial/ls1ok3/wC3g/q/iCmuqp/j - Message: {}",
            )
        )  # Check send command message was logged
        l.clear()
        await mqtt_helperbot.Client.disconnect()

        # Received response to command
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        msg_payload = '{"ret":"ok","ver":"0.13.5"}'
        msg_topic_name = "iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/iCmuqp/j"
        await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

        await asyncio.sleep(0.1)

        l.check_present(
            (
                "helperbot",
                "DEBUG",
                'Received Response - Topic: iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/iCmuqp/j - Message: {"ret":"ok","ver":"0.13.5"}',
            )
        )  # Check received response message was logged
        l.clear()
        await mqtt_helperbot.Client.disconnect()

        # Received unknown message
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        msg_payload = "test"
        msg_topic_name = "iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/TESTBAD/bumper/helperbot/p/iCmuqp/j"
        await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

        await asyncio.sleep(0.1)

        l.check_present(
            (
                "helperbot",
                "DEBUG",
                "Received Message - Topic: iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/TESTBAD/bumper/helperbot/p/iCmuqp/j - Message: test",
            )
        )  # Check received message was logged
        l.clear()
        await mqtt_helperbot.Client.disconnect()

        # Received error message
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        msg_payload = "<ctl ts='1560904925396' td='errors' old='' new='110'/>"
        msg_topic_name = "iot/atr/errors/bot_serial/ls1ok3/wC3g/x"
        await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

        await asyncio.sleep(0.1)

        l.check_present(
            (
                "boterror",
                "ERROR",
                "Received Error - Topic: iot/atr/errors/bot_serial/ls1ok3/wC3g/x - Message: <ctl ts='1560904925396' td='errors' old='' new='110'/>",
            )
        )  # Check received message was logged
        l.clear()
        await mqtt_helperbot.Client.disconnect()


@pytest.mark.usefixtures("mqtt_server")
async def test_helperbot_expire_message():
    timeout = 0.1
    # Test broadcast message
    mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT, timeout)
    bumper.mqtt_helperbot = mqtt_helperbot
    await mqtt_helperbot.start_helper_bot()
    assert (
        mqtt_helperbot.Client._connected_state._value == True
    )  # Check helperbot is connected

    expire_msg_payload = '{"ret":"ok","ver":"0.13.5"}'
    expire_msg_topic_name = "iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/testgood/j"
    currenttime = time.time()
    request_id = "ABC"
    data = {
        "time": currenttime,
        "topic": expire_msg_topic_name,
        "payload": expire_msg_payload,
    }

    mqtt_helperbot.commands[request_id] = data

    assert mqtt_helperbot.commands[request_id] == data

    await asyncio.sleep(0.1)
    msg_payload = "<ctl ts='1547822804960' td='DustCaseST' st='0'/>"
    msg_topic_name = "iot/atr/DustCaseST/bot_serial/ls1ok3/wC3g/x"
    await mqtt_helperbot.Client.publish(
        msg_topic_name, msg_payload.encode(), QOS_0
    )  # Send another message to force get_msg

    await asyncio.sleep(timeout * 2)

    assert mqtt_helperbot.commands.get(request_id, None) == None

    await mqtt_helperbot.Client.disconnect()


@pytest.mark.usefixtures("mqtt_server")
async def test_helperbot_sendcommand():
    timeout = 0.1
    mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT, timeout)
    bumper.mqtt_helperbot = mqtt_helperbot
    await mqtt_helperbot.start_helper_bot()
    assert (
        mqtt_helperbot.Client._connected_state._value == True
    )  # Check helperbot is connected

    cmdjson = {
        "toType": "ls1ok3",
        "payloadType": "j",
        "toRes": "wC3g",
        "payload": {},
        "td": "q",
        "toId": "bot_serial",
        "cmdName": "GetWKVer",
        "auth": {
            "token": "us_52cb21fef8e547f38f4ec9a699a5d77e",
            "resource": "IOSF53D07BA",
            "userid": "fuid_tmpuser",
            "with": "users",
            "realm": "ecouser.net",
        },
    }
    commandresult = await mqtt_helperbot.send_command(cmdjson, "testfail")
    # Don't send a response, ensure timeout
    assert commandresult == {
        "debug": "wait for response timed out",
        "errno": 500,
        "id": "testfail",
        "ret": "fail",
    }  # Check timeout

    # Send response beforehand
    msg_payload = '{"ret":"ok","ver":"0.13.5"}'
    msg_topic_name = "iot/p2p/GetWKVer/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/testgood/j"
    await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

    commandresult = await mqtt_helperbot.send_command(cmdjson, "testgood")
    assert commandresult == {
        "id": "testgood",
        "resp": {"ret": "ok", "ver": "0.13.5"},
        "ret": "ok",
    }

    # await mqtt_helperbot.Client.disconnect()

    # Test GetLifeSpan (xml command)
    cmdjson = {
        "toType": "ls1ok3",
        "payloadType": "x",
        "toRes": "wC3g",
        "payload": '<ctl type="Brush"/>',
        "td": "q",
        "toId": "bot_serial",
        "cmdName": "GetLifeSpan",
        "auth": {
            "token": "us_52cb21fef8e547f38f4ec9a699a5d77e",
            "resource": "IOSF53D07BA",
            "userid": "fuid_tmpuser",
            "with": "users",
            "realm": "ecouser.net",
        },
    }

    # Send response beforehand
    msg_payload = "<ctl ret='ok' type='Brush' left='4142' total='18000'/>"
    msg_topic_name = "iot/p2p/GetLifeSpan/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/testx/q"
    await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

    commandresult = await mqtt_helperbot.send_command(cmdjson, "testx")
    assert commandresult == {
        "id": "testx",
        "resp": "<ctl ret='ok' type='Brush' left='4142' total='18000'/>",
        "ret": "ok",
    }

    # Test json payload (OZMO950)
    cmdjson = {
        "toType": "ls1ok3",
        "payloadType": "j",
        "toRes": "wC3g",
        "payload": {
            "header": {"pri": 1, "ts": "1569380075887", "tzm": -240, "ver": "0.0.50"}
        },
        "td": "q",
        "toId": "bot_serial",
        "cmdName": "getStats",
        "auth": {
            "token": "us_52cb21fef8e547f38f4ec9a699a5d77e",
            "resource": "IOSF53D07BA",
            "userid": "fuid_tmpuser",
            "with": "users",
            "realm": "ecouser.net",
        },
    }

    # Send response beforehand
    msg_payload = '{"body":{"code":0,"data":{"area":0,"cid":"111","start":"1569378657","time":6,"type":"auto"},"msg":"ok"},"header":{"fwVer":"1.6.4","hwVer":"0.1.1","pri":1,"ts":"1569380074036","tzm":480,"ver":"0.0.1"}}'

    msg_topic_name = (
        "iot/p2p/getStats/bot_serial/ls1ok3/wC3g/helperbot/bumper/helperbot/p/testj/j"
    )
    await mqtt_helperbot.Client.publish(msg_topic_name, msg_payload.encode(), QOS_0)

    commandresult = await mqtt_helperbot.send_command(cmdjson, "testj")

    assert commandresult == {
        "id": "testj",
        "resp": {
            "body": {
                "code": 0,
                "data": {
                    "area": 0,
                    "cid": "111",
                    "start": "1569378657",
                    "time": 6,
                    "type": "auto",
                },
                "msg": "ok",
            },
            "header": {
                "fwVer": "1.6.4",
                "hwVer": "0.1.1",
                "pri": 1,
                "ts": "1569380074036",
                "tzm": 480,
                "ver": "0.0.1",
            },
        },
        "ret": "ok",
    }

    await mqtt_helperbot.Client.disconnect()


async def test_mqttserver():
    if os.path.exists("tests/tmp.db"):
        os.remove("tests/tmp.db")  # Remove existing db

    bumper.db = "tests/tmp.db"  # Set db location for testing

    mqtt_server = bumper.MQTTServer(
        HOST, MQTT_PORT, password_file="tests/passwd", allow_anonymous=True
    )

    await mqtt_server.broker_coro()

    try:
        # Test helperbot connect
        mqtt_helperbot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        await mqtt_helperbot.start_helper_bot()
        assert (
            mqtt_helperbot.Client._connected_state._value == True
        )  # Check helperbot is connected
        await mqtt_helperbot.Client.disconnect()

        # Test client connect
        bumper.user_add("user_123")  # Add user to db
        bumper.client_add("user_123", "ecouser.net", "resource_123")  # Add client to db
        test_client = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        test_client.client_id = "user_123@ecouser.net/resource_123"
        # await test_client.start_helper_bot()
        test_client.Client = amqtt.client.MQTTClient(
            client_id=test_client.client_id, config={"check_hostname": False}
        )

        await test_client.Client.connect(
            f"mqtts://{HOST}:{MQTT_PORT}/",
            cafile=bumper.ca_cert,
        )
        assert (
            test_client.Client._connected_state._value == True
        )  # Check client is connected
        await test_client.Client.disconnect()
        assert (
            test_client.Client._connected_state._value == False
        )  # Check client is disconnected

        # Test fake_bot connect
        fake_bot = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        fake_bot.client_id = "bot_serial@ls1ok3/wC3g"
        await fake_bot.start_helper_bot()
        assert (
            fake_bot.Client._connected_state._value == True
        )  # Check fake_bot is connected
        await fake_bot.Client.disconnect()

        # Test file auth client connect
        test_client = bumper.MQTTHelperBot(HOST, MQTT_PORT)
        test_client.client_id = "test-file-auth"
        # await test_client.start_helper_bot()
        test_client.Client = amqtt.client.MQTTClient(
            client_id=test_client.client_id,
            config={
                "check_hostname": False,
                "auto_reconnect": False,
                "reconnect_retries": 1,
            },
        )

        # good user/pass
        await test_client.Client.connect(
            f"mqtts://test-client:abc123!@{HOST}:{MQTT_PORT}/",
            cafile=bumper.ca_cert,
            cleansession=True,
        )

        assert (
            test_client.Client._connected_state._value == True
        )  # Check client is connected
        await test_client.Client.disconnect()
        assert (
            test_client.Client._connected_state._value == False
        )  # Check client is disconnected

        # bad password
        with LogCapture() as l:

            await test_client.Client.connect(
                f"mqtts://test-client:notvalid!@{HOST}:{MQTT_PORT}/",
                cafile=bumper.ca_cert,
                cleansession=True,
            )

            l.check_present(
                (
                    "mqttserver",
                    "INFO",
                    "File Authentication Failed - Username: test-client - ClientID: test-file-auth",
                ),
                order_matters=False,
            )
            # no username in file
            await test_client.Client.connect(
                f"mqtts://test-client-noexist:notvalid!@{HOST}:{MQTT_PORT}/",
                cafile=bumper.ca_cert,
                cleansession=True,
            )

            l.check_present(
                (
                    "mqttserver",
                    "INFO",
                    "File Authentication Failed - No Entry for Username: test-client-noexist - ClientID: test-file-auth",
                ),
                order_matters=False,
            )
    finally:
        await mqtt_server.broker.shutdown()


async def test_nofileauth_mqttserver():
    with LogCapture() as l:

        mqtt_server = bumper.MQTTServer(
            HOST, MQTT_PORT, password_file="tests/passwd-notfound"
        )
        await mqtt_server.broker_coro()
        await mqtt_server.broker.shutdown()

    l.check_present(
        (
            "amqtt.broker.plugins.bumper",
            "WARNING",
            "Password file tests/passwd-notfound not found",
        ),
        order_matters=False,
    )

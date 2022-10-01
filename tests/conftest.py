import asyncio
import ssl

import pytest
from gmqtt import Client
from gmqtt.mqtt.constants import MQTTv311

import bumper
from bumper import HelperBot, MQTTServer, WebserverBinding
from tests import HOST, MQTT_PORT, WEBSERVER_PORT


@pytest.fixture
async def mqtt_server():
    mqtt_server = MQTTServer(HOST, MQTT_PORT, password_file="tests/passwd")
    await mqtt_server.start()
    bumper.mqtt_server = mqtt_server
    while not mqtt_server.state == "started":
        await asyncio.sleep(0.1)

    yield mqtt_server

    await mqtt_server.shutdown()


@pytest.fixture
async def mqtt_client(mqtt_server: MQTTServer):
    assert mqtt_server.state == "started"

    client = Client("helperbot@bumper/test")
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    await client.connect(HOST, MQTT_PORT, ssl=ssl_ctx, version=MQTTv311)

    yield client

    await client.disconnect()


@pytest.fixture
async def helper_bot(mqtt_server: MQTTServer):
    assert mqtt_server.state == "started"

    helper_bot = HelperBot(HOST, MQTT_PORT, 0.1)
    bumper.mqtt_helperbot = helper_bot
    await helper_bot.start()
    assert helper_bot.is_connected

    yield helper_bot

    await helper_bot.disconnect()


@pytest.fixture
async def webserver_client(aiohttp_client):
    webserver = bumper.WebServer(
        WebserverBinding(HOST, WEBSERVER_PORT, False), False, True
    )
    client = await aiohttp_client(webserver._app)

    yield client

    await client.close()

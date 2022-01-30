import pytest

import bumper
from tests import HOST, MQTT_PORT


@pytest.fixture
async def mqtt_server():
    mqtt_server = bumper.MQTTServer(HOST, MQTT_PORT, password_file="tests/passwd")
    await mqtt_server.broker_coro()
    bumper.mqtt_server = mqtt_server

    yield

    await mqtt_server.broker.shutdown()


@pytest.fixture
async def conf_server_client(aiohttp_client):
    confserver = bumper.ConfServer("127.0.0.1:11111", False)
    confserver.confserver_app()

    client = await aiohttp_client(confserver.app)

    yield client

    await client.close()
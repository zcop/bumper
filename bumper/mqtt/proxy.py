"""Mqtt proxy module."""
import asyncio
import re
from typing import Any, MutableMapping

from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2
from cachetools import TTLCache

from ..util import get_logger

_LOGGER = get_logger("proxymode")

# iot/p2p/[command]]/[sender did]/[sender class]]/[sender resource]
# /[receiver did]/[receiver class]]/[receiver resource]/[q|p/[request id/j
# [q|p] q-> request p-> response

TOPIC_P2P = re.compile(
    "iot/p2p/(?P<command>[^/]+)/(?P<sender_id>[^/]+)/(?P<sender_cls>[^/]+)/(?P<sender_resource>[^/]+)/"
    "/(?P<receiver_id>[^/]+)/(?P<receiver_cls>[^/]+)/(?P<receiver_resource>[^/]+)/(?P<mode>[^/]+)/"
    "(?P<request_id>[^/]+)/(?P<data_type>[^/]+)"
)


class ProxyClient:
    """Mqtt client, which proxies all messages to the ecovacs servers."""

    def __init__(
        self,
        client_id: str,
        host: str,
        port: int = 443,
        config: dict[str, Any] | None = None,
        timeout: float = 180,
    ):
        self.request_mapper: MutableMapping[str, str] = TTLCache(
            maxsize=timeout * 60, ttl=timeout * 1.1
        )
        self._client = MQTTClient(client_id=client_id, config=config)
        self._host = host
        self._port = port

    async def connect(self, username: str, password: str) -> None:
        try:
            await self._client.connect(
                f"mqtts://{username}:{password}@{self._host}:{self._port}"
            )
        except Exception:
            _LOGGER.exception("An exception occurred during startup", exc_info=True)
            raise

        asyncio.create_task(self._handle_messages())

    async def _handle_messages(self) -> None:
        while self._client.session.transitions.is_connected():
            try:
                message = await self._client.deliver_message()
                data = str(message.data.decode("utf-8"))

                _LOGGER.info(
                    f"MQTT Proxy Client - Message Received From Ecovacs - Topic: {message.topic} - Message: {data}"
                )
                topic = message.topic
                ttopic = topic.split("/")
                if ttopic[1] == "p2p":
                    self.request_mapper[ttopic[10]] = ttopic[3]
                    ttopic[3] = "proxyhelper"
                    topic = "/".join(ttopic)
                    _LOGGER.info(
                        f"MQTT Proxy Client - Converted Topic From {message.topic} TO {topic}"
                    )

                _LOGGER.info(
                    f"MQTT Proxy Client - Proxy Forward Message to Robot - Topic: {topic} - Message: {data}"
                )
                await self._client.publish(topic, data.encode(), QOS_0)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.error(
                    "An error occurred during handling a message", exc_info=True
                )

    async def subscribe(self, topic: str, qos: QOS_0 | QOS_1 | QOS_2 = QOS_0) -> None:
        await self._client.subscribe([(topic, qos)])

    async def disconnect(self) -> None:
        await self._client.disconnect()

    async def publish(self, topic: str, message: bytes, qos: int | None = None) -> None:
        await self._client.publish(topic, message, qos)

"""Helper bot module."""
import asyncio
import json
import ssl
from typing import Any, MutableMapping

from cachetools import TTLCache
from gmqtt import Client, Subscription
from gmqtt.mqtt.constants import MQTTv311

from bumper.util import get_logger

_LOGGER = get_logger("helperbot")


class CommandDto:
    """Command DTO."""

    def __init__(self, payload_type: str) -> None:
        self._payload_type = payload_type
        self._event = asyncio.Event()
        self._response: str | bytes

    async def wait_for_response(self) -> str | dict[str, Any]:
        """Wait for the response to be received."""
        await self._event.wait()
        if self._payload_type == "j":
            return json.loads(self._response)  # type:ignore[no-any-return]

        return str(self._response)

    def add_response(self, response: str | bytes) -> None:
        """Add received response."""
        self._response = response
        self._event.set()


class HelperBot:
    """Helper bot, which converts commands from the rest api to mqtt ones."""

    def __init__(self, host: str, port: int, timeout: float = 60):
        self._commands: MutableMapping[str, CommandDto] = TTLCache(
            maxsize=timeout * 60, ttl=timeout * 1.1
        )
        self._host = host
        self._port = port
        self._client_id = "helperbot@bumper/helperbot"
        self._timeout = timeout
        self._client = Client("helperbot@bumper/helperbot")

        # pylint: disable=unused-argument
        async def _on_message(
            client: Client, topic: str, payload: bytes, qos: int, properties: dict
        ) -> None:
            try:
                _LOGGER.debug(
                    "Got message: topic=%s; payload=%s;", topic, payload.decode()
                )
                topic_split = topic.split("/")
                data_decoded = str(payload.decode())
                if topic_split[10] in self._commands:
                    self._commands[topic_split[10]].add_response(data_decoded)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.error(
                    "An exception occurred during handling message.", exc_info=True
                )

        self._client.on_message = _on_message

    @property
    def is_connected(self) -> bool:
        """Return True if client is connected successfully."""
        return self._client.is_connected  # type: ignore[no-any-return]

    async def start(self) -> None:
        """Connect and subscribe helper bot."""
        try:
            if self.is_connected:
                return

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            await self._client.connect(
                self._host, self._port, ssl=ssl_ctx, version=MQTTv311
            )
            self._client.subscribe(
                Subscription("iot/p2p/+/+/+/+/helperbot/bumper/helperbot/+/+/+")
            )
        except Exception:
            _LOGGER.exception("An exception occurred during startup", exc_info=True)
            raise

    async def _wait_for_resp(
        self, command_dto: CommandDto, request_id: str
    ) -> dict[str, Any]:
        try:
            payload = await asyncio.wait_for(
                command_dto.wait_for_response(), timeout=self._timeout
            )
            return {"id": request_id, "ret": "ok", "resp": payload}
        except asyncio.TimeoutError:
            _LOGGER.debug("wait_for_resp timeout reached")
        except asyncio.CancelledError:
            _LOGGER.debug("wait_for_resp cancelled by asyncio", exc_info=True)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("An unknown error occurred", exc_info=True)

        return {
            "id": request_id,
            "errno": 500,
            "ret": "fail",
            "debug": "wait for response timed out",
        }

    async def send_command(
        self, cmdjson: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        """Send command over MQTT."""
        if not self.is_connected:
            await self.start()

        try:
            topic = (
                f"iot/p2p/{cmdjson['cmdName']}/helperbot/bumper/helperbot/{cmdjson['toId']}/"
                f"{cmdjson['toType']}/{cmdjson['toRes']}/q/{request_id}/{cmdjson['payloadType']}"
            )

            if cmdjson["payloadType"] == "j":
                payload = json.dumps(cmdjson["payload"])
            else:
                payload = str(cmdjson["payload"])

            command_dto = CommandDto(cmdjson["payloadType"])
            self._commands[request_id] = command_dto

            _LOGGER.debug("Sending message %s", topic)
            self._client.publish(topic, payload.encode())

            resp = await self._wait_for_resp(command_dto, request_id)
            return resp
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Could not send command.", exc_info=True)
            return {
                "id": request_id,
                "errno": 500,
                "ret": "fail",
                "debug": "exception occurred please check bumper logs",
            }
        finally:
            self._commands.pop(request_id, None)

    async def disconnect(self) -> None:
        """Disconnect client."""
        if self.is_connected:
            await self._client.disconnect()

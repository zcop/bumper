#!/usr/bin/env python3

import asyncio
import json
import os
from asyncio import Task
from typing import Any, Dict, MutableMapping, Optional, Union

import amqtt
import pkg_resources
from amqtt.broker import Broker, BrokerContext
from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0
from amqtt.session import IncomingApplicationMessage, Session
from cachetools import TTLCache
from passlib.apps import custom_app_context as pwd_context

import bumper
from bumper.util import get_logger

mqttserverlog = get_logger("mqttserver")
helperbotlog = get_logger("helperbot")
boterrorlog = get_logger("boterror")


class CommandDto:
    def __init__(self, payload_type: str) -> None:
        self._payload_type = payload_type
        self._event = asyncio.Event()
        self._response: Union[str, bytes]

    async def wait_for_response(self) -> Union[str, dict[str, Any]]:
        await self._event.wait()
        if self._payload_type == "j":
            return json.loads(self._response)
        else:
            return str(self._response)

    def add_response(self, response: Union[str, bytes]) -> None:
        self._response = response
        self._event.set()


class MQTTHelperBot:
    def __init__(self, host: str, port: int, timeout: float = 60):
        self._commands: MutableMapping[str, CommandDto] = TTLCache(
            maxsize=timeout * 60, ttl=timeout * 1.1
        )
        self._host = host
        self._port = port
        self._client_id = "helperbot@bumper/helperbot"
        self._timeout = timeout
        self._client: Optional[MQTTClient] = None
        self._new_messages_task: Optional[Task] = None

    @property
    def is_connected(self) -> bool:
        """Return True if client is connected successfully."""
        return (
            self._client is not None
            and self._client.session.transitions.state == "connected"
        )

    async def start(self) -> None:
        try:
            if self._client is None:
                self._client = MQTTClient(
                    client_id=self._client_id,
                    config={"check_hostname": False, "reconnect_retries": 20},
                )

            await self._client.connect(
                f"mqtts://{self._host}:{self._port}/", cafile=bumper.ca_cert
            )
            await self._client.subscribe(
                [
                    ("iot/p2p/+/+/+/+/helperbot/bumper/helperbot/+/+/+", QOS_0),
                ]
            )
            self._new_messages_task = asyncio.create_task(
                self._check_for_new_messages()
            )
        except Exception as e:
            helperbotlog.exception(f"{e}")
            raise e

    async def _check_for_new_messages(self):
        while True:
            try:
                message: IncomingApplicationMessage = (
                    await self._client.deliver_message()
                )
                if message is not None:
                    topic_split = str(message.topic).split("/")
                    data_decoded = str(message.data.decode("utf-8"))
                    if topic_split[10] in self._commands:
                        self._commands[topic_split[10]].add_response(data_decoded)
            except asyncio.CancelledError:
                pass
            except Exception as ex:  # pylint: disable=broad-except
                helperbotlog.error(
                    "An exception occurred during handling new messages", exc_info=True
                )

    async def _wait_for_resp(
        self, command_dto: CommandDto, request_id: str
    ) -> dict[str, Any]:
        try:
            payload = await asyncio.wait_for(
                command_dto.wait_for_response(), timeout=self._timeout
            )
            return {"id": request_id, "ret": "ok", "resp": payload}
        except asyncio.TimeoutError:
            helperbotlog.debug("wait_for_resp timeout reached")
        except asyncio.CancelledError as e:
            helperbotlog.debug("wait_for_resp cancelled by asyncio", e, exc_info=True)
        except Exception as e:
            helperbotlog.exception(f"{e}")

        return {
            "id": request_id,
            "errno": 500,
            "ret": "fail",
            "debug": "wait for response timed out",
        }

    async def send_command(
        self, cmdjson: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        if self._client is None:
            await self.start()
            assert self._client is not None

        try:
            topic = "iot/p2p/{}/helperbot/bumper/helperbot/{}/{}/{}/q/{}/{}".format(
                cmdjson["cmdName"],
                cmdjson["toId"],
                cmdjson["toType"],
                cmdjson["toRes"],
                request_id,
                cmdjson["payloadType"],
            )
            command_dto = CommandDto(cmdjson["payloadType"])
            self._commands[request_id] = command_dto

            if cmdjson["payloadType"] == "j":
                payload = json.dumps(cmdjson["payload"])
            else:
                payload = str(cmdjson["payload"])

            await self._client.publish(topic, payload.encode(), QOS_0)

            resp = await self._wait_for_resp(command_dto, request_id)
            return resp
        except Exception as e:
            helperbotlog.exception(f"{e}")
            return {
                "id": request_id,
                "errno": 500,
                "ret": "fail",
                "debug": "exception occurred please check bumper logs",
            }
        finally:
            self._commands.pop(request_id, None)

    async def disconnect(self):
        if self._new_messages_task is not None:
            self._new_messages_task.cancel()
            self._new_messages_task = None

        if self._client is not None:
            await self._client.disconnect()
            self._client = None


class MQTTServer:
    def __init__(self, host: str, port: int, **kwargs: dict[str, Any]) -> None:
        try:
            self._host = host
            self._port = port

            # For file auth, set user:hash in passwd file see
            # (https://hbmqtt.readthedocs.io/en/latest/references/hbmqtt.html#configuration-example)
            passwd_file = kwargs.get(
                "password_file", os.path.join(os.path.join(bumper.data_dir, "passwd"))
            )
            allow_anon = kwargs.get("allow_anonymous", False)

            # The below adds a plugin to the amqtt.broker.plugins without having to futz with setup.py
            distribution = pkg_resources.Distribution("amqtt.broker.plugins")
            bumper_plugin = pkg_resources.EntryPoint.parse(
                "bumper = bumper.mqttserver:BumperMQTTServer_Plugin", dist=distribution
            )
            distribution._ep_map = {"amqtt.broker.plugins": {"bumper": bumper_plugin}}
            pkg_resources.working_set.add(distribution)

            # Initialize bot server
            config = {
                "listeners": {
                    "default": {"type": "tcp"},
                    "tls1": {
                        "bind": f"{host}:{port}",
                        "ssl": "on",
                        "certfile": bumper.server_cert,
                        "keyfile": bumper.server_key,
                    },
                },
                "sys_interval": 0,
                "auth": {
                    "allow-anonymous": allow_anon,
                    "password-file": passwd_file,
                    "plugins": [
                        "bumper"
                    ],  # Bumper plugin provides auth and handling of bots/clients connecting
                },
                "topic-check": {
                    "enabled": True,  # Workaround until https://github.com/Yakifo/amqtt/pull/93 is merged
                    "plugins": [],
                },
            }

            self._broker = amqtt.broker.Broker(config=config)

        except Exception as e:
            mqttserverlog.exception(f"{e}")

    @property
    def state(self) -> Broker.states:
        """Return the state of the broker."""
        return self._broker.transitions.state

    @property
    def broker(self) -> Broker:
        return self._broker

    async def start(self) -> None:
        mqttserverlog.info(f"Starting MQTT Server at {self._host}:{self._port}")

        try:
            await self._broker.start()
        except Exception as e:
            mqttserverlog.exception(f"{e}")
            raise e

    async def shutdown(self):
        await self._broker.shutdown()


class BumperMQTTServer_Plugin:
    def __init__(self, context: BrokerContext) -> None:
        self.context = context
        try:
            self.auth_config = self.context.config["auth"]
            self._users = self._read_password_file()

        except KeyError:
            self.context.logger.warning(
                "'bumper' section not found in context configuration"
            )
        except Exception as e:
            mqttserverlog.exception(f"{e}")

    async def authenticate(self, session: Session, **kwargs: dict[str, Any]) -> bool:
        authenticated = False
        username = session.username
        password = session.password
        client_id = session.client_id

        try:
            if "@" in client_id:
                didsplit = str(client_id).split("@")
                if not (  # if ecouser or bumper aren't in details it is a bot
                    "ecouser" in didsplit[1] or "bumper" in didsplit[1]
                ):
                    tmpbotdetail = str(didsplit[1]).split("/")
                    bumper.bot_add(
                        username,
                        didsplit[0],
                        tmpbotdetail[0],
                        tmpbotdetail[1],
                        "eco-ng",
                    )
                    mqttserverlog.info(
                        f"Bumper Authentication Success - Bot - SN: {username} - DID: {didsplit[0]}"
                        f" - Class: {tmpbotdetail[0]}"
                    )
                    authenticated = True
                else:
                    tmpclientdetail = str(didsplit[1]).split("/")
                    userid = didsplit[0]
                    realm = tmpclientdetail[0]
                    resource = tmpclientdetail[1]

                    if userid == "helperbot":
                        mqttserverlog.info(
                            f"Bumper Authentication Success - Helperbot: {client_id}"
                        )
                        authenticated = True
                    elif (
                        bumper.check_authcode(didsplit[0], password)
                        or not bumper.use_auth
                    ):
                        bumper.client_add(userid, realm, resource)
                        mqttserverlog.info(
                            f"Bumper Authentication Success - Client - Username: {username} - "
                            f"ClientID: {client_id}"
                        )
                        authenticated = True

            # Check for File Auth
            if (
                username and not authenticated
            ):  # If there is a username and it isn't already authenticated
                hash = self._users.get(username, None)
                if hash:  # If there is a matching entry in passwd, check hash
                    authenticated = pwd_context.verify(password, hash)
                    if authenticated:
                        mqttserverlog.info(
                            f"File Authentication Success - Username: {username} - ClientID: {client_id}"
                        )
                    else:
                        mqttserverlog.info(
                            f"File Authentication Failed - Username: {username} - ClientID: {client_id}"
                        )
                else:
                    mqttserverlog.info(
                        f"File Authentication Failed - No Entry for Username: {username} - ClientID: {client_id}"
                    )

        except Exception as e:
            mqttserverlog.exception(
                "Session: {} - {}".format((kwargs.get("session", None)), e)
            )
            authenticated = False

        # Check for allow anonymous
        allow_anonymous = self.auth_config.get("allow-anonymous", True)
        if (
            allow_anonymous and not authenticated
        ):  # If anonymous auth is allowed and it isn't already authenticated
            authenticated = True
            self.context.logger.debug(
                f"Anonymous Authentication Success: config allows anonymous - Username: {username}"
            )
            mqttserverlog.info(
                f"Anonymous Authentication Success: config allows anonymous - Username: {username}"
            )

        return authenticated

    def _read_password_file(self) -> dict[str, str]:
        password_file = self.auth_config.get("password-file", None)
        users: dict[str, str] = {}
        if password_file:
            try:
                with open(password_file) as f:
                    self.context.logger.debug(
                        f"Reading user database from {password_file}"
                    )
                    for l in f:
                        line = l.strip()
                        if not line.startswith("#"):  # Allow comments in files
                            (username, pwd_hash) = line.split(sep=":", maxsplit=3)
                            if username:
                                users[username] = pwd_hash
                                self.context.logger.debug(
                                    f"user: {username} - hash: {pwd_hash}"
                                )
                self.context.logger.debug(
                    f"{(len(users))} user(s) read from file {password_file}"
                )
            except FileNotFoundError:
                self.context.logger.warning(f"Password file {password_file} not found")

        return users

    async def on_broker_client_connected(self, client_id: str) -> None:
        self._set_client_connected(client_id, True)

    def _set_client_connected(self, client_id: str, connected: bool) -> None:
        didsplit = str(client_id).split("@")

        bot = bumper.bot_get(didsplit[0])
        if bot:
            bumper.bot_set_mqtt(bot["did"], connected)
            return

        clientresource = didsplit[1].split("/")[1]
        client = bumper.client_get(clientresource)
        if client:
            bumper.client_set_mqtt(client["resource"], connected)

    async def on_broker_message_received(
        self, message: IncomingApplicationMessage, **kwargs: dict[str, Any]
    ) -> None:
        topic = message.topic
        topic_split = str(topic).split("/")
        data_decoded = str(message.data.decode("utf-8"))
        if topic_split[6] == "helperbot":
            # Response to command
            helperbotlog.debug(
                f"Received Response - Topic: {topic} - Message: {data_decoded}"
            )
        elif topic_split[3] == "helperbot":
            # Helperbot sending command
            helperbotlog.debug(
                f"Send Command - Topic: {topic} - Message: {data_decoded}"
            )
        elif topic_split[1] == "atr":
            # Broadcast message received on atr
            if topic_split[2] == "errors":
                boterrorlog.error(
                    f"Received Error - Topic: {topic} - Message: {data_decoded}"
                )
            else:
                helperbotlog.debug(
                    f"Received Broadcast - Topic: {topic} - Message: {data_decoded}"
                )
        else:
            helperbotlog.debug(
                f"Received Message - Topic: {topic} - Message: {data_decoded}"
            )

    async def on_broker_client_disconnected(self, client_id: str) -> None:
        self._set_client_connected(client_id, False)

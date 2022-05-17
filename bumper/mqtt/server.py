"""Server module."""

import os
from typing import Any

import amqtt
import pkg_resources
from amqtt.broker import Broker, BrokerContext
from amqtt.session import IncomingApplicationMessage, Session
from passlib.apps import custom_app_context as pwd_context

import bumper
from bumper.db import (
    bot_add,
    bot_get,
    bot_set_mqtt,
    check_authcode,
    client_add,
    client_get,
    client_set_mqtt,
)
from bumper.util import get_logger

mqttserverlog = get_logger("mqttserver")
helperbotlog = get_logger("helperbot")
boterrorlog = get_logger("boterror")


class MQTTServer:
    """Mqtt server."""

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
                "bumper = bumper.mqtt.server:BumperMQTTServerPlugin", dist=distribution
            )
            distribution._ep_map = {"amqtt.broker.plugins": {"bumper": bumper_plugin}}  # type: ignore[attr-defined]
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

        except Exception:
            mqttserverlog.exception(
                "An exception occurred during initialize", exc_info=True
            )
            raise

    @property
    def state(self) -> Broker.states:
        """Return the state of the broker."""
        return self._broker.transitions.state

    @property
    def broker(self) -> Broker:
        """Get MQTT broker."""
        return self._broker

    async def start(self) -> None:
        """Start MQTT server."""
        mqttserverlog.info("Starting MQTT Server at %s:%d", self._host, self._port)
        try:
            await self._broker.start()
        except Exception:
            mqttserverlog.exception(
                "An exception occurred during startup", exc_info=True
            )
            raise

    async def shutdown(self) -> None:
        """Shutdown server."""
        # stop session handler manually otherwise connection will not be closed correctly
        for (
            _,
            handler,
        ) in self._broker._sessions.values():  # pylint: disable=protected-access
            await handler.stop()
        await self._broker.shutdown()


def _log__helperbot_message(custom_log_message: str, topic: str, data: str) -> None:
    helperbotlog.debug("%s - Topic: %s - Message: %s", custom_log_message, topic, data)


class BumperMQTTServerPlugin:
    """MQTT Server plugin which handles the authentication."""

    def __init__(self, context: BrokerContext) -> None:
        self.context = context
        try:
            self.auth_config = self.context.config["auth"]
            self._users = self._read_password_file()

        except KeyError:
            self.context.logger.warning(
                "'bumper' section not found in context configuration"
            )
        except Exception:
            mqttserverlog.exception(
                "An exception occurred during plugin initialization", exc_info=True
            )
            raise

    async def authenticate(self, session: Session, **kwargs: dict[str, Any]) -> bool:
        """Authenticate session."""
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
                    bot_add(
                        username,
                        didsplit[0],
                        tmpbotdetail[0],
                        tmpbotdetail[1],
                        "eco-ng",
                    )
                    mqttserverlog.info(
                        "Bumper Authentication Success - Bot - SN: %s - DID: %s - Class: %s",
                        username,
                        didsplit[0],
                        tmpbotdetail[0],
                    )
                    return True

                tmpclientdetail = str(didsplit[1]).split("/")
                userid = didsplit[0]
                realm = tmpclientdetail[0]
                resource = tmpclientdetail[1]

                if userid == "helperbot":
                    mqttserverlog.info(
                        "Bumper Authentication Success - Helperbot: %s", client_id
                    )
                    return True
                if check_authcode(didsplit[0], password) or not bumper.use_auth:
                    client_add(userid, realm, resource)
                    mqttserverlog.info(
                        "Bumper Authentication Success - Client - Username: %s - ClientID: %s",
                        username,
                        client_id,
                    )
                    return True

            # Check for File Auth
            if username:
                # If there is a username and it isn't already authenticated
                password_hash = self._users.get(username, None)
                message_suffix = f"- Username: {username} - ClientID: {client_id}"
                if password_hash:  # If there is a matching entry in passwd, check hash
                    if pwd_context.verify(password, password_hash):
                        mqttserverlog.info(
                            "File Authentication Success %s", message_suffix
                        )
                        return True

                    mqttserverlog.info("File Authentication Failed %s", message_suffix)
                else:
                    mqttserverlog.info(
                        "File Authentication Failed - No Entry %s", message_suffix
                    )

        except Exception:  # pylint: disable=broad-except
            mqttserverlog.exception(
                "Session: %s", kwargs.get("session", ""), exc_info=True
            )

        # Check for allow anonymous
        if self.auth_config.get("allow-anonymous", True):
            message = f"Anonymous Authentication Success: config allows anonymous - Username: {username}"
            self.context.logger.debug(message)
            mqttserverlog.info(message)
            return True

        return False

    def _read_password_file(self) -> dict[str, str]:
        password_file = self.auth_config.get("password-file", None)
        users: dict[str, str] = {}
        if password_file:
            try:
                with open(password_file, encoding="utf-8") as file:
                    self.context.logger.debug(
                        f"Reading user database from {password_file}"
                    )
                    for line in file:
                        line = line.strip()
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
        """On client connected."""
        self._set_client_connected(client_id, True)

    def _set_client_connected(  # pylint: disable=no-self-use
        self, client_id: str, connected: bool
    ) -> None:
        didsplit = str(client_id).split("@")

        bot = bot_get(didsplit[0])
        if bot:
            bot_set_mqtt(bot["did"], connected)
            return

        clientresource = didsplit[1].split("/")[1]
        client = client_get(clientresource)
        if client:
            client_set_mqtt(client["resource"], connected)

    async def on_broker_message_received(  # pylint: disable=no-self-use
        self, message: IncomingApplicationMessage, **_: dict[str, Any]
    ) -> None:
        """On message received."""
        topic = message.topic
        topic_split = str(topic).split("/")
        data_decoded = str(message.data.decode("utf-8"))
        if topic_split[6] == "helperbot":
            # Response to command
            _log__helperbot_message("Received Response", topic, data_decoded)
        elif topic_split[3] == "helperbot":
            # Helperbot sending command
            _log__helperbot_message("Send Command", topic, data_decoded)
        elif topic_split[1] == "atr":
            # Broadcast message received on atr
            if topic_split[2] == "errors":
                boterrorlog.error(
                    "Received Error - Topic: %s - Message: %s", topic, data_decoded
                )
            else:
                _log__helperbot_message("Received Broadcast", topic, data_decoded)
        else:
            _log__helperbot_message("Received Message", topic, data_decoded)

    async def on_broker_client_disconnected(self, client_id: str) -> None:
        """On client disconnect."""
        self._set_client_connected(client_id, False)

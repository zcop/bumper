"""Web server module."""

import asyncio
import dataclasses
import inspect
import json
import logging
import os
import ssl
from typing import Union

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_exceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
    HTTPNoContent,
)
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse

import bumper

from .db import bot_get, bot_remove, client_get, client_remove, db_get
from .plugins import ConfServerApp, WebserverPlugin, WebserverSubApi
from .util import get_logger
from .web.plugins import add_plugins


class _aiohttp_filter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "aiohttp.access" and record.levelno == 20:
            # Filters aiohttp.access log to switch it from INFO to DEBUG
            record.levelno = 10
            record.levelname = "DEBUG"

        if record.levelno == 10 and get_logger("confserver").getEffectiveLevel() == 10:
            return True
        else:
            return False


confserverlog = get_logger("confserver")
# Add logging filter above to aiohttp.access
logging.getLogger("aiohttp.access").addFilter(_aiohttp_filter())


@dataclasses.dataclass(frozen=True)
class WebserverBinding:
    """Webserver binding."""

    host: str
    port: int
    use_ssl: bool


class ConfServer:
    """Web server."""

    _EXCLUDE_FROM_LOGGING = ["base", "remove-bot", "remove-client", "restart-service"]

    def __init__(self, bindings: Union[list[WebserverBinding], WebserverBinding]):
        self._runners: list[web.AppRunner] = []

        if isinstance(bindings, WebserverBinding):
            bindings = [bindings]
        self._bindings = bindings

        self._app = web.Application(
            middlewares=[
                self._log_all_requests,
            ],
        )
        aiohttp_jinja2.setup(
            self._app,
            loader=jinja2.FileSystemLoader(
                os.path.join(bumper.bumper_dir, "bumper", "web", "templates")
            ),
        )
        self._add_routes()
        self._app.freeze()  # no modification allowed anymore

    def _add_routes(self) -> None:
        self._app.add_routes(
            [
                web.get("", self._handle_base, name="base"),
                web.get(
                    "/bot/remove/{did}", self._handle_remove_bot, name="remove-bot"
                ),
                web.get(
                    "/client/remove/{resource}",
                    self._handle_remove_client,
                    name="remove-client",
                ),
                web.get(
                    "/restart_{service}",
                    self._handle_restart_service,
                    name="restart-service",
                ),
                web.post("/lookup.do", self._handle_lookup),
                web.post("/newauth.do", self._handle_newauth),
            ]
        )

        # common api paths
        api_v1 = {"prefix": "/v1/", "app": web.Application()}  # for /v1/
        portal_api = {"prefix": "/api/", "app": web.Application()}  # for /api/

        apis = {
            WebserverSubApi.V1: api_v1,
            WebserverSubApi.API: portal_api,
        }

        add_plugins(self._app)

        # Load plugins
        for module in bumper.discovered_plugins.values():
            plugins = [
                m[1]
                for m in inspect.getmembers(module, inspect.isclass)
                if m[1].__module__ == module.__name__
            ]
            for plugin_class in plugins:
                if issubclass(plugin_class, WebserverPlugin):
                    plugin = plugin_class()
                    logging.debug(
                        f"Adding confserver sub_api ({plugin.__class__.__name__})"
                    )
                    apis[plugin.sub_api]["app"].add_routes(plugin.routes)
                elif issubclass(plugin_class, ConfServerApp):
                    plugin = plugin_class()
                    if plugin.plugin_type == "sub_api":  # app or sub_api
                        convert_api = {
                            "api_v1": WebserverSubApi.V1,
                            "api_v2": WebserverSubApi.V2,
                            "portal_api": WebserverSubApi.API,
                            "upload_api": WebserverSubApi.UPLOAD,
                        }
                        api = convert_api.get(plugin.sub_api, None)
                        if api and plugin.routes:
                            logging.debug(f"Adding confserver sub_api ({plugin.name})")
                            apis[api]["app"].add_routes(plugin.routes)

                    elif plugin.plugin_type == "app":
                        if plugin.path_prefix and plugin.app:
                            logging.debug(f"Adding confserver plugin ({plugin.name})")
                            self._app.add_subapp(plugin.path_prefix, plugin.app)
        for api in apis:
            self._app.add_subapp(apis[api]["prefix"], apis[api]["app"])

    async def start(self) -> None:
        """Start server."""
        try:
            confserverlog.info("Starting ConfServer")
            for binding in self._bindings:
                runner = web.AppRunner(self._app)
                self._runners.append(runner)
                await runner.setup()

                ssl_ctx = None
                if binding.use_ssl:
                    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ssl_ctx.load_cert_chain(bumper.server_cert, bumper.server_key)

                site = web.TCPSite(
                    runner,
                    host=binding.host,
                    port=binding.port,
                    ssl_context=ssl_ctx,
                )

                await site.start()
        except Exception as e:
            confserverlog.exception(f"{e}")
            raise e

    async def shutdown(self) -> None:
        """Shutdown server."""
        try:
            confserverlog.info("Shutting down")
            for runner in self._runners:
                await runner.shutdown()

            self._runners.clear()
            await self._app.shutdown()

        except Exception as e:
            confserverlog.exception(f"{e}")

    async def _handle_base(self, request: Request) -> Response:
        try:
            bots = db_get().table("bots").all()
            clients = db_get().table("clients").all()
            mq_sessions = []
            for (session, _) in bumper.mqtt_server.broker._sessions.values():
                mq_sessions.append(
                    {
                        "username": session.username,
                        "client_id": session.client_id,
                        "state": session.transitions.state,
                    }
                )
            all = {
                "bots": bots,
                "clients": clients,
                "helperbot": {"connected": bumper.mqtt_helperbot.is_connected},
                "mqtt_server": {
                    "state": bumper.mqtt_server.state,
                    "sessions": {
                        "count": len(mq_sessions),
                        "clients": mq_sessions,
                    },
                },
                "xmpp_server": bumper.xmpp_server,
            }
            return aiohttp_jinja2.render_template("home.jinja2", request, context=all)
        except Exception as e:
            confserverlog.exception(f"{e}")

        raise HTTPInternalServerError

    @web.middleware
    async def _log_all_requests(
        self, request: Request, handler: Handler
    ) -> StreamResponse:
        if request._match_info.route.name not in self._EXCLUDE_FROM_LOGGING:
            to_log = {
                "request": {
                    "route_name": f"{request.match_info.route.name}",
                    "method": f"{request.method}",
                    "path": f"{request.path}",
                    "query_string": f"{request.query_string}",
                    "raw_path": f"{request.raw_path}",
                    "raw_headers": f'{",".join(map("{}".format, request.raw_headers))}',
                }
            }
            try:
                postbody = None
                if request.content_length:
                    if request.content_type == "application/x-www-form-urlencoded":
                        postbody = await request.post()

                    elif request.content_type == "application/json":
                        try:
                            postbody = json.loads(await request.text())
                        except Exception as e:
                            confserverlog.error(f"Request body not json: {e}")
                            raise HTTPBadRequest(reason="Body was not json")

                    else:
                        postbody = await request.post()

                to_log["request"]["body"] = f"{postbody}"

                response = await handler(request)
                if response is None:
                    confserverlog.warning("Response was null!")
                    confserverlog.warning(json.dumps(to_log))
                    raise HTTPNoContent

                to_log["response"] = {
                    "status": f"{response.status}",
                }
                if (
                    "application/octet-stream" not in response.content_type
                    and isinstance(response, Response)
                ):
                    to_log["response"]["body"] = f"{json.loads(response.body)}"

                confserverlog.debug(json.dumps(to_log))

                return response

            except web.HTTPNotFound as notfound:
                confserverlog.debug(f"Request path {request.raw_path} not found")
                confserverlog.debug(json.dumps(to_log))
                return notfound

            except Exception as e:
                confserverlog.exception(f"{e}")
                confserverlog.error(json.dumps(to_log))
                raise e

        else:
            return await handler(request)

    async def _restart_helper_bot(self) -> None:
        await bumper.mqtt_helperbot.disconnect()
        asyncio.create_task(bumper.mqtt_helperbot.start())

    async def _restart_mqtt_server(self) -> None:
        loop = asyncio.get_event_loop()

        if bumper.mqtt_server.state not in ["stopped", "not_started"]:
            # close session writers - this was required so bots would reconnect properly after restarting
            for sess in list(bumper.mqtt_server.broker._sessions):
                sessobj = bumper.mqtt_server.broker._sessions[sess][1]
                if sessobj.session.transitions.state == "connected":
                    await sessobj.writer.close()

            loop.call_later(
                0.1, lambda: asyncio.create_task(bumper.mqtt_server.shutdown())
            )

        loop.call_later(1.5, lambda: asyncio.create_task(bumper.mqtt_server.start()))

    async def _handle_restart_service(self, request: Request) -> Response:
        try:
            service = request.match_info.get("service", "")
            if service == "Helperbot":
                await self._restart_helper_bot()
                return web.json_response({"status": "complete"})
            if service == "MQTTServer":
                asyncio.create_task(self._restart_mqtt_server())
                aloop = asyncio.get_event_loop()
                aloop.call_later(
                    5, lambda: asyncio.create_task(self._restart_helper_bot())
                )  # In 5 seconds restart Helperbot

                return web.json_response({"status": "complete"})
            if service == "XMPPServer":
                bumper.xmpp_server.disconnect()
                await bumper.xmpp_server.start_async_server()
                return web.json_response({"status": "complete"})

            return web.json_response({"status": "invalid service"})
        except Exception as e:
            confserverlog.exception(f"{e}")
            raise

    async def _handle_remove_bot(self, request: Request) -> Response:
        try:
            did = request.match_info.get("did", "")
            bot_remove(did)
            if bot_get(did):
                return web.json_response({"status": "failed to remove bot"})
            else:
                return web.json_response({"status": "successfully removed bot"})

        except Exception as e:
            confserverlog.exception(f"{e}")

        raise HTTPInternalServerError

    async def _handle_remove_client(self, request: Request) -> Response:
        try:
            resource = request.match_info.get("resource", "")
            client_remove(resource)
            if client_get(resource):
                return web.json_response({"status": "failed to remove client"})
            else:
                return web.json_response({"status": "successfully removed client"})

        except Exception as e:
            confserverlog.exception(f"{e}")

        raise HTTPInternalServerError

    async def _handle_lookup(self, request: Request) -> Response:
        try:
            if request.content_type == "application/x-www-form-urlencoded":
                body = await request.post()
            else:
                body = json.loads(await request.text())

            confserverlog.debug(body)

            if body["todo"] == "FindBest":
                service = body["service"]
                if service == "EcoMsgNew":
                    srvip = bumper.bumper_announce_ip
                    srvport = 5223
                    confserverlog.info(
                        "Announcing EcoMsgNew Server to bot as: {}:{}".format(
                            srvip, srvport
                        )
                    )
                    server = json.dumps({"ip": srvip, "port": srvport, "result": "ok"})
                    # bot seems to be very picky about having no spaces, only way was with text
                    server = server.replace(" ", "")
                    return web.json_response(text=server)

                elif service == "EcoUpdate":
                    srvip = "47.88.66.164"  # EcoVacs Server
                    srvport = 8005
                    confserverlog.info(
                        "Announcing EcoUpdate Server to bot as: {}:{}".format(
                            srvip, srvport
                        )
                    )
                    return web.json_response(
                        {"result": "ok", "ip": srvip, "port": srvport}
                    )

            return web.json_response({})

        except Exception as e:
            confserverlog.exception(f"{e}")

        raise HTTPInternalServerError

    async def _handle_newauth(self, request: Request) -> Response:
        # Bumper is only returning the submitted token. No reason yet to create another new token
        try:
            if request.content_type == "application/x-www-form-urlencoded":
                postbody = await request.post()
            else:
                postbody = json.loads(await request.text())

            confserverlog.debug(postbody)

            body = {"authCode": postbody["itToken"], "result": "ok", "todo": "result"}

            return web.json_response(body)

        except Exception as e:
            confserverlog.exception(f"{e}")

        raise HTTPInternalServerError

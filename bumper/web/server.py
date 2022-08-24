"""Web server module."""
import asyncio
import dataclasses
import json
import logging
import os
import ssl

import aiohttp
import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp.web_request import Request
from aiohttp.web_response import Response

import bumper
from bumper.db import bot_get, bot_remove, client_get, client_remove, db_get
from bumper.dns import get_resolver_with_public_nameserver
from bumper.util import get_logger
from bumper.web.middlewares import log_all_requests
from bumper.web.plugins import add_plugins


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
proxymodelog = logging.getLogger("proxymode")


@dataclasses.dataclass(frozen=True)
class WebserverBinding:
    """Webserver binding."""

    host: str
    port: int
    use_ssl: bool


class WebServer:
    """Web server."""

    def __init__(
        self, bindings: list[WebserverBinding] | WebserverBinding, proxy_mode: bool
    ):
        self._runners: list[web.AppRunner] = []

        if isinstance(bindings, WebserverBinding):
            bindings = [bindings]
        self._bindings = bindings

        self._app = web.Application(
            middlewares=[
                log_all_requests,
            ],
        )
        aiohttp_jinja2.setup(
            self._app,
            loader=jinja2.FileSystemLoader(
                os.path.join(bumper.bumper_dir, "bumper", "web", "templates")
            ),
        )
        self._add_routes(proxy_mode)
        self._app.freeze()  # no modification allowed anymore

    def _add_routes(self, proxy_mode: bool) -> None:
        self._app.add_routes(
            [
                web.get("/bot/remove/{did}", self._handle_remove_bot),
                web.get(
                    "/client/remove/{resource}",
                    self._handle_remove_client,
                ),
                web.get(
                    "/restart_{service}",
                    self._handle_restart_service,
                ),
            ]
        )

        if proxy_mode:
            self._app.add_routes(
                [
                    web.route("*", "/{path:.*}", self._handle_proxy),
                ]
            )
        else:
            self._app.add_routes(
                [
                    web.get("", self._handle_base),
                    web.post("/lookup.do", self._handle_lookup),
                    web.post("/newauth.do", self._handle_newauth),
                ]
            )
            add_plugins(self._app)

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

    async def _restart_helper_bot(self) -> None:
        await bumper.mqtt_helperbot.disconnect()
        asyncio.create_task(bumper.mqtt_helperbot.start())

    async def _restart_mqtt_server(self) -> None:
        if bumper.mqtt_server.state not in ["stopped", "not_started"]:
            await bumper.mqtt_server.shutdown()

        asyncio.create_task(bumper.mqtt_server.start())

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

    async def _handle_proxy(self, request: Request) -> Response:
        try:
            if request.raw_path == "/":
                return await self._handle_base(request)
            if request.raw_path == "/lookup.do":
                return await self._handle_lookup(request)
                # use bumper to handle lookup so bot gets Bumper IP and not Ecovacs

            async with aiohttp.ClientSession(
                headers=request.headers,
                connector=aiohttp.TCPConnector(
                    verify_ssl=False, resolver=get_resolver_with_public_nameserver()
                ),
            ) as session:
                if request.content.total_bytes > 0:
                    read_body = await request.read()
                    proxymodelog.info(
                        f"HTTP Proxy Request to EcoVacs (body=true) (URL:{request.url}) - {read_body.decode('utf-8')}"
                    )
                    if request.content_type == "application/x-www-form-urlencoded":
                        # android apps use form
                        fdata = await request.post()
                        async with session.request(
                            request.method, request.url, data=fdata
                        ) as resp:
                            response = await resp.text()
                            proxymodelog.info(
                                f"HTTP Proxy Response from EcoVacs (URL: {request.url}) - (Status: {resp.status}) - {response}"
                            )
                    else:
                        # handle json
                        async with session.request(
                            request.method, request.url, json=request.json()
                        ) as resp:
                            response = await resp.text()
                            proxymodelog.info(
                                f"HTTP Proxy Response from EcoVacs (URL: {request.url}) - (Status: {resp.status}) - {response}"
                            )

                else:
                    proxymodelog.info(
                        f"HTTP Proxy Request to EcoVacs (body=false) (URL:{request.url})"
                    )
                    async with session.request(request.method, request.url) as resp:
                        if resp.content_type == "application/octet-stream":
                            proxymodelog.info(
                                f"HTTP Proxy Response from EcoVacs (URL: {request.url}) - (Status: {resp.status}) - <BYTES CONTENT>"
                            )
                            return web.Response(body=await resp.read())
                        else:
                            response = await resp.text()
                            proxymodelog.info(
                                f"HTTP Proxy Response from EcoVacs (URL: {request.url}) - (Status: {resp.status}) - {response}"
                            )

                if resp.status == 200:
                    if resp.content_type == "application/json":
                        response = json.loads(response)
                        return web.json_response(response)
                    if resp.content_type == "application/octet-stream":
                        return web.Response(body=response)

                return web.Response(text=response)
        except asyncio.CancelledError:
            proxymodelog.exception(
                f"Request cancelled or timeout - {request.url}", exc_info=True
            )
            raise

        except Exception:
            proxymodelog.exception("An exception occurred", exc_info=True)

        raise HTTPInternalServerError

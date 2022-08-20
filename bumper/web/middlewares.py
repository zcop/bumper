"""Web server middleware module."""
import json
from typing import Any

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_exceptions import HTTPNoContent
from aiohttp.web_request import Request
from aiohttp.web_response import Response, StreamResponse

from bumper.util import get_logger

_LOGGER = get_logger("webserver_requests")


class CustomEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


_EXCLUDE_FROM_LOGGING = ["base", "remove-bot", "remove-client", "restart-service"]


@web.middleware
async def log_all_requests(request: Request, handler: Handler) -> StreamResponse:
    if request.match_info.route.name not in _EXCLUDE_FROM_LOGGING:
        to_log = {
            "request": {
                "method": request.method,
                "url": str(request.url),
                "path": request.path,
                "query_string": request.query_string,
                "headers": {h for h in request.headers.items()},
            }
        }

        if request.match_info.route.resource:
            to_log["request"][
                "route_resource"
            ] = request.match_info.route.resource.canonical

        try:
            if request.content_length:
                if request.content_type == "application/json":
                    to_log["request"]["body"] = await request.json()
                else:
                    to_log["request"]["body"] = {h for h in await request.post()}

            response = await handler(request)
            if response is None:
                _LOGGER.warning(  # type:ignore[unreachable]
                    "Response was null!"
                )
                _LOGGER.warning(json.dumps(to_log, cls=CustomEncoder))
                raise HTTPNoContent

            to_log["response"] = {
                "status": f"{response.status}",
            }

            if isinstance(response, Response) and response.body:
                assert response.text
                if response.content_type == "application/json":
                    to_log["response"]["body"] = json.loads(response.text)
                elif response.content_type.startswith("text"):
                    to_log["response"]["body"] = response.text

            return response

        except web.HTTPNotFound:
            _LOGGER.debug(f"Request path {request.raw_path} not found")
            raise

        except Exception:
            _LOGGER.exception(
                "An exception occurred in the logging middleware.", exc_info=True
            )
            raise

        finally:
            _LOGGER.debug(json.dumps(to_log, cls=CustomEncoder))

    else:
        return await handler(request)

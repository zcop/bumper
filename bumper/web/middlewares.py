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
    """Custom json encoder, which supports set."""

    def default(self, o: Any) -> Any:
        """Convert objects, which are not supported by the default JSONEncoder."""
        if isinstance(o, set):
            return list(o)
        return json.JSONEncoder.default(self, o)


_EXCLUDE_FROM_LOGGING = [
    "/",
    "/bot/remove/{did}",
    "/client/remove/{resource}",
    "/restart_{service}",
]


@web.middleware
async def log_all_requests(  # pylint: disable=too-many-branches
    request: Request, handler: Handler
) -> StreamResponse:
    """Middleware to log all requests."""
    if (
        not request.match_info.route.resource
    ) or request.match_info.route.resource.canonical in _EXCLUDE_FROM_LOGGING:
        return await handler(request)

    to_log = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "path": request.path,
            "query_string": request.query_string,
            "headers": set(request.headers.items()),
            "route_resource": request.match_info.route.resource.canonical,
        }
    }

    try:
        try:
            if request.content_length:
                if request.content_type == "application/json":
                    to_log["request"]["body"] = await request.json()
                else:
                    to_log["request"]["body"] = set(await request.post())
        except Exception:
            _LOGGER.exception(
                "An exception occurred during logging the request.", exc_info=True
            )
            raise

        response = await handler(request)

        try:
            if response is None:
                _LOGGER.warning(  # type:ignore[unreachable]
                    "Response was null!"
                )
                _LOGGER.warning(json.dumps(to_log, cls=CustomEncoder))
                raise HTTPNoContent

            to_log["response"] = {
                "status": f"{response.status}",
                "headers": set(response.headers.items()),
            }

            if isinstance(response, Response) and response.body:
                assert response.text
                if response.content_type == "application/json":
                    to_log["response"]["body"] = json.loads(response.text)
                elif response.content_type.startswith("text"):
                    to_log["response"]["body"] = response.text

            return response
        except Exception:
            _LOGGER.exception(
                "An exception occurred during logging the response", exc_info=True
            )
            raise

    except web.HTTPNotFound:
        _LOGGER.debug("Request path %s not found", request.raw_path)
        raise

    finally:
        _LOGGER.debug(json.dumps(to_log, cls=CustomEncoder))

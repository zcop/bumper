from abc import abstractmethod
from enum import Enum
from typing import Iterable

from aiohttp.web_routedef import AbstractRouteDef


class ConfServerApp:
    name = None
    plugin_type = None
    path_prefix = None
    app = None
    sub_api = None
    routes = None


class WebserverSubApi(str, Enum):
    """Enum with all different sub apis."""

    V1 = "v1"
    V2 = "v2"
    API = "api"
    UPLOAD = "upload"


class WebserverPlugin:
    """Abstract webserver plugin."""

    @property
    @abstractmethod
    def sub_api(self) -> WebserverSubApi:
        """Sub api."""
        raise NotImplementedError

    @property
    @abstractmethod
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        raise NotImplementedError

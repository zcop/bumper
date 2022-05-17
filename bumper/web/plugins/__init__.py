"""Webserver plugin module."""
import inspect
import sys
from abc import abstractmethod
from glob import glob
from os.path import dirname, isfile, join
from types import ModuleType
from typing import Any, Iterable

from aiohttp import web
from aiohttp.web_response import Response
from aiohttp.web_routedef import AbstractRouteDef

from bumper.models import RETURN_API_SUCCESS
from bumper.util import get_current_time_as_millis


class WebserverPlugin:
    """Abstract webserver plugin."""

    @property
    @abstractmethod
    def routes(self) -> Iterable[AbstractRouteDef]:
        """Plugin routes."""
        raise NotImplementedError


def _add_routes(
    app: web.Application, module: ModuleType, plugin_module_name: str
) -> None:
    if not module.__name__.startswith(plugin_module_name):
        return

    assert module.__file__ is not None
    if module.__file__.endswith("__init__.py"):
        sub_app = web.Application()
    else:
        sub_app = app

    for _, clazz in inspect.getmembers(module, inspect.isclass):
        if not issubclass(clazz, WebserverPlugin) or clazz == WebserverPlugin:
            continue

        obj = clazz()
        sub_app.add_routes(obj.routes)

    for _, obj in inspect.getmembers(module, inspect.ismodule):
        _add_routes(sub_app, obj, plugin_module_name)

    if module.__file__.endswith("__init__.py"):
        prefix = module.__file__.removesuffix("/__init__.py")
        prefix = prefix[prefix.rindex("/") :] + "/"
        app.add_subapp(prefix, sub_app)


def _import_plugins(module: ModuleType) -> None:
    assert module.__file__ is not None
    for file in glob(join(dirname(module.__file__), "**/*.py"), recursive=True):
        if not isfile(file) or file == module.__file__:
            continue

        name = file.replace("/", ".")
        name = name[name.find(module.__name__) : -3].removesuffix(".__init__")

        __import__(name)


def add_plugins(app: web.Application) -> None:
    """Discover and add all plugin to app."""
    module = sys.modules[__name__]
    _import_plugins(module)

    plugin_module_name = module.__name__
    for _, obj in inspect.getmembers(module, inspect.ismodule):
        if not obj.__name__.startswith(plugin_module_name):
            continue

        _add_routes(app, obj, plugin_module_name)


def get_success_response(data: Any) -> Response:
    """Get success response with provided data."""
    body = {
        "code": RETURN_API_SUCCESS,
        "data": data,
        "msg": "操作成功",
        "success": True,
        "time": get_current_time_as_millis(),
    }

    return web.json_response(body)

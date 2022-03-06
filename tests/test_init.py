import asyncio
import os

from testfixtures import LogCapture

import bumper
from bumper import strtobool


def test_strtobool():
    assert strtobool("t") == True
    assert strtobool("f") == False
    assert strtobool(0) == False


async def test_start_stop():
    with LogCapture() as l:
        if os.path.exists("tests/tmp.db"):
            os.remove("tests/tmp.db")  # Remove existing db

        asyncio.create_task(bumper.start())
        await asyncio.sleep(0.1)
        l.check_present(("bumper", "INFO", "Starting Bumper"))
        l.clear()

        await bumper.shutdown()
        l.check_present(
            ("bumper", "INFO", "Shutting down"), ("bumper", "INFO", "Shutdown complete")
        )
        assert bumper.shutting_down == True


async def test_start_stop_debug():
    with LogCapture() as l:
        if os.path.exists("tests/tmp.db"):
            os.remove("tests/tmp.db")  # Remove existing db

        bumper.bumper_listen = "0.0.0.0"
        bumper.bumper_debug = True
        asyncio.create_task(bumper.start())

        await asyncio.sleep(0.1)
        while bumper.mqtt_server.state == "starting":
            await asyncio.sleep(0.1)
        l.check_present(("bumper", "INFO", "Starting Bumper"))
        l.clear()

        asyncio.create_task(bumper.shutdown())
        await asyncio.sleep(0.1)
        l.check_present(
            ("bumper", "INFO", "Shutting down"), ("bumper", "INFO", "Shutdown complete")
        )
        assert bumper.shutting_down == True

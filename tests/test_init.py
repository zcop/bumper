import asyncio
import os

import pytest
from testfixtures import LogCapture

import bumper
from bumper import strtobool


def test_strtobool():
    assert strtobool("t") is True
    assert strtobool("f") is False
    assert strtobool(0) is False


@pytest.mark.parametrize("debug", [False, True])
async def test_start_stop(debug: bool):
    with LogCapture() as l:
        if os.path.exists("tests/tmp.db"):
            os.remove("tests/tmp.db")  # Remove existing db

        if debug:
            bumper.bumper_debug = True

        asyncio.create_task(bumper.start())
        await asyncio.sleep(0.1)
        l.check_present(("bumper", "INFO", "Starting Bumper"))
        while True:
            try:
                l.check_present(("bumper", "INFO", "Bumper started successfully"))
                break
            except AssertionError:
                pass
            await asyncio.sleep(0.1)

        l.clear()

        await bumper.shutdown()
        l.check_present(
            ("bumper", "INFO", "Shutting down"), ("bumper", "INFO", "Shutdown complete")
        )
        assert bumper.shutting_down is True

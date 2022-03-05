import datetime

from bumper.util import convert_to_millis


def test_get_milli_time():
    assert (
        convert_to_millis(
            datetime.datetime(
                2018, 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
            ).timestamp()
        )
        == 1514768400000
    )

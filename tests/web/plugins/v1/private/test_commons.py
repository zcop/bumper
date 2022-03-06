import json

from bumper.models import RETURN_API_SUCCESS


async def test_getAreas(webserver_client):
    resp = await webserver_client.get(
        "/v1/private/us/en/dev_1234/ios/1/0/0/common/getAreas"
    )
    assert resp.status == 200
    text = await resp.text()
    jsonresp = json.loads(text)
    assert jsonresp["code"] == RETURN_API_SUCCESS

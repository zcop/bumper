"""Api pim module plugin."""
import json
import os
from typing import Any


def get_product_iot_map() -> tuple[Any]:
    """Get product iot map."""
    with open(
        os.path.join(os.path.dirname(__file__), "productIotMap.json"),
        encoding="utf-8",
    ) as file:
        return (json.load(file),)

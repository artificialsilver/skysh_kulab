from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.constants import MARKETS


UPBIT_TICKER_URL = "https://api.upbit.com/v1/ticker"


def fetch_upbit_tickers(markets: tuple[str, ...] = MARKETS, timeout: float = 3.0) -> dict[str, float]:
    query = urlencode({"markets": ",".join(markets)})
    request = Request(
        f"{UPBIT_TICKER_URL}?{query}",
        headers={"Accept": "application/json", "User-Agent": "skysh-kulab/0.1"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return {item["market"]: float(item["trade_price"]) for item in payload}


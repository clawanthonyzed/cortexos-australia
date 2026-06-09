"""FX rate fetcher — USD→AUD daily rate from Reserve Bank of Australia XML feed.

RBA publishes rates at: https://www.rba.gov.au/statistics/frequency/exchange-rates.html
XML endpoint: https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml

Rate is cached in memory for 24 hours to avoid hammering the RBA endpoint.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
import structlog

logger = structlog.get_logger(__name__)

_CACHE: dict[str, float | float] = {"rate": 1.55, "updated_at": 0.0}
_CACHE_TTL = 86_400  # 24 hours
_RBA_XML_URL = "https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml"


async def get_usd_aud_rate() -> float:
    """Return current USD→AUD rate. Falls back to 1.55 on error."""
    now = time.time()
    if now - _CACHE["updated_at"] < _CACHE_TTL:
        return float(_CACHE["rate"])

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_RBA_XML_URL)
            resp.raise_for_status()
            xml = resp.text

        # Parse USD/AUD from XML — look for USD item
        import re
        match = re.search(
            r"<cb:baseCurrency>USD</cb:baseCurrency>.*?<cb:targetCurrency>AUD</cb:targetCurrency>.*?<cb:exchangeRate>([\d.]+)</cb:exchangeRate>",
            xml,
            re.DOTALL,
        )
        if match:
            rate = float(match.group(1))
            _CACHE["rate"] = rate
            _CACHE["updated_at"] = now
            logger.info("FX rate updated", usd_aud=rate)
            return rate
    except Exception as exc:
        logger.warning("FX rate fetch failed, using cached value", error=str(exc))

    return float(_CACHE["rate"])

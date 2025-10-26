from __future__ import annotations
import os
import httpx
from typing import List, Dict, Any

OKLINK_KEY = os.environ.get("OKLINK_API_KEY")

HEADERS = {
    "User-Agent": "Top100Bot/1.0",
    "Ok-Access-Key": OKLINK_KEY or "",
}

BASE = "https://www.oklink.com/api/v5/explorer/address"

async def get_top_100() -> List[Dict[str, Any]]:
    # OKLink: 'top holders' lists up to top 300.
    # Endpoint (subject to change): /top-holders?chainShortName=eth&tokenContractAddress=
    # For native ETH, contract is empty; OKLink uses 'top-holders' for token & native.
    if not OKLINK_KEY:
        return []
    params = {
        "chainShortName": "eth",
        "size": "100",
        # no tokenContractAddress for native chain coin
    }
    url = f"{BASE}/top-holders"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code != 200:
            return []
        data = r.json()
        # Expected schema: data[0].holderList with address and balance
        try:
            holder_list = data["data"][0]["holderList"]
        except Exception:
            return []
        out: List[Dict[str, Any]] = []
        for i, h in enumerate(holder_list[:100], start=1):
            bal = h.get("balance", "0").replace(",", "")
            try:
                bal = float(bal)
            except:
                bal = 0.0
            out.append({
                "address": h.get("address"),
                "name_tag": h.get("tag"),
                "balance_eth": bal,
                "source": "oklink",
            })
        # Ensure sorted
        out.sort(key=lambda x: x.get("balance_eth", 0.0), reverse=True)
        return out[:100]

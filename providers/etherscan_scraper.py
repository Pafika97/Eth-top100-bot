from __future__ import annotations
import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import os

ETHERSCAN_BASE = os.environ.get("ETHERSCAN_BASE", "https://etherscan.io")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Top100Bot/1.0; +https://example.com)"
}

async def fetch_page(client: httpx.AsyncClient, page: int) -> List[Dict[str, Any]]:
    # Etherscan 'Top Accounts by ETH Balance' paginator
    url = f"{ETHERSCAN_BASE}/accounts/{page}"
    r = await client.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table")
    if not table:
        return []
    rows = table.find_all("tr")
    items: List[Dict[str, Any]] = []
    for tr in rows[1:]:
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        # Columns usually: Rank, Address, Name Tag, Balance, %
        rank = int(tds[0].get_text(strip=True).replace("#","") or "0")
        address_link = tds[1].find("a")
        address = address_link.get_text(strip=True) if address_link else tds[1].get_text(strip=True)
        name_tag = tds[2].get_text(strip=True)
        bal_text = tds[3].get_text(strip=True).split(" ETH")[0].replace(",","")
        try:
            balance_eth = float(bal_text)
        except:
            continue
        items.append({
            "address": address,
            "name_tag": name_tag or None,
            "balance_eth": balance_eth,
            "source": "etherscan",
        })
    return items

async def get_top_100() -> List[Dict[str, Any]]:
    # 25 rows per page typically; fetch first 4 pages (1..4)
    out: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [fetch_page(client, p) for p in range(1,5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                out.extend(res)
    # Ensure sorted by balance desc, then slice 100
    out.sort(key=lambda x: x.get("balance_eth", 0.0), reverse=True)
    return out[:100]

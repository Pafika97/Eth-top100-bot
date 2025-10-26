from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any

DATA_PATH = Path(__file__).parent / "data"
DATA_PATH.mkdir(parents=True, exist_ok=True)
STATE_FILE = DATA_PATH / "last_top100_eth.json"

def load_last() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_current(addresses: List[Dict[str, Any]]) -> None:
    payload = {item["address"].lower(): item for item in addresses}
    STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def compute_changes(current: List[Dict[str, Any]]):
    last = load_last()
    out = []
    for rank, item in enumerate(current, start=1):
        a = item["address"].lower()
        last_item = last.get(a)
        change_pct = None
        if last_item:
            prev_bal = float(last_item.get("balance_eth", 0.0))
            curr_bal = float(item.get("balance_eth", 0.0))
            if prev_bal > 0:
                change_pct = (curr_bal - prev_bal) / prev_bal * 100.0
            elif curr_bal > 0:
                change_pct = float("inf")
        # Attach computed fields
        new_item = dict(item)
        new_item["rank"] = rank
        new_item["change_pct"] = change_pct
        new_item["flag_50"] = (abs(change_pct) >= 50.0) if (change_pct not in (None, float("inf"))) else True if change_pct == float("inf") else False
        out.append(new_item)
    return out

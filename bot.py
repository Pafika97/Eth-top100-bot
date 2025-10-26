from __future__ import annotations
import asyncio
import os
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from storage import compute_changes, save_current
from providers import etherscan_scraper as es
from providers import oklink_api as ok

def format_row(item: Dict[str, Any]) -> str:
    addr = item['address']
    bal = item['balance_eth']
    tag = f" — {item['name_tag']}" if item.get('name_tag') else ""
    src = item.get('source', 'n/a')
    ch = item.get('change_pct')
    flag = " ⚠️50%+" if item.get('flag_50') else ""
    ch_str = ""
    if ch is None:
        ch_str = " (new)"
    elif ch == float('inf'):
        ch_str = " (new balance)"
    else:
        ch_str = f" ({ch:+.1f}%)"
    return f"{item['rank']:>3}. <code>{addr}</code>{tag}\n     {bal:,.4f} ETH • src:{src}{ch_str}{flag}"

async def fetch_top100() -> List[Dict[str, Any]]:
    # Try OKLink first if key provided; fall back to Etherscan scraping
    data: List[Dict[str, Any]] = []
    try:
        data = await ok.get_top_100()
    except Exception:
        data = []
    if not data:
        data = await es.get_top_100()
    return data

async def handle_top100(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    data = await fetch_top100()
    enriched = compute_changes(data)
    # Persist new snapshot
    save_current(enriched)
    # Build message chunks (Telegram limit ~4096 chars)
    header = "<b>ETH — Top 100 richest addresses</b>\nMarked with ⚠️ if balance changed >50% since last check."
    lines = [format_row(x) for x in enriched]
    chunks = []
    cur = header
    for line in lines:
        if len(cur) + len(line) + 2 > 3800:
            chunks.append(cur)
            cur = ""
        cur += ("\n" + line)
    if cur:
        chunks.append(cur)
    for i, ch in enumerate(chunks, start=1):
        suffix = f"\n\nPart {i}/{len(chunks)}"
        await update.message.reply_text(ch + suffix, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        "Привет! Я бот для списка топ‑100 кошельков ETH.\n"
        "Команда: /top100 — показать топ‑100 и отметить кошельки с изменением >50%"
    )
    await update.message.reply_text(txt)

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN in environment")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top100", handle_top100))
    app.run_polling()

if __name__ == "__main__":
    main()

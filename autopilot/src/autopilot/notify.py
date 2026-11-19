"""通知（Discord Webhook・無料）。未設定ならログ出力のみ。"""
from __future__ import annotations

import logging
import os

import requests

log = logging.getLogger(__name__)


def notify(title: str, body: str = "", level: str = "info") -> None:
    icon = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "error": "🚨"}.get(level, "")
    text = f"{icon} **{title}**\n{body}".strip()
    log.info("notify: %s", text.replace("\n", " | "))
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    try:
        requests.post(url, json={"content": text[:1900]}, timeout=15)
    except requests.RequestException as e:  # 通知の失敗で本処理は止めない
        log.warning("discord notify failed: %s", e)

"""オフライン動作確認用：sample/products.json を DB に取り込む（API キー不要）。"""
from __future__ import annotations

import json
from datetime import timedelta

from ..config import Settings, now_jst
from ..db import DB
from . import amazon_search_url, clean_name


def load_sample(settings: Settings, db: DB) -> dict[str, int]:
    data = json.loads((settings.root / "sample" / "products.json").read_text(encoding="utf-8"))
    today = now_jst().date()
    stats: dict[str, int] = {}
    for item in data["items"]:
        # 7日前のスナップショットも入れて、値下がり・順位上昇シグナルの検出も試せるようにする
        for days_ago, key in ((7, "past"), (0, "now")):
            snap = item[key]
            db.upsert_product({
                "source": "sample",
                "item_code": item["item_code"],
                "genre_key": item["genre_key"],
                "name": item["name"],
                "short_name": item.get("short_name") or clean_name(item["name"]),
                "shop": item.get("shop"),
                "caption": item.get("caption", ""),
                "image_url": None,
                "affiliate_url": item.get("url"),
                "amazon_url": amazon_search_url(item.get("short_name") or item["name"], "sample-22"),
                "date": (today - timedelta(days=days_ago)).isoformat(),
                **snap,
            })
        stats[item["genre_key"]] = stats.get(item["genre_key"], 0) + 1
    return stats

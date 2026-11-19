"""トレンドシグナル（無料RSS）と、DB 上の価格・順位推移から「ネタの強さ」を作る。

RSS のニュース本文から投稿を作ることはしない（誤情報防止）。
「そのジャンルがいま話題か」の重み付けにだけ使う。
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

from ..config import Settings, now_jst
from ..db import DB

log = logging.getLogger(__name__)

FEEDS = {
    "google_trends": "https://trends.google.co.jp/trending/rss?geo=JP",
    "prtimes": "https://prtimes.jp/index.rdf",
}


def collect_rss(settings: Settings, db: DB) -> int:
    try:
        import feedparser
    except ImportError:
        return 0
    n = 0
    now = now_jst().isoformat()
    for src, url in FEEDS.items():
        try:
            feed = feedparser.parse(url, agent="autopilot-rss/1.0")
        except Exception as e:  # pragma: no cover
            log.warning("rss %s failed: %s", src, e)
            continue
        for entry in feed.entries[:100]:
            title = entry.get("title", "")
            for g in settings.genres:
                if g["keyword"] in title or g["label"] in title:
                    db.exec("INSERT INTO signals (kind, genre_key, strength, detail, created_at) VALUES (?,?,?,?,?)",
                            ("trend" if src == "google_trends" else "news", g["key"], 1.0, title[:200], now))
                    n += 1
    return n


def detect_product_signals(settings: Settings, db: DB) -> int:
    """順位の急上昇・値下がり・新規ランクインを検出。"""
    n = 0
    now = now_jst().isoformat()
    for g in settings.genres:
        for p in db.latest_products(g["key"], limit=30):
            hist = db.snapshot_history(p["id"], limit=8)
            if len(hist) == 1:
                if p.get("rank") and p["rank"] <= 10 and len(db.q("SELECT 1 FROM product_snapshots s JOIN products x ON x.id=s.product_id WHERE x.genre_key=? GROUP BY s.date", (g["key"],))) > 1:
                    _sig(db, "new_entry", g["key"], p["id"], 1.0, f"{p['short_name']} が新しくランクイン", now)
                    n += 1
                continue
            cur, old = hist[0], hist[-1]
            if cur["rank"] and old["rank"] and old["rank"] - cur["rank"] >= 5:
                _sig(db, "rank_up", g["key"], p["id"], min(3.0, (old["rank"] - cur["rank"]) / 5),
                     f"{old['rank']}位→{cur['rank']}位", now)
                n += 1
            if cur["price"] and old["price"] and cur["price"] <= old["price"] * 0.9:
                _sig(db, "price_drop", g["key"], p["id"], min(3.0, (old["price"] - cur["price"]) / old["price"] * 10),
                     f"{old['price']:,}円→{cur['price']:,}円（{_days(old['date'], cur['date'])}日前比）", now)
                n += 1
    return n


def _days(a: str, b: str) -> int:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def _sig(db: DB, kind: str, genre: str, pid: int, strength: float, detail: str, now: str) -> None:
    today = now[:10]
    if db.one("SELECT 1 FROM signals WHERE kind=? AND product_id=? AND substr(created_at,1,10)=?", (kind, pid, today)):
        return
    db.exec("INSERT INTO signals (kind, genre_key, product_id, strength, detail, created_at) VALUES (?,?,?,?,?,?)",
            (kind, genre, pid, strength, detail, now))


def season_for(settings: Settings, genre_key: str, today: date | None = None) -> dict[str, Any] | None:
    today = today or now_jst().date()
    md = today.strftime("%m-%d")
    for ev in settings.calendar:
        s, e = ev["start"], ev["end"]
        inside = (s <= md <= e) if s <= e else (md >= s or md <= e)
        if inside and genre_key in ev.get("genres", []):
            return ev
    return None

"""楽天ウェブサービス（ランキングAPI / 商品検索API）からの商品収集。

- 無料（アプリID登録のみ）。1 リクエスト/秒程度に抑える。
- affiliateId を付けると、レスポンスの affiliateUrl に自分のアフィリエイトリンクが入る。
- API のベース URL は RAKUTEN_API_BASE で差し替え可能（楽天側のエンドポイント移行に備える）。
"""
from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any

import requests

from ..config import Settings, now_jst
from ..db import DB
from . import amazon_search_url, clean_name, is_excluded

log = logging.getLogger(__name__)

DEFAULT_BASE = "https://app.rakuten.co.jp/services/api"


class RakutenClient:
    def __init__(self, app_id: str, affiliate_id: str | None, base: str | None = None, access_key: str | None = None):
        self.app_id = app_id
        self.affiliate_id = affiliate_id
        self.access_key = access_key
        self.base = (base or DEFAULT_BASE).rstrip("/")
        self._last = 0.0
        self.session = requests.Session()

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        wait = 1.1 - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        p = {"applicationId": self.app_id, "format": "json", "formatVersion": 2, **params}
        if self.affiliate_id:
            p["affiliateId"] = self.affiliate_id
        if self.access_key:
            p["accessKey"] = self.access_key
        for attempt in range(3):
            r = self.session.get(f"{self.base}/{path}", params=p, timeout=30)
            self._last = time.time()
            if r.status_code == 429:
                time.sleep(2 ** attempt * 2)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()
        return {}

    def ranking(self, genre_id: str) -> list[dict[str, Any]]:
        data = self._get("IchibaItem/Ranking/20220601", {"genreId": genre_id})
        return [_item(i) for i in data.get("Items", [])]

    def search(self, keyword: str, genre_id: str | None = None, hits: int = 30, sort: str = "standard") -> list[dict[str, Any]]:
        params: dict[str, Any] = {"keyword": keyword, "hits": hits, "sort": sort, "availability": 1}
        if genre_id:
            params["genreId"] = genre_id
        data = self._get("IchibaItem/Search/20220601", params)
        return [_item(i) for i in data.get("Items", [])]


def _item(raw: dict[str, Any]) -> dict[str, Any]:
    i = raw.get("Item", raw)  # formatVersion 1/2 両対応
    imgs = i.get("mediumImageUrls") or []
    img = imgs[0] if imgs else None
    if isinstance(img, dict):
        img = img.get("imageUrl")
    return {
        "item_code": i.get("itemCode"),
        "name": i.get("itemName", ""),
        "price": int(i.get("itemPrice") or 0),
        "rank": i.get("rank"),
        "review_count": int(i.get("reviewCount") or 0),
        "review_avg": float(i.get("reviewAverage") or 0),
        "shop": i.get("shopName"),
        "caption": (i.get("itemCaption") or "")[:600],
        "url": i.get("affiliateUrl") or i.get("itemUrl"),
        "image_url": (img or "").replace("?_ex=128x128", "?_ex=500x500") or None,
        "genre_id": str(i.get("genreId") or ""),
    }


def resolve_genre_id(client: RakutenClient, db: DB, genre: dict[str, Any]) -> str | None:
    if genre.get("rakuten_genre_id"):
        return str(genre["rakuten_genre_id"])
    row = db.one("SELECT rakuten_genre_id FROM genre_ids WHERE genre_key=?", (genre["key"],))
    if row:
        return row["rakuten_genre_id"]
    items = client.search(genre["keyword"], hits=30, sort="-reviewCount")
    counts = Counter(i["genre_id"] for i in items if i["genre_id"] and not is_excluded(i["name"], genre))
    if not counts:
        return None
    gid = counts.most_common(1)[0][0]
    db.exec("INSERT OR REPLACE INTO genre_ids VALUES (?,?,?)", (genre["key"], gid, now_jst().isoformat()))
    log.info("genre %s -> rakuten genreId %s", genre["key"], gid)
    return gid


def collect(settings: Settings, db: DB) -> dict[str, int]:
    app_id = settings.env("RAKUTEN_APP_ID")
    if not app_id:
        raise RuntimeError("RAKUTEN_APP_ID が未設定です（.env または GitHub Secrets）")
    client = RakutenClient(app_id, settings.env("RAKUTEN_AFFILIATE_ID"), settings.env("RAKUTEN_API_BASE"),
                           settings.env("RAKUTEN_ACCESS_KEY"))
    tag = settings.env("AMAZON_ASSOCIATE_TAG")
    min_price = int(settings.get("content.min_price", 0))
    stats: dict[str, int] = {}
    for genre in settings.genres:
        try:
            gid = resolve_genre_id(client, db, genre)
            items = client.ranking(gid) if gid else []
            if len(items) < 5:  # ランキングが取れないジャンルは検索（レビュー件数順）で代用
                items = client.search(genre["keyword"], genre_id=gid, sort="-reviewCount")
                for n, it in enumerate(items, 1):
                    it["rank"] = it.get("rank") or n
        except requests.RequestException as e:
            log.warning("rakuten %s failed: %s", genre["key"], e)
            stats[genre["key"]] = 0
            continue
        saved = 0
        for it in items:
            if not it["item_code"] or it["price"] < min_price or is_excluded(it["name"], genre):
                continue
            short = clean_name(it["name"])
            db.upsert_product({
                **it,
                "source": "rakuten",
                "genre_key": genre["key"],
                "short_name": short,
                "affiliate_url": it["url"],
                "amazon_url": amazon_search_url(short, tag),
            })
            saved += 1
        stats[genre["key"]] = saved
    return stats

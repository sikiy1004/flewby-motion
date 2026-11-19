"""企画：ジャンル・フォーマット・フック型・テーマの選択と、投稿に載せる商品の決定。

- フォーマット／フック型／テーマは Thompson Sampling（arm_stats）で選ぶ → 成績の良い型に自動で寄る。
- 価格・順位・レビューなどの数値はすべて DB の実データ。LLM は文章だけを担当する。
"""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime
from typing import Any

from .collectors import extract_features
from .collectors.trends import season_for
from .config import Settings, now_jst
from .db import DB
from .scoring import score_products

FORMAT_MIN_PRODUCTS = {"ranking": 3, "price_band": 3, "spotlight": 3, "guide": 3}


class NoCandidate(Exception):
    pass


# ---------------- bandit ----------------
def sample_arm(db: DB, dim: str, options: list[str], rng: random.Random) -> str:
    best, best_v = options[0], -1.0
    for opt in options:
        row = db.one("SELECT alpha, beta FROM arm_stats WHERE arm_key=?", (f"{dim}:{opt}",))
        a, b = (row["alpha"], row["beta"]) if row else (1.0, 1.0)
        v = rng.betavariate(a, b)
        if v > best_v:
            best, best_v = opt, v
    return best


def reward_arm(db: DB, dim: str, opt: str, reward: float) -> None:
    reward = max(0.0, min(1.0, reward))
    key = f"{dim}:{opt}"
    row = db.one("SELECT alpha, beta FROM arm_stats WHERE arm_key=?", (key,))
    a, b = (row["alpha"], row["beta"]) if row else (1.0, 1.0)
    db.exec("INSERT OR REPLACE INTO arm_stats (arm_key, alpha, beta, updated_at) VALUES (?,?,?,?)",
            (key, a + reward, b + (1 - reward), now_jst().isoformat()))


# ---------------- helpers ----------------
def _popularity(p: dict[str, Any]) -> float:
    return (p.get("review_avg") or 0) * math.log10((p.get("review_count") or 0) + 10)


def _enrich(settings: Settings, p: dict[str, Any]) -> dict[str, Any]:
    g = settings.genre(p["genre_key"])
    text = f"{p['name']} {p.get('caption') or ''}"
    return {
        "id": p["id"],
        "item_code": p["item_code"],
        "name": p["short_name"],
        "full_name": p["name"],
        "price": p.get("price"),
        "rank": p.get("rank"),
        "review_count": p.get("review_count"),
        "review_avg": round(p.get("review_avg") or 0, 2),
        "features": extract_features(text, g.get("features", {})),
        "affiliate_url": p.get("affiliate_url"),
        "amazon_url": p.get("amazon_url"),
        "image_url": p.get("image_url") if settings.get("content.use_product_images") else None,
        "date": p.get("date"),
    }


def _picks(products: list[dict[str, Any]]) -> list[dict[str, str]]:
    """データから決まる「タイプ別のおすすめ」。"""
    picks = []
    if products:
        cheap = min(products, key=lambda p: p["price"] or 10**9)
        picks.append({"label": "価格重視なら", "name": cheap["name"], "reason": f"{cheap['price']:,}円で比較中いちばん手頃"})
        rated = max(products, key=lambda p: p["review_avg"] or 0)
        picks.append({"label": "評価重視なら", "name": rated["name"], "reason": f"レビュー平均★{rated['review_avg']:.2f}"})
        popular = max(products, key=lambda p: p["review_count"] or 0)
        picks.append({"label": "定番を選ぶなら", "name": popular["name"], "reason": f"レビュー{popular['review_count']:,}件"})
    return picks


def _select_products(settings: Settings, db: DB, fmt: str, genre_key: str, n: int) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    raw = db.latest_products(genre_key, limit=40)
    if not raw:
        return [], None
    signal = None
    if fmt == "ranking":
        chosen = raw[:n]
    elif fmt == "price_band":
        bands = [(0, 10000), (10000, 25000), (25000, 10**9)]
        chosen = []
        for lo, hi in bands:
            inside = [p for p in raw if lo <= (p["price"] or 0) < hi]
            if inside:
                chosen.append(max(inside, key=_popularity))
        if len(chosen) < 3:
            # 帯が足りなければ価格の安い順・高い順から補完
            rest = sorted([p for p in raw if p not in chosen], key=lambda p: p["price"] or 0)
            while len(chosen) < 3 and rest:
                chosen.append(rest.pop(len(rest) // 2))
        chosen.sort(key=lambda p: p["price"] or 0)
    elif fmt == "spotlight":
        used = db.recently_used_product_ids(int(settings.get("content.product_cooldown_days", 21)))
        sig = db.one(
            "SELECT * FROM signals WHERE genre_key=? AND product_id IS NOT NULL AND used=0 "
            "ORDER BY strength DESC, id DESC LIMIT 1", (genre_key,))
        main = None
        if sig:
            main = next((p for p in raw if p["id"] == sig["product_id"]), None)
            if main:
                signal = dict(sig)
        if main is None:
            fresh = [p for p in raw if p["id"] not in used] or raw
            main = max(fresh, key=_popularity)
        others = sorted([p for p in raw if p["id"] != main["id"]], key=_popularity, reverse=True)[:2]
        chosen = [main, *others]
    else:  # guide
        chosen = sorted(raw[:10], key=_popularity, reverse=True)[:3]
    return [_enrich(settings, p) for p in chosen], signal


def _genre_score(settings: Settings, db: DB, genre_key: str, now: datetime, rng: random.Random) -> float:
    last = db.last_used_genre_day(genre_key)
    days = 30.0 if not last else max(0.0, (now - datetime.fromisoformat(last)).total_seconds() / 86400)
    freshness = min(days, 10) / 10 + 0.05
    trend = db.one("SELECT COUNT(*) AS c FROM signals WHERE genre_key=? AND created_at >= ?",
                   (genre_key, (now.replace(hour=0, minute=0, second=0)).isoformat()))["c"]
    season = 1.3 if season_for(settings, genre_key, now.date()) else 1.0
    has_data = 1.0 if db.latest_products(genre_key, limit=3) else 0.0
    return has_data * freshness * season * (1 + 0.2 * min(trend, 5)) * rng.uniform(0.8, 1.2)


def pick_group(settings: Settings, db: DB, rng: random.Random, window: int = 20) -> str | None:
    """美容 / 暮らし(QOL) の比率を設定値に近づけるように、次に出すグループを決める。"""
    weights: dict[str, float] = dict(settings.get("content.group_weights", {}) or {})
    groups = {g.get("group", "beauty") for g in settings.genres}
    weights = {k: float(v) for k, v in weights.items() if k in groups and float(v) > 0}
    if len(weights) < 2:
        return next(iter(weights), None)
    total = sum(weights.values())
    group_of = {g["key"]: g.get("group", "beauty") for g in settings.genres}
    rows = db.q("SELECT genre_key FROM posts WHERE status NOT IN ('failed','skipped') ORDER BY id DESC LIMIT ?", (window,))
    if not rows:
        r, acc = rng.uniform(0, total), 0.0
        for k, w in weights.items():
            acc += w
            if r <= acc:
                return k
    counts = {k: 0 for k in weights}
    for r_ in rows:
        g = group_of.get(r_["genre_key"])
        if g in counts:
            counts[g] += 1
    n = sum(counts.values()) or 1
    deficit = {k: weights[k] / total - counts[k] / n + rng.uniform(-0.05, 0.05) for k in weights}
    return max(deficit, key=deficit.get)


def plan_post(settings: Settings, db: DB, kind: str, rng: random.Random | None = None) -> dict[str, Any]:
    """1 投稿分の企画を作って DB に登録（status=planned）。"""
    rng = rng or random.Random()
    now = now_jst()
    group = pick_group(settings, db, rng)
    genres = sorted(settings.genres, key=lambda g: (g.get("group", "beauty") == group,
                                                    _genre_score(settings, db, g["key"], now, rng)), reverse=True)
    formats = list(settings.get("content.formats", ["ranking"]))
    for genre in genres:
        tried: set[str] = set()
        while len(tried) < len(formats):
            fmt = sample_arm(db, "format", [f for f in formats if f not in tried], rng)
            tried.add(fmt)
            n = int(settings.get("content.products_per_post", 5)) if (fmt == "ranking" and kind == "carousel") else 3
            products, signal = _select_products(settings, db, fmt, genre["key"], n)
            if len(products) < FORMAT_MIN_PRODUCTS[fmt]:
                continue
            products = score_products(products)
            week = now.strftime("%G-W%V")
            codes = ",".join(sorted(p["item_code"] for p in products))
            h = hashlib.sha1(f"{kind}|{fmt}|{genre['key']}|{week}|{codes}".encode()).hexdigest()
            if db.hash_exists(h):
                continue
            hook = sample_arm(db, "hook", list(settings.get("content.hook_types", ["number"])), rng)
            theme = sample_arm(db, "theme", list(settings.get("content.themes", ["milk"])), rng)
            season = season_for(settings, genre["key"], now.date())
            plan = {
                "kind": kind,
                "format": fmt,
                "genre_key": genre["key"],
                "genre_label": genre["label"],
                "hook_type": hook,
                "theme": theme,
                "date": now.date().isoformat(),
                "date_label": f"{now.month}月{now.day}日",
                "season": season["phrase"] if season else None,
                "signal": {"kind": signal["kind"], "detail": signal["detail"]} if signal else None,
                "products": products,
                "picks": _picks(products),
                "tips": genre.get("tips", [])[:4] if fmt == "guide" else [],
                "genre_hashtags": genre.get("hashtags", []),
                "group": genre.get("group", "beauty"),
                "stock_queries": genre.get("stock_queries", []),
            }
            post = db.create_post(kind=kind, fmt=fmt, genre_key=genre["key"], hook_type=hook, theme=theme,
                                  content_hash=h, plan=plan, product_ids=[p["id"] for p in products])
            if signal:
                db.exec("UPDATE signals SET used=1 WHERE id=?", (signal["id"],))
            return post
    raise NoCandidate("企画できる候補がありません（商品データ不足 or 今週分を作り切った）")

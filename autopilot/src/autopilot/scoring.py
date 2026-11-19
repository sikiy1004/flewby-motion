"""比較用の指標（データスコア・◎○△）を実データだけから計算する。LLM には作らせない。

データスコア（当アカウント独自指標・100点満点）
  = 評価 40% ＋ 口コミの多さ 30% ＋ 価格の手頃さ 20% ＋ 機能の多さ 10%
  ※ いずれも「その投稿で比較した商品の中での相対値」を含むため、投稿ごとの比較用。
"""
from __future__ import annotations

import math
from typing import Any

AXES = [("value", "価格"), ("rating", "評価"), ("popular", "口コミ数"), ("features", "機能")]


def _minmax(vals: list[float]) -> list[float]:
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return [0.7 for _ in vals]
    return [(v - lo) / (hi - lo) for v in vals]


def score_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not products:
        return products
    prices = [float(p.get("price") or 0) for p in products]
    avgs = [float(p.get("review_avg") or 0) for p in products]
    counts = [math.log10(float(p.get("review_count") or 0) + 10) for p in products]
    feats = [min(1.0, len(p.get("features") or []) / 4) for p in products]
    value_rel = [1 - v for v in _minmax(prices)]
    rating_abs = [max(0.0, min(1.0, (a - 3.5) / 1.5)) for a in avgs]
    rating = [0.5 * a + 0.5 * r for a, r in zip(rating_abs, _minmax(avgs))]
    popular = [0.5 * c / max(counts) + 0.5 * r for c, r in zip(counts, _minmax(counts))]
    value = [0.6 * v + 0.4 * (1 - min(1.0, p / 60000)) for v, p in zip(value_rel, prices)]
    out = []
    for i, p in enumerate(products):
        axes = {"value": value[i], "rating": rating[i], "popular": popular[i], "features": feats[i]}
        score = 100 * (0.4 * axes["rating"] + 0.3 * axes["popular"] + 0.2 * axes["value"] + 0.1 * axes["features"])
        out.append({**p, "axes": {k: round(v, 3) for k, v in axes.items()}, "score": int(round(40 + 0.6 * score))})
    # ◎○△（比較した中での順位）
    n = len(out)
    for key, _ in AXES:
        order = sorted(range(n), key=lambda i: out[i]["axes"][key], reverse=True)
        for rank, i in enumerate(order):
            frac = rank / max(1, n - 1)
            mark = "◎" if frac < 0.34 else ("○" if frac < 0.67 else "△")
            if key == "features" and out[i]["axes"][key] == out[order[0]]["axes"][key]:
                mark = "◎"
            out[i].setdefault("marks", {})[key] = mark
    best = max(range(n), key=lambda i: out[i]["score"])
    out[best]["best"] = True
    return out

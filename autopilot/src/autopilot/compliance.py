"""コンプライアンス検査（ステマ規制の PR 表記・薬機法/景表法 NG 表現・数値の捏造・使い回し）。

ここを通らない生成物は投稿されない。
"""
from __future__ import annotations

import difflib
import re
from typing import Any, Iterable

from .config import Settings
from .llm.schema import Copy

_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _allowed_numbers(plan: dict[str, Any]) -> set[str]:
    allowed: set[str] = {str(i) for i in range(0, 11)}
    for p in plan.get("products", []):
        for k in ("price", "review_count", "rank", "score"):
            v = p.get(k)
            if v is not None:
                allowed.add(str(int(v)))
        if p.get("price"):
            man, rest = divmod(int(p["price"]), 10000)
            allowed.update({str(man), str(rest)})
        avg = p.get("review_avg")
        if avg:
            allowed.update({f"{avg:.2f}", f"{avg:.1f}", str(avg)})
        for f in p.get("features", []):
            allowed.update(m.replace(",", "") for m in _NUM.findall(f))
        for m in _NUM.findall(p.get("name", "")):
            allowed.add(m.replace(",", ""))
    for t in plan.get("tips", []):
        allowed.update(m.replace(",", "") for m in _NUM.findall(t.get("title", "") + t.get("body", "")))
    sig = plan.get("signal") or {}
    allowed.update(m.replace(",", "") for m in _NUM.findall(sig.get("detail", "")))
    allowed.update({"10000", "25000", "5000", "2.5"})  # 価格帯の区切り（1万円・2万5000円）
    d = plan.get("date", "")
    allowed.update(x.lstrip("0") for x in d.split("-") if x)
    return allowed


def ng_violations(settings: Settings, texts: Iterable[str]) -> list[str]:
    out = []
    joined = "\n".join(texts)
    for pat in settings.ng.get("patterns", []):
        m = re.search(pat["re"], joined, flags=re.IGNORECASE)
        if m:
            out.append(f"NG表現「{m.group(0)}」: {pat['reason']}")
    return out


def number_violations(plan: dict[str, Any], texts: Iterable[str]) -> list[str]:
    allowed = _allowed_numbers(plan)
    out = []
    for t in texts:
        for m in _NUM.findall(t):
            v = m.replace(",", "")
            if v in allowed:
                continue
            try:
                if float(v) <= 10:
                    continue
            except ValueError:
                pass
            out.append(f"データに無い数値「{m}」")
    return out


def similarity_violation(caption: str, recent: list[str], threshold: float) -> str | None:
    for old in recent:
        if old and difflib.SequenceMatcher(None, caption, old).ratio() >= threshold:
            return "過去の投稿とキャプションが似すぎています"
    return None


def check_copy(settings: Settings, plan: dict[str, Any], copy: Copy, recent_captions: list[str]) -> list[str]:
    texts = [copy.hook, copy.subtitle, copy.summary, copy.narration_hook, copy.narration_outro,
             copy.caption_body, copy.caption_tiktok, *copy.product_notes.values(), *copy.narration_products.values()]
    problems = ng_violations(settings, texts)
    problems += number_violations(plan, texts)
    codes = {p["item_code"] for p in plan["products"]}
    if not codes.issubset(copy.narration_products.keys()):
        problems.append("narration_products に不足があります")
    sim = similarity_violation(copy.caption_body, recent_captions, float(settings.get("content.similarity_threshold", 0.85)))
    if sim:
        problems.append(sim)
    return problems


def check_final_caption(settings: Settings, caption: str) -> list[str]:
    prefix = settings.ng.get("required", {}).get("caption_prefix", "PR")
    problems = []
    if not caption.lstrip().startswith(prefix):
        problems.append(f"キャプション冒頭に「{prefix}」表記がありません（ステマ規制）")
    if len(caption) > 2200:
        problems.append("キャプションが2,200字を超えています")
    if caption.count("#") > 30:
        problems.append("ハッシュタグが30個を超えています")
    return problems

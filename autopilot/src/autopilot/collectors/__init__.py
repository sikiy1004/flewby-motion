"""ネタ・商品データ収集。"""
from __future__ import annotations

import re
import urllib.parse
from typing import Any

_BRACKETS = re.compile(r"[【\[［〔（(<＜《].*?[】\]］〕）)>＞》]")
_NOISE = re.compile(
    r"送料無料|ポイント\s*\d+\s*倍|P\d+倍|楽天\s*\d+\s*位|ランキング\s*\d+\s*位|\d+冠|"
    r"あす楽|即納|正規品|国内正規品|クーポン.*?OFF|\d+%\s*OFF|最大\s*\d+|公式|新品|"
    r"母の日|父の日|プレゼント|ギフト|クリスマス|ラッピング|メーカー保証|日本製"
)


def clean_name(name: str, max_len: int = 26) -> str:
    """楽天の長い商品名から、表示用の短い名前を作る（LLM 不使用・決定論）。"""
    s = _BRACKETS.sub(" ", name)
    s = _NOISE.sub(" ", s)
    s = re.sub(r"[★☆◆◇■□●○♪！!※＊*｜|/／]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" 　-・,、")
    if not s:
        s = name
    words = s.split(" ")
    out = ""
    for w in words:
        cand = (out + " " + w).strip()
        if len(cand) > max_len:
            break
        out = cand
    return out or s[:max_len]


def extract_features(text: str, features: dict[str, str], limit: int = 4) -> list[str]:
    found: list[str] = []
    for kw, label in features.items():
        if kw.lower() in text.lower() and label not in found:
            found.append(label)
        if len(found) >= limit:
            break
    return found


def amazon_search_url(query: str, tag: str | None) -> str | None:
    if not tag:
        return None
    q = urllib.parse.quote_plus(query)
    return f"https://www.amazon.co.jp/s?k={q}&tag={urllib.parse.quote(tag)}"


def is_excluded(name: str, genre: dict[str, Any]) -> bool:
    return any(x in name for x in genre.get("exclude", []))

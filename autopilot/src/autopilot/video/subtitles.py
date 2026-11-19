"""ナレーションを字幕（1行ずつ）＋単語（文節）単位のタイミングに分割する。

VOICEVOX の節タイミングがあればそれに合わせ、無ければ文字数で按分する。
"""
from __future__ import annotations

import re
from typing import Any

try:
    import budoux
    _parser = budoux.load_default_japanese_parser()
except Exception:  # pragma: no cover
    _parser = None

MAX_CHARS = 14
_EM = re.compile(r"\d|位|円|比較|保存|コスパ|プロフ|おすすめ|特徴")
_CLAUSE = re.compile(r"(?<=[、。！？!?])")


def phrases(text: str) -> list[str]:
    return _parser.parse(text) if _parser else list(text)


def clauses(text: str) -> list[str]:
    return [c for c in _CLAUSE.split(text.strip()) if c.strip("。、！？!? ")]


def split_caption(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """表示用の 1 行（max_chars 前後）に分割。句読点は表示しない。"""
    out: list[str] = []
    for clause in clauses(text):
        cur = ""
        for ph in phrases(clause):
            if len(cur) + len(ph) > max_chars and cur:
                out.append(cur)
                cur = ph
            else:
                cur += ph
        if cur:
            out.append(cur)
    hard: list[str] = []
    for c in out:
        while len(c) > max_chars + 3:
            cut = c.rfind(" ", 0, max_chars + 1)
            cut = cut if cut > 3 else max_chars
            hard.append(c[:cut].strip())
            c = c[cut:].strip()
        hard.append(c)
    return [c.strip("。、！？ ") for c in hard if c.strip("。、！？ ")]


def build_captions(text: str, offset: float, duration: float,
                   timings: list[tuple[float, float]] | None) -> list[dict[str, Any]]:
    """1 シーン分の字幕。offset=音声の開始時刻（動画内の秒）。"""
    cls = clauses(text)
    if not timings or len(timings) != len(cls):
        total = sum(len(c) for c in cls) or 1
        t, timings = 0.05, []
        usable = max(0.5, duration - 0.15)
        for c in cls:
            d = usable * len(c) / total
            timings.append((t, t + d))
            t += d
    caps: list[dict[str, Any]] = []
    for clause, (cs, ce) in zip(cls, timings):
        lines = split_caption(clause)
        n_chars = sum(len(x) for x in lines) or 1
        t = cs
        for line in lines:
            ld = (ce - cs) * len(line) / n_chars
            words, wt = [], t
            for w in phrases(line):
                wd = ld * len(w) / max(1, len(line))
                words.append({"text": w, "start": round(offset + wt, 3), "end": round(offset + wt + wd, 3),
                              "em": bool(_EM.search(w))})
                wt += wd
            caps.append({"start": round(offset + t, 3), "end": round(offset + t + ld, 3), "words": words})
            t += ld
    # 行と行の隙間を埋めて字幕のチラつきを防ぐ
    for a, b in zip(caps, caps[1:]):
        if 0 < b["start"] - a["end"] < 0.45:
            a["end"] = b["start"]
    return caps

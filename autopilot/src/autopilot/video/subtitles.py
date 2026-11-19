"""ナレーションを短い字幕に分割し、ASS ファイルを書き出す（libass で焼き込み）。"""
from __future__ import annotations

import re
from pathlib import Path

try:
    import budoux
    _parser = budoux.load_default_japanese_parser()
except Exception:  # pragma: no cover
    _parser = None

MAX_CHARS = 15


def split_caption(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    sentences = [s for s in re.split(r"(?<=[。！？!?、])", text.strip()) if s.strip()]
    out: list[str] = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) <= max_chars:
            out.append(sent)
            continue
        phrases = _parser.parse(sent) if _parser else list(sent)
        cur = ""
        for ph in phrases:
            if len(cur) + len(ph) > max_chars and cur:
                out.append(cur)
                cur = ph
            else:
                cur += ph
        if cur:
            out.append(cur)
    # まだ長すぎる断片は、空白位置（なければ文字数）で強制的に分ける
    hard: list[str] = []
    for c in out:
        while len(c) > max_chars + 2:
            cut = c.rfind(" ", 0, max_chars + 1)
            cut = cut if cut > 3 else max_chars
            hard.append(c[:cut].strip())
            c = c[cut:].strip()
        hard.append(c)
    out = hard
    # 句読点だけの断片を前に結合し、末尾の「。」「、」は表示しない
    merged: list[str] = []
    for c in out:
        c = c.rstrip("。、")
        if not c:
            continue
        if merged and len(c) <= 2:
            merged[-1] += c
        else:
            merged.append(c)
    return merged


def _ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(path: Path, cues: list[tuple[float, float, str]], *, width: int, height: int, font: str = "Noto Sans JP",
              margin_v: int = 450) -> Path:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},66,&H00FFFFFF,&H00FFFFFF,&H261E1A16,&H00000000,-1,0,0,0,100,100,1,0,3,20,0,2,80,160,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for start, end, text in cues:
        safe = text.replace("{", "（").replace("}", "）").replace("\n", " ")
        lines.append(f"Dialogue: 0,{_ts(start)},{_ts(end)},Sub,,0,0,0,,{{\\fad(80,60)}}{safe}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return path


def cues_for(text: str, start: float, duration: float) -> list[tuple[float, float, str]]:
    chunks = split_caption(text)
    total = sum(len(c) for c in chunks) or 1
    t = start
    cues = []
    for c in chunks:
        d = duration * len(c) / total
        cues.append((t, t + d - 0.02, c))
        t += d
    return cues

"""縦型ショート動画（1080×1920 / 30fps / H.264 + AAC）の自動生成。

演出は Remotion（React）テンプレート `autopilot/remotion` で行う:
  フック（文字ポップ＋マーカー＋保存版スタンプ）→ 商品（スライドイン・価格カウントアップ・◎○△・スコアリング）
  → 結論 → 保存CTA。上部に進行バー、下部に文節ごとに色が変わる字幕、シーン間はワイプ＋効果音。
Python 側は 台本 → 音声（VOICEVOX）→ 字幕タイミング → props.json を作り、Remotion で書き出し、
最後に FFmpeg で音量を正規化（-14 LUFS）する。
"""
from __future__ import annotations

import json
import logging
import os
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..config import Settings
from ..llm.schema import Copy
from ..render import FORMAT_LABEL
from ..render.carousel import product_labels
from ..render.illustrations import icon, illustration
from .stock import fetch_background_video
from .subtitles import build_captions, phrases
from .tts import get_tts, probe_duration

log = logging.getLogger(__name__)

REMOTION_DIR = Path(__file__).resolve().parents[3] / "remotion"
_EMPH = ("比較", "後悔", "選び方", "どれ", "盲点", "予算", "TOP", "注目")


def _hook_chunks(hook: str) -> list[dict[str, Any]]:
    out, done = [], False
    for c in phrases(hook):
        em = not done and (any(k in c for k in _EMPH) or any(ch.isdigit() for ch in c))
        done = done or em
        out.append({"text": c, "em": em})
    return out


def _big_number(plan: dict[str, Any]) -> tuple[str, str]:
    return {
        "ranking": (str(min(3, len(plan["products"]))), "機種を<br>データで比較"),
        "price_band": ("3", "つの価格帯で<br>選んでみた"),
        "spotlight": ("1", "台を深掘り"),
        "guide": (str(len(plan["tips"]) or 4), "つの<br>チェックポイント"),
    }[plan["format"]]


def build_scenes(plan: dict[str, Any], copy: Copy) -> list[dict[str, Any]]:
    fmt = plan["format"]
    big_n, big_label = _big_number(plan)
    scenes: list[dict[str, Any]] = [{
        "type": "hook", "hookChunks": _hook_chunks(copy.hook), "subtitle": copy.subtitle, "bigN": big_n,
        "bigLabel": big_label, "narration": copy.narration_hook, "min": 3.0,
    }]
    if fmt == "guide":
        annos = ["ここ大事！", "見落としがち", "要チェック", "比べてみて"]
        for n, t in enumerate(plan["tips"], 1):
            body = t["body"].split("。")[0] + "。"
            scenes.append({"type": "tip", "n": n, "title": t["title"], "body": body, "anno": annos[(n - 1) % 4],
                           "narration": f"ポイント{n}、{t['title']}。{body}", "min": 3.2})
    else:
        prods = plan["products"][:3]
        if fmt == "ranking":  # カウントダウン（3位 → 1位）で最後まで見たくなる構成に
            prods = sorted(prods, key=lambda p: -(p.get("rank") or 0))
        for i, p in enumerate(prods):
            idx = plan["products"].index(p)
            big, suffix, chip, _ = product_labels(fmt, idx, p)
            prod = {k: p[k] for k in ("name", "price", "review_avg", "review_count", "features", "score", "axes", "marks")}
            prod.update({"best": bool(p.get("best")), "label_main": big, "label_suffix": suffix, "label_chip": chip})
            scenes.append({"type": "product", "product": prod, "index": i, "total": len(prods),
                           "narration": copy.narration_products.get(p["item_code"], p["name"]), "min": 3.4})
        icons = {"価格重視なら": icon("yen", 80), "評価重視なら": icon("star", 80), "定番を選ぶなら": icon("people", 80)}
        picks = [{**k, "icon": icons.get(k["label"], icon("check", 80))} for k in plan["picks"][:3]]
        scenes.append({"type": "picks", "picks": picks,
                       "narration": "、".join(f"{k['label']}{k['name']}" for k in picks[:2]) + "がおすすめ。", "min": 3.0})
    scenes.append({"type": "cta", "narration": copy.narration_outro, "min": 2.6})
    return scenes


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd[:4])} ...\n{(proc.stderr or proc.stdout)[-3000:]}")


def _bgm(settings: Settings, work: Path, seconds: float, rng: random.Random) -> Path:
    bgm_dir = settings.assets_dir / "bgm"
    files = sorted([*bgm_dir.glob("*.mp3"), *bgm_dir.glob("*.wav"), *bgm_dir.glob("*.m4a")])
    if files:
        return rng.choice(files)
    # 素材が無い場合：テンポのある Lo-fi 風ループを生成（キック＋ハイハット＋コード。権利フリー）
    chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
    pad = "+".join(
        f"between(mod(t,8),{2 * k},{2 * k + 1.999})*(sin(2*PI*{a}*t)+0.8*sin(2*PI*{b}*t)+0.7*sin(2*PI*{c}*t)+0.5*sin(2*PI*{a / 2}*t))"
        for k, (a, b, c) in enumerate(chords))
    beat = 0.5  # 120 BPM
    kick = f"0.9*sin(2*PI*(55+80*exp(-mod(t,{beat})*30))*mod(t,{beat}))*exp(-mod(t,{beat})*9)"
    hat = f"0.12*(random(0)*2-1)*exp(-mod(t+{beat / 2},{beat})*60)"
    expr = f"0.07*({pad})*(0.75+0.25*cos(2*PI*mod(t,{beat})/{beat}))+0.35*{kick}+{hat}"
    out = work / "bgm.wav"
    _run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={seconds + 2:.2f}",
          "-af", "lowpass=f=5000,highpass=f=35,aecho=0.8:0.6:180:0.18,volume=0.9", "-ac", "2", str(out)])
    return out


def _ensure_node_modules() -> None:
    if (REMOTION_DIR / "node_modules" / "remotion").exists():
        return
    _run(["npm", "ci", "--no-audit", "--no-fund"], cwd=REMOTION_DIR)


def render_video(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path,
                 rng: random.Random | None = None) -> dict[str, Any]:
    rng = rng or random.Random(post_no)
    work = out_dir / "_video"
    if work.exists():
        shutil.rmtree(work)
    public = work / "public"
    public.mkdir(parents=True)
    fps = int(settings.get("video.fps", 30))
    scenes = build_scenes(plan, copy)

    # 1) 音声（長すぎたら話速を上げて作り直す。最大 1.4 倍）
    tts, voice = get_tts(settings)
    max_s = float(settings.get("video.max_seconds", 45))
    for _round in range(2):
        for i, sc in enumerate(scenes):
            wav = public / f"voice_{i:02d}.wav"
            sc["timings"] = tts.synth(sc["narration"], wav)
            sc["voice"] = wav.name
            sc["voice_dur"] = probe_duration(wav)
            sc["voiceStart"] = 0.35 if i == 0 else 0.2
            sc["duration"] = round(max(sc["min"], sc["voiceStart"] + sc["voice_dur"] + 0.35), 3)
        est = sum(s["duration"] for s in scenes)
        speed = getattr(tts, "speed", None)
        if est <= max_s or speed is None or speed >= 1.4:
            break
        tts.speed = min(1.4, speed * est / (max_s - 1))
        log.info("動画が %.1f 秒になるため話速を %.2f に上げて再生成します", est, tts.speed)

    # 2) タイムライン・字幕
    t = 0.0
    captions: list[dict[str, Any]] = []
    for sc in scenes:
        sc["start"] = round(t, 3)
        captions += build_captions(sc["narration"], t + sc["voiceStart"], sc["voice_dur"], sc.pop("timings", None))
        t += sc["duration"]
    total = t
    frames = int(round(total * fps))

    # 3) 素材を public へ
    os.symlink(settings.assets_dir.joinpath("webfonts").resolve(), public / "webfonts")
    shutil.copyfile(settings.assets_dir / "design" / "design.css", public / "design.css")
    for name in ("slide", "impact", "pop", "line"):
        shutil.copyfile(settings.assets_dir / "sfx" / f"{name}.wav", public / f"sfx_{name}.wav")
    bgm = _bgm(settings, work, total, rng)
    shutil.copyfile(bgm, public / f"bgm{bgm.suffix}")
    bg_video = fetch_background_video(settings, plan, work)
    if bg_video:
        shutil.move(str(bg_video), public / "stock.mp4")

    glyph_src = [copy.hook, copy.subtitle, plan["genre_label"], FORMAT_LABEL[plan["format"]],
                 "保存版比較プロフから見てね商品リンクはプロフィールのリンク結論タイプ別なら価格評価口コミ機能円件位音声",
                 json.dumps(scenes, ensure_ascii=False), json.dumps(captions, ensure_ascii=False), voice.credit or ""]
    glyphs = "".join(sorted(set("".join(glyph_src))))
    props = {
        "fps": fps, "width": 1080, "height": 1920, "durationInFrames": frames,
        "theme": plan["theme"], "postNo": post_no, "genre": plan["genre_label"],
        "formatLabel": FORMAT_LABEL[plan["format"]], "dateLabel": plan["date_label"],
        "illust": illustration(plan["genre_key"], 330),
        "icons": {"yen": icon("yen", 54), "star": icon("star", 54), "people": icon("people", 54), "spark": icon("spark", 54),
                  "bookmark_big": icon("bookmark", 230)},
        "scenes": [{k: v for k, v in s.items() if k not in ("narration", "min", "voice_dur")} for s in scenes],
        "captions": captions,
        "bgm": f"bgm{bgm.suffix}", "bgmVolume": float(settings.get("video.bgm_volume", 0.18)) * 1.4,
        "sfx": {"whoosh": "sfx_slide.wav", "impact": "sfx_impact.wav", "pop": "sfx_pop.wav", "line": "sfx_line.wav"},
        "bgVideo": "stock.mp4" if bg_video else None,
        "credit": voice.credit,
        "glyphs": glyphs,
    }
    props_path = work / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    # 4) Remotion で書き出し
    _ensure_node_modules()
    raw = work / "raw.mp4"
    conc = settings.env("REMOTION_CONCURRENCY", str(max(1, min(4, os.cpu_count() or 2))))
    cmd = ["npx", "remotion", "render", "src/index.ts", "Reel", str(raw), f"--props={props_path}",
           f"--public-dir={public}", "--log=error", "--codec=h264", "--crf=19", f"--concurrency={conc}"]
    exe = os.environ.get("CHROMIUM_EXECUTABLE")
    if exe:
        cmd.append(f"--browser-executable={exe}")
    _run(cmd, cwd=REMOTION_DIR)

    # 5) 音量正規化・faststart
    out = out_dir / "reel.mp4"
    _run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c:v", "copy",
          "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100", "-c:a", "aac", "-b:a", "128k",
          "-movflags", "+faststart", str(out)])
    cover = out_dir / "reel_cover.jpg"
    _run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(1.3, scenes[0]['duration'] - 0.2):.2f}", "-i", str(out),
          "-frames:v", "1", "-q:v", "2", str(cover)])
    if total > 90:
        raise RuntimeError(f"動画が長すぎます（{total:.1f}秒）")
    if total > max_s:
        log.warning("動画尺 %.1f 秒が推奨上限 %.0f 秒を超えています", total, max_s)
    return {"video": out, "cover": cover, "seconds": round(total, 2), "voice": voice.engine, "credit": voice.credit,
            "scenes": len(scenes)}

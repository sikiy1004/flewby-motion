"""縦型ショート動画（1080×1920 / 30fps / H.264 + AAC）の自動生成。

流れ: シーン画像(Playwright) → 音声(VOICEVOX) → シーンごとのクリップ(Ken Burns + 前景フェード)
     → xfade で結合 → 字幕(ASS)焼き込み → ナレーション + BGM(ダッキング) + 効果音 → loudnorm
"""
from __future__ import annotations

import logging
import random
import subprocess
from pathlib import Path
from typing import Any

from ..config import Settings
from ..llm.schema import Copy
from ..render import base_css, phrase_html, render_template, screenshot_sections
from ..render.carousel import product_labels
from .stock import fetch_background_video
from .subtitles import cues_for, write_ass
from .tts import get_tts, probe_duration

log = logging.getLogger(__name__)

TRANSITIONS = ["smoothleft", "fade", "smoothup", "fadeblack"]


def build_scenes(plan: dict[str, Any], copy: Copy) -> list[dict[str, Any]]:
    fmt = plan["format"]
    scenes: list[dict[str, Any]] = [{
        "type": "hook", "hook_html": phrase_html(copy.hook), "subtitle": copy.subtitle,
        "narration": copy.narration_hook,
    }]
    if fmt == "guide":
        for n, t in enumerate(plan["tips"], 1):
            body = t["body"].split("。")[0] + "。"
            scenes.append({"type": "tip", "n": n, "title": t["title"], "body": body, "narration": f"ポイント{n}、{t['title']}。{body}"})
    else:
        for i, p in enumerate(plan["products"][:3]):
            big, suffix, _, _ = product_labels(fmt, i, p)
            scenes.append({"type": "product", "product": p, "label_main": big, "label_suffix": suffix,
                           "narration": copy.narration_products.get(p["item_code"], p["name"])})
        picks = plan["picks"][:2]
        scenes.append({"type": "picks", "picks": picks,
                       "narration": "、".join(f"{k['label']}{k['name']}" for k in picks) + "がおすすめ。"})
    scenes.append({"type": "cta", "narration": copy.narration_outro})
    return scenes


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(cmd[:6])} ...\n{proc.stderr[-2000:]}")


def _bgm(settings: Settings, work: Path, seconds: float, rng: random.Random) -> Path:
    files = sorted([*settings.assets_dir.joinpath("bgm").glob("*.mp3"), *settings.assets_dir.joinpath("bgm").glob("*.wav"),
                    *settings.assets_dir.joinpath("bgm").glob("*.m4a")])
    if files:
        return rng.choice(files)
    # 素材が無い場合：やわらかいコード進行のパッドを生成（権利フリー）
    chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
    terms = []
    for k, (a, b, c) in enumerate(chords):
        terms.append(f"between(mod(t,16),{4 * k},{4 * k + 3.999})*(sin(2*PI*{a}*t)+0.8*sin(2*PI*{b}*t)+0.7*sin(2*PI*{c}*t)"
                     f"+0.3*sin(2*PI*{a / 2}*t))")
    expr = f"0.09*(0.55-0.45*cos(2*PI*mod(t,4)/4))*({'+'.join(terms)})"
    out = work / "bgm_pad.wav"
    _run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={seconds + 2:.2f}",
          "-af", "lowpass=f=1400,aecho=0.8:0.7:120:0.25,afade=t=in:d=1.5", "-ac", "2", str(out)])
    return out


def render_video(settings: Settings, plan: dict[str, Any], copy: Copy, post_no: int, out_dir: Path,
                 rng: random.Random | None = None) -> dict[str, Any]:
    rng = rng or random.Random(post_no)
    work = out_dir / "_video"
    work.mkdir(parents=True, exist_ok=True)
    W, H = int(settings.get("video.width", 1080)), int(settings.get("video.height", 1920))
    fps = int(settings.get("video.fps", 30))
    T = float(settings.get("video.transition_seconds", 0.3))
    scenes = build_scenes(plan, copy)

    # 1) 音声（長すぎたら話速を上げて作り直す。最大 1.4 倍まで）
    tts, voice = get_tts(settings)
    max_s = float(settings.get("video.max_seconds", 45))
    for _round in range(2):
        durations: list[float] = []
        wavs: list[Path] = []
        for i, sc in enumerate(scenes):
            wav = work / f"voice_{i:02d}.wav"
            tts.synth(sc["narration"], wav)
            wavs.append(wav)
            vd = probe_duration(wav)
            sc["voice_dur"] = vd
            lead = 0.25 if i == 0 else 0.15
            sc["lead"] = lead
            durations.append(max(2.2, vd + lead + 0.45))
        est = sum(durations) - T * (len(durations) - 1)
        speed = getattr(tts, "speed", None)
        if est <= max_s or speed is None or speed >= 1.4:
            break
        tts.speed = min(1.4, speed * est / (max_s - 1))
        log.info("動画が %.1f 秒になるため話速を %.2f に上げて再生成します", est, tts.speed)

    # 2) シーン画像
    credit = f"音声: {voice.credit}" if voice.credit else ""
    html_text = render_template("video.html.j2", base_css=base_css(settings.fonts_dir), theme=plan["theme"],
                                scenes=scenes, post_no=post_no, genre=plan["genre_label"], credit=credit)
    targets = [("#bg", work / "bg.png")] + [(f"#scene-{i}", work / f"fg_{i:02d}.png") for i in range(len(scenes))]
    screenshot_sections(html_text, work, targets, width=W, height=H, transparent=True)

    bg_video = fetch_background_video(settings, plan, work)

    # 3) シーンごとのクリップ（Ken Burns + 前景フェードイン）
    clips: list[Path] = []
    for i, d in enumerate(durations):
        clip = work / f"clip_{i:02d}.mp4"
        zoom_in = i % 2 == 0
        z = "min(1+0.0009*on,1.08)" if zoom_in else "max(1.08-0.0009*on,1.0)"
        if i == 0 and bg_video:
            bg_in = ["-stream_loop", "-1", "-t", f"{d:.3f}", "-i", str(bg_video)]
            bg_f = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},"
                    f"eq=brightness=-0.05:saturation=0.85,boxblur=6:1,setsar=1[b]")
        else:
            bg_in = ["-loop", "1", "-framerate", str(fps), "-t", f"{d:.3f}", "-i", str(work / "bg.png")]
            bg_f = (f"[0:v]scale={int(W * 1.5)}:-2,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                    f":d=1:s={W}x{H}:fps={fps},setsar=1[b]")
        _run(["ffmpeg", "-v", "error", "-y", *bg_in,
              "-loop", "1", "-framerate", str(fps), "-t", f"{d:.3f}", "-i", str(work / f"fg_{i:02d}.png"),
              "-filter_complex", f"{bg_f};[1:v]format=rgba,fade=t=in:st=0:d=0.35:alpha=1[f];"
                                 f"[b][f]overlay=0:0:format=auto,format=yuv420p[v]",
              "-map", "[v]", "-t", f"{d:.3f}", "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
              str(clip)])
        clips.append(clip)

    # 4) タイムライン
    starts = [0.0]
    for i in range(1, len(durations)):
        starts.append(starts[-1] + durations[i - 1] - T)
    total = starts[-1] + durations[-1]

    cues = []
    for sc, st in zip(scenes, starts):
        cues += cues_for(sc["narration"], st + sc["lead"], sc["voice_dur"])
    ass = write_ass(work / "subs.ass", cues, width=W, height=H)

    bgm = _bgm(settings, work, total, rng)
    sfx_dir = settings.assets_dir / "sfx"
    whoosh, impact = sfx_dir / "slide.wav", sfx_dir / "impact.wav"

    n = len(clips)
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]
    for w in wavs:
        inputs += ["-i", str(w)]
    inputs += ["-stream_loop", "-1", "-i", str(bgm), "-i", str(impact), "-i", str(whoosh)]
    i_bgm, i_imp, i_wh = 2 * n, 2 * n + 1, 2 * n + 2

    f: list[str] = []
    last = "0:v"
    for k in range(1, n):
        tr = TRANSITIONS[(k - 1) % len(TRANSITIONS)]
        f.append(f"[{last}][{k}:v]xfade=transition={tr}:duration={T}:offset={starts[k]:.3f}[x{k}]")
        last = f"x{k}"
    fonts = str(settings.fonts_dir.resolve()).replace(":", r"\:")
    f.append(f"[{last}]ass={str(ass.resolve())}:fontsdir={fonts},format=yuv420p[vout]")
    for k in range(n):
        ms = int((starts[k] + scenes[k]["lead"]) * 1000)
        f.append(f"[{n + k}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{k}]")
    f.append("".join(f"[a{k}]" for k in range(n)) + f"amix=inputs={n}:normalize=0,apad[voice]")
    f.append("[voice]asplit=2[vo1][vo2]")
    vol = float(settings.get("video.bgm_volume", 0.18))
    f.append(f"[{i_bgm}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},"
             f"afade=t=out:st={max(0, total - 1.2):.2f}:d=1.2[bgm]")
    f.append("[bgm][vo2]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[duck]")
    trans = [f"[{i_wh}:a]asplit={max(1, n - 1)}" + "".join(f"[w{k}]" for k in range(max(1, n - 1)))]
    for k in range(1, n):
        ms = int(max(0, starts[k] - 0.1) * 1000)
        trans.append(f"[w{k - 1}]volume=0.35,adelay={ms}|{ms}[wd{k}]")
    f += trans
    f.append(f"[{i_imp}:a]volume=0.45[imp]")
    sfx_labels = "[imp]" + "".join(f"[wd{k}]" for k in range(1, n))
    f.append(f"{sfx_labels}amix=inputs={n}:normalize=0[sfx]")
    f.append("[vo1][duck][sfx]amix=inputs=3:normalize=0,"
             f"atrim=0:{total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[aout]")

    out = out_dir / "reel.mp4"
    _run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f),
          "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
          "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
          "-r", str(fps), "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", str(out)])

    cover = out_dir / "reel_cover.jpg"
    _run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(1.0, durations[0] - 0.1):.2f}", "-i", str(out),
          "-frames:v", "1", "-q:v", "2", str(cover)])
    if total > 90:
        raise RuntimeError(f"動画が長すぎます（{total:.1f}秒）")
    if total > max_s:
        log.warning("動画尺 %.1f 秒が推奨上限 %.0f 秒を超えています", total, max_s)
    return {"video": out, "cover": cover, "seconds": round(total, 2), "voice": voice.engine, "credit": voice.credit,
            "scenes": len(scenes)}

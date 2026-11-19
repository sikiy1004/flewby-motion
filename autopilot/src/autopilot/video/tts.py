"""音声合成：VOICEVOX（ローカル / Docker）→ Edge-TTS（非常用）→ 無音（--sample のみ）。"""
from __future__ import annotations

import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import requests

from ..config import Settings

log = logging.getLogger(__name__)


class TTSUnavailable(Exception):
    pass


@dataclass
class Voice:
    engine: str
    credit: str | None


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def _reading(text: str) -> str:
    """読み上げ用に記号を整える（★4.62 → 星4.62 など）。"""
    t = text.replace("★", "星").replace("→", "、").replace("｜", "、").replace("/", "、")
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)
    return t


class VoicevoxTTS:
    def __init__(self, url: str, speaker_name: str, style: str, speed: float):
        self.url = url.rstrip("/")
        self.speed = speed
        self.speaker_name = speaker_name
        self.speaker_id = self._resolve(speaker_name, style)

    def _resolve(self, name: str, style: str) -> int:
        try:
            r = requests.get(f"{self.url}/speakers", timeout=5)
            r.raise_for_status()
        except requests.RequestException as e:
            raise TTSUnavailable(f"VOICEVOX に接続できません: {e}") from e
        speakers = r.json()
        for sp in speakers:
            if sp["name"] == name:
                for st in sp["styles"]:
                    if st["name"] == style:
                        return int(st["id"])
                return int(sp["styles"][0]["id"])
        self.speaker_name = speakers[0]["name"]
        return int(speakers[0]["styles"][0]["id"])

    def synth(self, text: str, path: Path) -> list[tuple[float, float]] | None:
        q = requests.post(f"{self.url}/audio_query", params={"text": _reading(text), "speaker": self.speaker_id}, timeout=60)
        q.raise_for_status()
        query = q.json()
        query["speedScale"] = self.speed
        query["prePhonemeLength"] = 0.05
        query["postPhonemeLength"] = 0.15
        w = requests.post(f"{self.url}/synthesis", params={"speaker": self.speaker_id}, json=query, timeout=120)
        w.raise_for_status()
        path.write_bytes(w.content)
        return clause_timings(query)

    @property
    def credit(self) -> str:
        return f"VOICEVOX:{self.speaker_name}"


def clause_timings(query: dict) -> list[tuple[float, float]]:
    """VOICEVOX の audio_query から、句読点（ポーズ）で区切った節ごとの (開始, 終了) 秒を求める。字幕同期用。"""
    speed = float(query.get("speedScale", 1.0)) or 1.0
    t = float(query.get("prePhonemeLength", 0.1)) / speed
    out: list[tuple[float, float]] = []
    start = t
    phrases = query.get("accent_phrases", [])
    for i, ph in enumerate(phrases):
        for m in ph.get("moras", []):
            t += (float(m.get("consonant_length") or 0) + float(m.get("vowel_length") or 0)) / speed
        pause = ph.get("pause_mora")
        if pause or i == len(phrases) - 1:
            out.append((start, t))
            if pause:
                t += float(pause.get("vowel_length") or 0) / speed
            start = t
    return out


class EdgeTTS:
    def __init__(self, voice: str, speed: float):
        try:
            import edge_tts  # noqa: F401
        except ImportError as e:
            raise TTSUnavailable("edge-tts 未インストール") from e
        self.voice = voice
        self.speed = speed

    def synth(self, text: str, path: Path) -> None:
        import edge_tts  # noqa: F811

        mp3 = path.with_suffix(".mp3")
        rate = f"+{int(round((self.speed - 1) * 100))}%"
        asyncio.run(edge_tts.Communicate(_reading(text), self.voice, rate=rate).save(str(mp3)))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(path)], check=True)

    credit = None


class SilentTTS:
    """音声なし（字幕だけで成立させる）。本番では require_voice=true なら使われない。"""

    def synth(self, text: str, path: Path) -> None:
        dur = max(1.6, len(text) / 7.0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                        "-t", f"{dur:.2f}", str(path)], check=True)

    credit = None


def get_tts(settings: Settings) -> tuple[object, Voice]:
    speed = float(settings.get("video.speed_scale", 1.15))
    errors = []
    for engine in settings.get("tts.engine_order", ["voicevox", "edge"]):
        try:
            if engine == "voicevox":
                t = VoicevoxTTS(settings.env("VOICEVOX_URL", "http://localhost:50021"),
                                settings.get("tts.voicevox_speaker", "冥鳴ひまり"),
                                settings.get("tts.voicevox_style", "ノーマル"), speed)
                return t, Voice("voicevox", t.credit)
            if engine == "edge":
                t2 = EdgeTTS(settings.get("tts.edge_voice", "ja-JP-NanamiNeural"), speed)
                return t2, Voice("edge", None)
        except TTSUnavailable as e:
            errors.append(f"{engine}: {e}")
    if settings.sample_mode or not settings.get("video.require_voice", True):
        log.warning("音声合成エンジンが使えないため無音で生成します: %s", errors)
        return SilentTTS(), Voice("silent", None)
    raise TTSUnavailable("; ".join(errors))

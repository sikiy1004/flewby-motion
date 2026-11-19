"""TikTok Content Posting API（Direct Post / FILE_UPLOAD）。

- 審査（audit）前のアプリは「自分のみ（SELF_ONLY）」でしか投稿できない。creator_info で許可された
  プライバシー設定を確認し、希望値が使えなければ使える値に自動で切り替える。
- アクセストークンは短命（約24時間）。毎回リフレッシュトークンで更新し、新しい値を DB に暗号化保存する。
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import requests

from ..config import Settings, now_jst
from ..tokens import TokenStore

API = "https://open.tiktokapis.com/v2"
CHUNK = 10 * 1024 * 1024


class TikTokError(Exception):
    pass


class TikTokPublisher:
    def __init__(self, settings: Settings, tokens: TokenStore | None, dry_run: bool = False):
        self.settings = settings
        self.tokens = tokens
        self.dry_run = dry_run
        self.requests_log: list[dict[str, Any]] = []
        self._access: str | None = None

    def _refresh(self) -> str:
        if self.dry_run:
            return "DRY_RUN_TOKEN"
        stored = (self.tokens.get("tiktok") if self.tokens else None) or {}
        refresh = stored.get("refresh_token") or self.settings.env("TIKTOK_REFRESH_TOKEN")
        key, secret = self.settings.env("TIKTOK_CLIENT_KEY"), self.settings.env("TIKTOK_CLIENT_SECRET")
        if not (refresh and key and secret):
            raise TikTokError("TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET / TIKTOK_REFRESH_TOKEN が未設定です")
        r = requests.post(f"{API}/oauth/token/", data={
            "client_key": key, "client_secret": secret, "grant_type": "refresh_token", "refresh_token": refresh,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=30)
        data = r.json()
        if r.status_code != 200 or "access_token" not in data:
            raise TikTokError(f"token refresh failed: {data}")
        if self.tokens:
            self.tokens.put("tiktok", {"refresh_token": data.get("refresh_token", refresh),
                                       "refreshed_at": now_jst().isoformat()})
        return data["access_token"]

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if self.dry_run:
            self.requests_log.append({"path": path, "body": body})
            if path.endswith("creator_info/query/"):
                return {"data": {"privacy_level_options": ["SELF_ONLY", "PUBLIC_TO_EVERYONE"], "max_video_post_duration_sec": 600}}
            if path.endswith("status/fetch/"):
                return {"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": ["dry"]}}
            return {"data": {"publish_id": "dry_publish", "upload_url": "https://example.invalid/upload"}}
        if not self._access:
            self._access = self._refresh()
        r = requests.post(f"{API}/{path}", json=body, timeout=60, headers={
            "Authorization": f"Bearer {self._access}", "Content-Type": "application/json; charset=UTF-8"})
        data = r.json()
        err = data.get("error", {})
        if r.status_code >= 400 or (err.get("code") not in (None, "ok")):
            raise TikTokError(f"{path}: {err}")
        return data

    def publish_video(self, video: Path, caption: str) -> dict[str, Any]:
        info = self._post("post/publish/creator_info/query/", {})["data"]
        options = info.get("privacy_level_options", [])
        privacy = self.settings.get("tiktok.privacy_level", "PUBLIC_TO_EVERYONE")
        if privacy not in options:
            privacy = "SELF_ONLY" if "SELF_ONLY" in options else (options[0] if options else "SELF_ONLY")
        size = video.stat().st_size
        chunk = size if size <= CHUNK else CHUNK
        total = 1 if size <= CHUNK else math.floor(size / CHUNK)
        post_info: dict[str, Any] = {
            "title": caption[:2200],
            "privacy_level": privacy,
            "disable_comment": bool(self.settings.get("tiktok.disable_comment", False)),
            "disable_duet": False,
            "disable_stitch": False,
            # アフィリエイト＝第三者ブランドの宣伝として開示（非公開投稿では TikTok 側が許可しないので外す）
            "brand_content_toggle": bool(self.settings.get("tiktok.disclose_branded", True)) and privacy != "SELF_ONLY",
            "brand_organic_toggle": False,
        }
        if self.settings.get("tiktok.aigc_label", True):
            post_info["is_aigc"] = True
        init = self._post("post/publish/video/init/", {
            "post_info": post_info,
            "source_info": {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": total},
        })["data"]
        publish_id, upload_url = init["publish_id"], init["upload_url"]
        if not self.dry_run:
            with video.open("rb") as fh:
                for i in range(total):
                    start = i * chunk
                    end = size - 1 if i == total - 1 else start + chunk - 1
                    fh.seek(start)
                    body = fh.read(end - start + 1)
                    r = requests.put(upload_url, data=body, timeout=300, headers={
                        "Content-Type": "video/mp4", "Content-Length": str(len(body)),
                        "Content-Range": f"bytes {start}-{end}/{size}"})
                    if r.status_code not in (200, 201, 206):
                        raise TikTokError(f"upload chunk {i} failed: {r.status_code} {r.text[:200]}")
        deadline = time.time() + 600
        while time.time() < deadline:
            st = self._post("post/publish/status/fetch/", {"publish_id": publish_id})["data"]
            status = st.get("status")
            if status == "PUBLISH_COMPLETE":
                ids = st.get("publicaly_available_post_id") or []
                return {"media_id": str(ids[0]) if ids else publish_id, "container_id": publish_id,
                        "permalink": None, "privacy": privacy}
            if status == "FAILED":
                raise TikTokError(f"publish failed: {st.get('fail_reason')}")
            time.sleep(5)
        raise TikTokError("publish status timeout")

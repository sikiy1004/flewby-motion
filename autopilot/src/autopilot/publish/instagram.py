"""Instagram Graph API（Content Publishing）でカルーセル・リール・ストーリーズを投稿する。

- 既定は「Instagram ログインの Instagram API」（graph.instagram.com）。
  Facebook ページ経由で連携している場合は IG_GRAPH_HOST=graph.facebook.com にする。
- 画像は JPEG の公開 URL、動画は MP4 の公開 URL を渡す（media_host が用意）。
- dry_run では API を呼ばず、送るはずだったリクエストを記録する。
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests

from ..config import Settings, now_jst
from ..tokens import TokenStore

log = logging.getLogger(__name__)


class InstagramError(Exception):
    pass


class InstagramPublisher:
    def __init__(self, settings: Settings, tokens: TokenStore | None, dry_run: bool = False):
        self.settings = settings
        self.tokens = tokens
        self.dry_run = dry_run
        self.host = settings.env("IG_GRAPH_HOST", "graph.instagram.com")
        self.version = settings.env("IG_API_VERSION", "v24.0")
        self.user_id = settings.env("IG_USER_ID", "me")
        self.requests_log: list[dict[str, Any]] = []
        self._fake = 0

    # ---------------- low level ----------------
    @property
    def token(self) -> str:
        stored = self.tokens.get("instagram") if self.tokens else None
        tok = (stored or {}).get("access_token") or self.settings.env("IG_ACCESS_TOKEN")
        if not tok and not self.dry_run:
            raise InstagramError("IG_ACCESS_TOKEN が未設定です")
        return tok or "DRY_RUN_TOKEN"

    def _url(self, path: str) -> str:
        return f"https://{self.host}/{self.version}/{path.lstrip('/')}"

    def _call(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(params or {})
        if self.dry_run:
            self.requests_log.append({"method": method, "path": path, "params": params})
            self._fake += 1
            if path.endswith("media_publish"):
                return {"id": f"dry_media_{self._fake}"}
            if method == "GET" and "status_code" in str(params.get("fields", "")):
                return {"status_code": "FINISHED"}
            if method == "GET" and "permalink" in str(params.get("fields", "")):
                return {"permalink": f"https://www.instagram.com/p/DRYRUN{self._fake}/"}
            if path.endswith("content_publishing_limit"):
                return {"data": [{"quota_usage": 0, "config": {"quota_total": 100}}]}
            return {"id": f"dry_container_{self._fake}"}
        params["access_token"] = self.token
        for attempt in range(4):
            r = requests.request(method, self._url(path), params=params if method == "GET" else None,
                                 data=params if method == "POST" else None, timeout=60)
            if r.status_code >= 500 or r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            data = r.json() if r.content else {}
            if r.status_code >= 400 or "error" in data:
                err = data.get("error", {})
                raise InstagramError(f"{r.status_code} {err.get('type')} {err.get('code')}: {err.get('message')}")
            return data
        raise InstagramError(f"{method} {path} が連続で失敗しました（{r.status_code}）")

    def _user_id(self) -> str:
        if self.user_id != "me" or self.dry_run:
            return self.user_id
        data = self._call("GET", "me", {"fields": "user_id,username"})
        self.user_id = str(data.get("user_id") or data["id"])
        return self.user_id

    def _wait(self, container_id: str, timeout: int = 600) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            st = self._call("GET", container_id, {"fields": "status_code,status"})
            code = st.get("status_code")
            if code == "FINISHED":
                return
            if code in ("ERROR", "EXPIRED"):
                raise InstagramError(f"container {container_id} {code}: {st.get('status')}")
            time.sleep(5 if not self.dry_run else 0)
        raise InstagramError(f"container {container_id} がタイムアウトしました")

    def _publish(self, container_id: str) -> dict[str, Any]:
        self._wait(container_id)
        media = self._call("POST", f"{self._user_id()}/media_publish", {"creation_id": container_id})
        media_id = media["id"]
        try:
            link = self._call("GET", media_id, {"fields": "permalink"}).get("permalink")
        except InstagramError:
            link = None
        return {"container_id": container_id, "media_id": media_id, "permalink": link}

    # ---------------- public ----------------
    def quota_left(self) -> int:
        data = self._call("GET", f"{self._user_id()}/content_publishing_limit", {"fields": "quota_usage,config"})
        item = (data.get("data") or [{}])[0]
        total = (item.get("config") or {}).get("quota_total", 50)
        return int(total) - int(item.get("quota_usage", 0))

    def find_existing(self, marker: str) -> dict[str, Any] | None:
        """途中で落ちた場合の二重投稿防止：直近の投稿に No.xxx を含むものがあるか。"""
        if self.dry_run:
            return None
        data = self._call("GET", f"{self._user_id()}/media", {"fields": "id,caption,permalink,timestamp", "limit": 15})
        for m in data.get("data", []):
            if marker in (m.get("caption") or ""):
                return {"media_id": m["id"], "permalink": m.get("permalink"), "container_id": None}
        return None

    def publish_carousel(self, image_urls: list[str], caption: str) -> dict[str, Any]:
        uid = self._user_id()
        children = []
        for url in image_urls[:10]:
            c = self._call("POST", f"{uid}/media", {"image_url": url, "is_carousel_item": "true"})
            children.append(c["id"])
        for cid in children:
            self._wait(cid, timeout=180)
        parent = self._call("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                                     "caption": caption})
        return self._publish(parent["id"])

    def publish_reel(self, video_url: str, caption: str, cover_url: str | None = None) -> dict[str, Any]:
        params = {"media_type": "REELS", "video_url": video_url, "caption": caption, "share_to_feed": "true"}
        if cover_url:
            params["cover_url"] = cover_url
        c = self._call("POST", f"{self._user_id()}/media", params)
        return self._publish(c["id"])

    def publish_story(self, image_url: str) -> dict[str, Any]:
        c = self._call("POST", f"{self._user_id()}/media", {"media_type": "STORIES", "image_url": image_url})
        return self._publish(c["id"])

    def insights(self, media_id: str, kind: str) -> dict[str, int]:
        metrics = ["reach", "saved", "shares", "likes", "comments"]
        metrics.append("views")
        out: dict[str, int] = {}
        try:
            data = self._call("GET", f"{media_id}/insights", {"metric": ",".join(metrics)})
        except InstagramError:
            data = {"data": []}
            for m in metrics:  # 一部の指標が非対応の場合は 1 つずつ
                try:
                    data["data"] += self._call("GET", f"{media_id}/insights", {"metric": m}).get("data", [])
                except InstagramError:
                    pass
        for item in data.get("data", []):
            vals = item.get("values") or [{}]
            out[item["name"]] = int(vals[0].get("value") or item.get("total_value", {}).get("value") or 0)
        return out

    def refresh_token(self) -> bool:
        """長期トークン（約60日）を延長。24時間以上経過したトークンのみ更新可能。"""
        if self.dry_run or self.host != "graph.instagram.com":
            return False  # Facebook ログイン経由のページトークンは無期限運用が基本
        r = requests.get(f"https://{self.host}/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": self.token}, timeout=30)
        if r.status_code != 200:
            raise InstagramError(f"token refresh failed: {r.text[:200]}")
        data = r.json()
        if self.tokens:
            self.tokens.put("instagram", {"access_token": data["access_token"],
                                          "expires_in": data.get("expires_in"),
                                          "refreshed_at": now_jst().isoformat()})
        return True

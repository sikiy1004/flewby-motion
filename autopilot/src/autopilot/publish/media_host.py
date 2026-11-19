"""メディアの公開 URL 化（Instagram API は画像・動画を URL から取得する仕様のため）。

- github_pages（既定）: 公開用リポジトリ（GitHub Pages 有効）に push。リンク集ページもここに置く。
- static_dir: 任意のディレクトリにコピー（VPS の nginx / Cloudflare Tunnel 等で配信する場合）。
- local: output/public にコピーするだけ（動作確認用。URL は file://）。
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests

from ..config import Settings

log = logging.getLogger(__name__)


class MediaHostError(Exception):
    pass


class MediaHost:
    base_url: str = ""

    def sync(self, files: dict[str, Path | str], deletes: list[str] | None = None, message: str = "update") -> None:
        """files: {公開パス: ローカルファイル or 文字列コンテンツ}"""
        raise NotImplementedError

    def url(self, rel: str) -> str:
        return f"{self.base_url.rstrip('/')}/{rel.lstrip('/')}"

    def wait_available(self, urls: list[str], timeout: int = 300) -> bool:
        if not urls or not urls[0].startswith("http"):
            return True
        deadline = time.time() + timeout
        pending = list(urls)
        while pending and time.time() < deadline:
            u = pending[0]
            try:
                r = requests.head(u, timeout=15, allow_redirects=True)
                if r.status_code == 200:
                    pending.pop(0)
                    continue
            except requests.RequestException:
                pass
            time.sleep(10)
        return not pending


def _write(dst: Path, src: Path | str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(src, Path):
        shutil.copyfile(src, dst)
    else:
        dst.write_text(src, encoding="utf-8")


class DirHost(MediaHost):
    def __init__(self, root: Path, base_url: str):
        self.root = root
        self.base_url = base_url

    def sync(self, files, deletes=None, message="update"):
        for rel, src in files.items():
            _write(self.root / rel, src)
        for rel in deletes or []:
            p = self.root / rel
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.exists():
                p.unlink()


class GitHubPagesHost(MediaHost):
    def __init__(self, settings: Settings):
        self.repo = settings.env("MEDIA_REPO")
        self.token = settings.env("MEDIA_REPO_TOKEN")
        self.branch = settings.env("MEDIA_BRANCH", "main")
        self.base_url = settings.env("MEDIA_BASE_URL", "")
        if not (self.repo and self.token and self.base_url):
            raise MediaHostError("MEDIA_REPO / MEDIA_REPO_TOKEN / MEDIA_BASE_URL を設定してください")
        self.work = settings.data_dir / "_media_repo"

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        p = subprocess.run(["git", *args], cwd=cwd or self.work, capture_output=True, text=True, env=env)
        if p.returncode != 0:
            raise MediaHostError(f"git {args[0]} failed: {p.stderr.replace(self.token or '', '***')[-500:]}")
        return p.stdout

    def sync(self, files, deletes=None, message="update"):
        remote = f"https://x-access-token:{self.token}@github.com/{self.repo}.git"
        if self.work.exists():
            shutil.rmtree(self.work)
        self._git("clone", "--depth", "1", "--branch", self.branch, remote, str(self.work), cwd=self.work.parent)
        self._git("config", "user.name", "autopilot-bot")
        self._git("config", "user.email", "autopilot-bot@users.noreply.github.com")
        _write(self.work / ".nojekyll", "")
        for rel, src in files.items():
            _write(self.work / rel, src)
        for rel in deletes or []:
            p = self.work / rel
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            elif p.exists():
                p.unlink()
        self._git("add", "-A")
        if not self._git("status", "--porcelain").strip():
            return
        self._git("commit", "-m", message)
        for attempt in range(4):
            try:
                self._git("push", "origin", self.branch)
                return
            except MediaHostError:
                time.sleep(2 ** attempt * 2)
                self._git("pull", "--rebase", "origin", self.branch)
        raise MediaHostError("push に失敗しました")


def get_host(settings: Settings) -> MediaHost:
    backend = settings.env("MEDIA_HOST_BACKEND") or settings.get("media_host.backend", "github_pages")
    if settings.sample_mode or backend == "local":
        root = settings.output_dir / "public"
        return DirHost(root, root.resolve().as_uri())
    if backend == "static_dir":
        return DirHost(Path(settings.env("MEDIA_STATIC_DIR", str(settings.output_dir / "public"))),
                       settings.env("MEDIA_BASE_URL", ""))
    return GitHubPagesHost(settings)

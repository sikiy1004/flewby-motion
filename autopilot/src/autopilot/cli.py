"""コマンドライン：autopilot <command>

  demo        サンプルデータで「カルーセル1投稿分」と「ショート動画1本」をローカル生成（APIキー不要）
  generate    収集→企画→台本→画像/動画→公開URL化（バッファ補充）。cron で毎日実行
  publish     投稿スロットに従って 1 件投稿（--slot auto で現在時刻から判定）
  maintain    インサイト取得・学習・トークン更新・メディア掃除・週次レポート
  doctor      設定・APIキー・依存ツールの診断
  status      バッファと直近の投稿状況を表示
  keygen      トークン暗号化用の AUTOPILOT_SECRET_KEY を生成
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .config import load_settings, now_jst
from .db import DB


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
    for noisy in ("urllib3", "asyncio", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_demo(args) -> int:
    from . import pipeline

    out = Path(args.out).resolve() if args.out else None
    os.environ.setdefault("AUTOPILOT_DATA_DIR", str((out or Path("output/demo")).resolve() / "_data"))
    if out:
        os.environ["AUTOPILOT_OUTPUT_DIR"] = str(out)
    s = load_settings(sample_mode=True)
    s.data.setdefault("volume", {})["buffer_days"] = 1
    db_path = s.db_path
    if db_path.exists():
        db_path.unlink()
    db = DB(db_path)
    try:
        summary = pipeline.generate(s, db)
        for slot in ("carousel", "story", "reel"):
            summary[f"publish_{slot}"] = pipeline.publish(s, db, slot, force=True)
        os.environ["TIKTOK_ENABLED"] = "true"
        summary["publish_tiktok"] = pipeline.publish(s, db, "tiktok", force=True)
        (s.output_dir / "public").mkdir(exist_ok=True)
        _print(summary)
        print("\n生成物:")
        for p in db.posts_by_status(["published", "ready", "skipped"]):
            print(f"  No.{p['post_no']:03d} {p['kind']:8s} {p['format']:10s} {p['status']:9s} -> {p['assets_dir']}")
            if p["status"] == "skipped":
                print(f"      理由: {p['last_error']}")
        print(f"  リンク集ページ -> {s.output_dir / 'public' / 'index.html'}")
        return 0
    finally:
        db.close()


def cmd_generate(args) -> int:
    from . import pipeline

    s = load_settings(sample_mode=args.sample, dry_run=args.dry_run)
    db = DB(s.db_path)
    try:
        _print(pipeline.generate(s, db))
        return 0
    finally:
        db.close()


def cmd_publish(args) -> int:
    from . import pipeline

    s = load_settings(sample_mode=args.sample, dry_run=args.dry_run)
    db = DB(s.db_path)
    try:
        _print(pipeline.publish(s, db, args.slot, force=args.force))
        return 0
    finally:
        db.close()


def cmd_maintain(args) -> int:
    from . import pipeline

    s = load_settings(sample_mode=args.sample, dry_run=args.dry_run)
    db = DB(s.db_path)
    try:
        _print(pipeline.maintain(s, db))
        return 0
    finally:
        db.close()


def cmd_collect(args) -> int:
    from . import pipeline

    s = load_settings(sample_mode=args.sample)
    db = DB(s.db_path)
    try:
        _print(pipeline.collect(s, db, force=True))
        return 0
    finally:
        db.close()


def cmd_status(args) -> int:
    s = load_settings()
    db = DB(s.db_path)
    try:
        rows = db.q("SELECT kind, status, COUNT(*) c FROM posts GROUP BY 1,2 ORDER BY 1,2")
        print("投稿の状態:")
        for r in rows:
            print(f"  {r['kind']:8s} {r['status']:10s} {r['c']}")
        print("\n直近の投稿:")
        for r in db.q("SELECT p.post_no, pub.platform, pub.kind, pub.status, pub.published_at, pub.permalink, pub.error "
                      "FROM publications pub JOIN posts p ON p.id=pub.post_id ORDER BY pub.id DESC LIMIT 10"):
            print(f"  No.{r['post_no']:03d} {r['platform']:9s} {r['kind']:8s} {r['status']:10s} "
                  f"{(r['published_at'] or '')[:16]} {r['permalink'] or ''} {(r['error'] or '')[:80]}")
        print("\n直近の実行:")
        for r in db.q("SELECT job, started_at, status, summary FROM runs ORDER BY id DESC LIMIT 5"):
            print(f"  {r['started_at'][:16]} {r['job']:9s} {r['status']}  {(r['summary'] or '')[:100]}")
        until = db.kv_get("breaker_until")
        if until:
            print(f"\nサーキットブレーカー: {until} まで停止（解除: autopilot reset-breaker）")
        return 0
    finally:
        db.close()


def cmd_reset_breaker(args) -> int:
    s = load_settings()
    db = DB(s.db_path)
    db.kv_set("breaker_until", "")
    db.kv_set("consecutive_failures", "0")
    db.close()
    print("解除しました")
    return 0


def cmd_keygen(args) -> int:
    from .tokens import new_key

    print(new_key())
    return 0


def cmd_doctor(args) -> int:
    import requests

    s = load_settings()
    ok = True

    def line(flag: bool | None, name: str, detail: str = "") -> None:
        nonlocal ok
        mark = {True: "OK ", False: "NG ", None: "-- "}[flag]
        if flag is False:
            ok = False
        print(f"  [{mark}] {name} {detail}")

    print("ツール:")
    line(shutil.which("ffmpeg") is not None, "ffmpeg")
    filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout if shutil.which("ffmpeg") else ""
    line(" ass " in filters, "ffmpeg libass（字幕焼き込み）")
    line(all((s.fonts_dir / f).exists() for f in ("NotoSansJP_700Bold.ttf", "NotoSansJP_800ExtraBold.ttf")), "日本語フォント")
    try:
        from .render import browser
        with browser() as b:
            b.new_page().close()
        line(True, "Playwright Chromium")
    except Exception as e:
        line(False, "Playwright Chromium", f"→ python -m playwright install chromium （{str(e)[:80]}）")
    try:
        r = requests.get(f"{s.env('VOICEVOX_URL', 'http://localhost:50021')}/version", timeout=3)
        line(r.ok, "VOICEVOX Engine", r.text.strip())
    except requests.RequestException:
        line(False, "VOICEVOX Engine", "→ docker compose up -d voicevox")

    print("\n必須の設定:")
    for k in ("RAKUTEN_APP_ID", "RAKUTEN_AFFILIATE_ID", "IG_ACCESS_TOKEN", "AUTOPILOT_SECRET_KEY"):
        line(bool(s.env(k)), k)
    backend = s.env("MEDIA_HOST_BACKEND") or s.get("media_host.backend")
    if backend == "github_pages":
        for k in ("MEDIA_REPO", "MEDIA_REPO_TOKEN", "MEDIA_BASE_URL"):
            line(bool(s.env(k)), k)
    print("\n任意の設定（あると品質・安定性が上がる）:")
    for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "PEXELS_API_KEY", "AMAZON_ASSOCIATE_TAG",
              "DISCORD_WEBHOOK_URL"):
        line(True if s.env(k) else None, k)
    print(f"\nTikTok: {'有効' if s.platform_enabled('tiktok') else '無効'}")
    if s.platform_enabled("tiktok"):
        for k in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN"):
            line(bool(s.env(k)), k)
    if s.env("IG_ACCESS_TOKEN") and args.online:
        from .publish.instagram import InstagramPublisher
        try:
            ig = InstagramPublisher(s, None)
            line(True, "Instagram API", f"user_id={ig._user_id()} 残り投稿枠={ig.quota_left()}")
        except Exception as e:
            line(False, "Instagram API", str(e)[:120])
    print(f"\n現在時刻(JST): {now_jst():%Y-%m-%d %H:%M}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="autopilot", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="サンプルデータでカルーセルと動画を生成（APIキー不要）")
    d.add_argument("--out", help="出力先（既定: output/）")
    d.set_defaults(fn=cmd_demo)

    for name, fn in (("generate", cmd_generate), ("maintain", cmd_maintain), ("collect", cmd_collect)):
        sp = sub.add_parser(name)
        sp.add_argument("--sample", action="store_true", help="サンプルデータを使う（投稿は dry-run）")
        sp.add_argument("--dry-run", action="store_true")
        sp.set_defaults(fn=fn)

    pb = sub.add_parser("publish")
    pb.add_argument("--slot", default="auto", help="auto / story / carousel / reel / tiktok")
    pb.add_argument("--force", action="store_true", help="本日実行済みでも実行")
    pb.add_argument("--sample", action="store_true")
    pb.add_argument("--dry-run", action="store_true")
    pb.set_defaults(fn=cmd_publish)

    dr = sub.add_parser("doctor")
    dr.add_argument("--online", action="store_true", help="Instagram API への疎通も確認")
    dr.set_defaults(fn=cmd_doctor)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("reset-breaker").set_defaults(fn=cmd_reset_breaker)
    sub.add_parser("keygen").set_defaults(fn=cmd_keygen)

    args = p.parse_args(argv)
    _setup_logging(args.verbose)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Playwright MCP で取得した note のページ情報の保存と、ブラウザ操作のエラー記録。

使い方:
  python3 scripts/note_pages.py save <browser_evaluate が保存したJSON> [--keep-body]
  python3 scripts/note_pages.py error <step> <url> "<エラー内容>" "<推定原因>" "<次の対応>"
  python3 scripts/note_pages.py login <logged_in|logged_out|unknown> "<判定の根拠>"

save:
  research/note-pages/index.csv に1行追加（同じURLは上書き）し、
  research/note-pages/<id>.md にメタデータと冒頭の抜粋を書く。
  本文全文は --keep-body を付けたときだけ research/note-pages/raw/<id>.md に保存する（raw/ は git 管理外）。
  他人の記事の全文をリポジトリに入れないための区別。
error / login:
  research/browser/errors.csv、research/browser/login_status.csv に追記する。
  Cookie の値やパスワードは記録しない。
"""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

from common import ROOT, read_csv, write_csv

PAGES = ROOT / "research" / "note-pages"
BROWSER = ROOT / "research" / "browser"
INDEX_FIELDS = ["id", "url", "title", "author", "published_at", "price_hint", "paywall_hint",
                "body_chars", "hashtags", "title_source", "body_source", "fetched_at"]
ERROR_FIELDS = ["at", "step", "url", "error", "cause", "next_action"]
LOGIN_FIELDS = ["at", "status", "evidence"]
EXCERPT_CHARS = 400


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def page_id(url):
    m = re.search(r"/n/(n[0-9a-z]+)", url)
    return m.group(1) if m else "u" + hashlib.sha1(url.encode()).hexdigest()[:12]


def cmd_save(path, keep_body):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # browser_evaluate のファイル出力は、戻り値そのもの、または {"result": ...} の形になりうる
    data = raw.get("result", raw) if isinstance(raw, dict) else raw
    if isinstance(data, str):
        data = json.loads(data)
    if not data.get("url"):
        sys.exit("url がありません。extract_note_article.js の結果か確認してください")
    pid = page_id(data["url"])
    row = {
        "id": pid, "url": data["url"], "title": data.get("title", ""), "author": data.get("author", ""),
        "published_at": data.get("published_at", ""), "price_hint": data.get("price_hint", ""),
        "paywall_hint": str(data.get("paywall_hint", "")).lower(), "body_chars": data.get("body_chars", ""),
        "hashtags": " ".join(data.get("hashtags", [])), "title_source": data.get("source", {}).get("title", ""),
        "body_source": data.get("source", {}).get("body", ""), "fetched_at": data.get("fetched_at", now()),
    }
    index = PAGES / "index.csv"
    _, rows = read_csv(index)
    rows = [r for r in rows if r["url"] != row["url"]] + [row]
    write_csv(index, INDEX_FIELDS, rows)

    body = data.get("body", "")
    excerpt = body[:EXCERPT_CHARS] + ("…" if len(body) > EXCERPT_CHARS else "")
    md = [f"# {row['title']}", "",
          "| 項目 | 値 |", "|---|---|"]
    md += [f"| {k} | {row[k]} |" for k in INDEX_FIELDS if k not in ("title",)]
    md += ["", "## 説明（og:description）", "", data.get("description", "") or "（なし）",
           "", f"## 冒頭の抜粋（{EXCERPT_CHARS}字まで。分析用。全文はこのファイルに含めない）", "", excerpt or "（本文を取得できなかった）"]
    if keep_body:
        (PAGES / "raw").mkdir(parents=True, exist_ok=True)
        (PAGES / "raw" / f"{pid}.md").write_text(f"# {row['title']}\n\n{data['url']}\n\n{body}\n", encoding="utf-8")
        md += ["", f"本文全文：`research/note-pages/raw/{pid}.md`（git 管理外）"]
    (PAGES / f"{pid}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"保存しました: research/note-pages/{pid}.md（タイトル: {row['title']}、本文 {row['body_chars']} 字）")
    if not body:
        print("WARN 本文が空です。セレクタが合っていない可能性があります。errors.csv に記録してください")


def append(path, fields, row):
    _, rows = read_csv(path)
    write_csv(path, fields, rows + [row])


def cmd_error(step, url, error, cause, next_action):
    append(BROWSER / "errors.csv", ERROR_FIELDS,
           {"at": now(), "step": step, "url": url, "error": error[:500], "cause": cause, "next_action": next_action})
    print("research/browser/errors.csv に記録しました")


def cmd_login(status, evidence):
    if status not in ("logged_in", "logged_out", "unknown"):
        sys.exit("status は logged_in / logged_out / unknown のいずれか")
    append(BROWSER / "login_status.csv", LOGIN_FIELDS, {"at": now(), "status": status, "evidence": evidence})
    print(f"ログイン状態を記録しました: {status}")


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "save":
        cmd_save(a[1], "--keep-body" in a)
    elif len(a) == 6 and a[0] == "error":
        cmd_error(*a[1:])
    elif len(a) == 3 and a[0] == "login":
        cmd_login(a[1], a[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

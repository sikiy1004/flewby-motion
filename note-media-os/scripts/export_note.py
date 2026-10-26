#!/usr/bin/env python3
"""レビューに合格した下書きから、note投稿用のファイルを作る（STEP 12）。

使い方:
  python3 scripts/export_note.py articles/drafts/<slug>.md

作るファイル:
  articles/ready_to_publish/<slug>.note.md     note に貼り付ける本文
  articles/ready_to_publish/<slug>.publish.md  公開チェックリストと承認欄

check_article.py --final に通らない下書きは出力しない。出力後、記事は awaiting_approval になる。
noteへの投稿はしない。
"""
import subprocess
import sys
from pathlib import Path

from common import (ARTICLES, INDEX, INDEX_FIELDS, PAYWALL, PAYWALL_NOTE_LINE, read_csv,
                    set_front_matter, split_front_matter, to_int, today, write_csv)

CHECKLIST = """\
---
slug: {slug}
status: awaiting_approval
exported: {today}
---
# 公開チェックリスト：{title}

| 項目 | 値 |
|---|---|
| タイトル | {title} |
| 価格 | {price} |
| 品質スコア | {score} / 100 |
| 文字数（付録を除く） | {length} |
| 有料ライン | 本文中の「{marker}」の位置 |
| ハッシュタグ案 | （メインのセッションが記入） |
| マガジン案 | （メインのセッションが記入） |
| レビュー記録 | articles/review/{slug}.md |
| リサーチ記録 | articles/research/{slug}.md |

## 公開前に人間が確認すること

- [ ] タイトルと冒頭3段落を読み、煽りや誇張がない
- [ ] 参考文献のうち、少なくとも主要な2〜3件のリンクを自分で開いて確認した
- [ ] 「筆者の考察」として書かれた部分の主張に、自分も責任を持てる
- [ ] 人物・研究への言及に、不当な批判がない
- [ ] 図版・引用の権利に問題がない
- [ ] 有料部分に、無料部分にない明確な追加価値がある
- [ ] note の利用規約・ガイドラインに反していない
- [ ] AI利用の開示方針（config/settings.md）に沿っている

## 承認

承認するときは `/approve-article {slug}` を実行する（このファイルを直接書き換えない）。

- 承認者：
- 承認日：
"""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    scripts = Path(__file__).resolve().parent
    check = subprocess.run([sys.executable, str(scripts / "check_article.py"), str(path), "--final"])
    if check.returncode != 0:
        sys.exit("check_article.py --final に通らないため、出力を中止しました")

    text = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(text)
    slug = meta["slug"]
    price = to_int(meta["price_yen"])
    note_body = body.strip()
    # note ではタイトルを別の欄に入力するので、本文先頭の見出し（# タイトル）は除く
    if note_body.startswith("# "):
        note_body = note_body.partition("\n")[2].lstrip()
    note_body = note_body.replace(PAYWALL, PAYWALL_NOTE_LINE) + "\n"
    length = len("".join(body.split("\n## 確度の一覧")[0].split()))

    out = ARTICLES / "ready_to_publish"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{slug}.note.md").write_text(note_body, encoding="utf-8")
    (out / f"{slug}.publish.md").write_text(CHECKLIST.format(
        slug=slug, title=meta["title"], price=f"{price}円" if price else "無料",
        score=meta.get("quality_score", ""), length=length, marker=PAYWALL_NOTE_LINE, today=today(),
    ), encoding="utf-8")

    path.write_text(set_front_matter(text, {"status": "awaiting_approval", "updated": today()}), encoding="utf-8")
    fields, rows = read_csv(INDEX)
    for row in rows:
        if row["slug"] == slug:
            row["status"] = "awaiting_approval"
    write_csv(INDEX, INDEX_FIELDS, rows)
    print(f"出力しました: articles/ready_to_publish/{slug}.note.md, {slug}.publish.md（承認待ち）")


if __name__ == "__main__":
    main()

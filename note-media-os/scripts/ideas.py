#!/usr/bin/env python3
"""記事企画バックログの採点・優先度付け・重複チェック。

使い方:
  python3 scripts/ideas.py score              # total と priority を再計算して ideas.csv を上書き
  python3 scripts/ideas.py top [N] [GENRE]    # 未着手の上位 N 件を表示（GENRE で絞り込み可）
  python3 scripts/ideas.py dup "タイトル案"     # 既存の企画・記事との類似を確認
  python3 scripts/ideas.py next [N]           # 販売実績を加味した次の制作候補（/next-article が使う）

標準ライブラリのみ使用。
"""
import csv
import difflib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDEAS = ROOT / "ideas" / "backlog" / "ideas.csv"
ARTICLES = ROOT / "articles" / "index.csv"
GENRE_STATS = ROOT / "analytics" / "reports" / "latest_genre_stats.csv"

SCORE_COLS = ["s_interest", "s_originality", "s_depth", "s_paid", "s_fit", "s_series"]
MAX = {"s_interest": 20, "s_originality": 20, "s_depth": 20, "s_paid": 20, "s_fit": 10, "s_series": 10}
DUP_THRESHOLD = 0.6


def load(path):
    if not path.exists():
        return [], []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def save(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def priority(total):
    if total >= 80:
        return "A"
    if total >= 70:
        return "B"
    return "C"


def cmd_score():
    fields, rows = load(IDEAS)
    for row in rows:
        for col in SCORE_COLS:
            value = int(row[col])
            if not 0 <= value <= MAX[col]:
                sys.exit(f"{row['id']}: {col}={value} は 0〜{MAX[col]} の範囲外です")
        total = sum(int(row[c]) for c in SCORE_COLS)
        row["total"] = str(total)
        row["priority"] = priority(total)
    save(IDEAS, fields, rows)
    counts = {}
    for row in rows:
        counts[row["priority"]] = counts.get(row["priority"], 0) + 1
    print(f"{len(rows)} 件を採点しました: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


def cmd_top(n=10, genre=None):
    _, rows = load(IDEAS)
    rows = [r for r in rows if r["status"] == "backlog" and (genre is None or r["genre_id"] == genre)]
    rows.sort(key=lambda r: int(r["total"] or 0), reverse=True)
    for r in rows[:n]:
        print(f"{r['total']:>3} [{r['priority']}] {r['id']}  {r['title']}  ({r['price_yen']}円)")


def bigrams(text):
    text = "".join(ch for ch in text if ch.isalnum())
    return {text[i:i + 2] for i in range(len(text) - 1)}


def similarity(a, b):
    """文字列の一致率と文字バイグラムの重なり係数の大きい方。日本語の言い換えにもある程度反応する。"""
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    ga, gb = bigrams(a), bigrams(b)
    overlap = len(ga & gb) / min(len(ga), len(gb)) if ga and gb else 0.0
    return max(ratio, overlap)


def similar(title, candidates):
    hits = []
    for source, cid, ctitle in candidates:
        ratio = similarity(title, ctitle)
        if ratio >= DUP_THRESHOLD:
            hits.append((ratio, source, cid, ctitle))
    return sorted(hits, reverse=True)


def cmd_dup(title):
    candidates = []
    _, ideas = load(IDEAS)
    candidates += [("idea", r["id"], r["title"]) for r in ideas]
    _, articles = load(ARTICLES)
    candidates += [("article", r["slug"], r["title"]) for r in articles]
    hits = similar(title, candidates)
    if not hits:
        print("類似する企画・記事は見つかりませんでした（タイトル文字列の比較のみ。内容の重複は人間または編集エージェントが確認してください）")
        return
    for ratio, source, cid, ctitle in hits:
        print(f"{ratio:.2f} {source:<7} {cid}  {ctitle}")


def genre_bonus():
    """実績が十分なジャンルだけ、購入率の平均との差を -10〜+10 点の補正にする。"""
    _, stats = load(GENRE_STATS)
    rates = {r["genre_id"]: float(r["purchase_rate"]) for r in stats if r["sufficient"] == "yes" and r["purchase_rate"]}
    if len(rates) < 2:
        return {}, "販売実績が十分なジャンルが2つ未満のため、補正なし（企画の評価点のみで順位付け）"
    mean = sum(rates.values()) / len(rates)
    if mean == 0:
        return {}, "購入率がすべて0のため、補正なし"
    bonus = {g: max(-10, min(10, round(10 * (r / mean - 1)))) for g, r in rates.items()}
    return bonus, "販売実績による補正: " + ", ".join(f"{g} {b:+d}" for g, b in sorted(bonus.items()))


def cmd_next(n=5):
    bonus, note = genre_bonus()
    _, rows = load(IDEAS)
    rows = [r for r in rows if r["status"] == "backlog"]
    ranked = sorted(rows, key=lambda r: int(r["total"] or 0) + bonus.get(r["genre_id"], 0), reverse=True)
    print(note)
    for r in ranked[:n]:
        b = bonus.get(r["genre_id"], 0)
        print(f"{int(r['total']) + b:>3} (評価{r['total']}{b:+d}) {r['id']}  {r['title']}  ({r['price_yen']}円)")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "score":
        cmd_score()
    elif args[0] == "top":
        n = int(args[1]) if len(args) > 1 else 10
        genre = args[2] if len(args) > 2 else None
        cmd_top(n, genre)
    elif args[0] == "dup" and len(args) > 1:
        cmd_dup(args[1])
    elif args[0] == "next":
        cmd_next(int(args[1]) if len(args) > 1 else 5)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()

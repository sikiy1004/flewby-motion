#!/usr/bin/env python3
"""販売実績の集計とレポート作成（Phase 4）。

使い方:
  python3 scripts/analytics.py            # レポートを analytics/reports/ に書き出す
  python3 scripts/analytics.py --stdout   # 書き出さずに表示だけ

入力:
  articles/index.csv            記事のメタデータ（ジャンル・タイトルの型・価格・制作時間）
  analytics/sales/sales.csv     月ごと・記事ごとの実績（人間が note の管理画面から手入力する）
    period       集計月（YYYY-MM）
    slug         記事のslug（index.csv と一致させる）
    views        その月のビュー数
    purchases    その月の購入数
    revenue_yen  その月の売上（税込の販売額。空欄なら purchases × price_yen で計算）
    likes / comments / reaction_notes  反応（任意）

出力:
  analytics/reports/YYYY-MM-DD_report.md
  analytics/reports/latest_genre_stats.csv   （/next-article と /genre-analysis が参照する）
"""
import sys
from collections import defaultdict

from common import INDEX, REPORTS, SALES, read_csv, to_int, today, write_csv

TARGET_LOW, TARGET_HIGH = 100_000, 300_000
MIN_ARTICLES = 5     # ジャンル・型ごとの比較に必要な公開本数
MIN_VIEWS = 300      # 購入率を比較に使う最低ビュー数


def pct(a, b):
    return f"{a / b:.1%}" if b else "—"


def load():
    _, index = read_csv(INDEX)
    meta = {r["slug"]: r for r in index}
    _, sales = read_csv(SALES)
    per_article = defaultdict(lambda: {"views": 0, "purchases": 0, "revenue": 0, "likes": 0, "comments": 0, "notes": []})
    per_month = defaultdict(int)
    unknown = set()
    for s in sales:
        slug = s["slug"]
        if slug not in meta:
            unknown.add(slug)
            continue
        price = to_int(meta[slug]["price_yen"])
        revenue = to_int(s["revenue_yen"]) if s.get("revenue_yen", "").strip() else to_int(s["purchases"]) * price
        a = per_article[slug]
        a["views"] += to_int(s["views"])
        a["purchases"] += to_int(s["purchases"])
        a["revenue"] += revenue
        a["likes"] += to_int(s.get("likes", 0))
        a["comments"] += to_int(s.get("comments", 0))
        if s.get("reaction_notes", "").strip():
            a["notes"].append(f"{s['period']}: {s['reaction_notes'].strip()}")
        per_month[s["period"]] += revenue
    return meta, per_article, per_month, unknown


def group(meta, per_article, key):
    groups = defaultdict(lambda: {"articles": 0, "paid_articles": 0, "views": 0, "paid_views": 0, "purchases": 0, "revenue": 0})
    for slug, m in meta.items():
        if m["status"] != "published":
            continue
        g = groups[m.get(key) or "（未設定）"]
        a = per_article.get(slug, {"views": 0, "purchases": 0, "revenue": 0})
        g["articles"] += 1
        g["views"] += a["views"]
        g["purchases"] += a["purchases"]
        g["revenue"] += a["revenue"]
        if to_int(m["price_yen"]) > 0:
            g["paid_articles"] += 1
            g["paid_views"] += a["views"]
    return groups


def group_table(groups, label):
    lines = [f"| {label} | 公開本数 | 有料本数 | 購入数 | 売上 | 購入率（有料記事） | 1本あたり売上 | 判定 |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for name, g in sorted(groups.items(), key=lambda kv: -kv[1]["revenue"]):
        enough = g["paid_articles"] >= MIN_ARTICLES and g["paid_views"] >= MIN_VIEWS
        per = g["revenue"] // g["paid_articles"] if g["paid_articles"] else 0
        lines.append(f"| {name} | {g['articles']} | {g['paid_articles']} | {g['purchases']} | {g['revenue']:,}円 | "
                     f"{pct(g['purchases'], g['paid_views'])} | {per:,}円 | {'比較可' if enough else 'データ不足'} |")
    return "\n".join(lines)


def build():
    meta, per_article, per_month, unknown = load()
    published = [s for s, m in meta.items() if m["status"] == "published"]
    out = [f"# 販売実績レポート（{today()}）", ""]
    if unknown:
        out += [f"> 注意：sales.csv に index.csv に無い slug があります（集計から除外）: {', '.join(sorted(unknown))}", ""]
    if not published:
        out += ["公開済みの記事がまだありません。`/mark-published` で公開を記録し、`analytics/sales/sales.csv` に実績を入力してください。"]
        return "\n".join(out), {}

    total = sum(a["revenue"] for a in per_article.values())
    out += ["## 1. 目標までの進捗", "",
            "| 月 | 売上 | 月10万円に対して | 月30万円に対して |", "|---|---:|---:|---:|"]
    for month in sorted(per_month):
        r = per_month[month]
        out.append(f"| {month} | {r:,}円 | {pct(r, TARGET_LOW)} | {pct(r, TARGET_HIGH)} |")
    latest = max(per_month) if per_month else None
    if latest:
        gap = max(TARGET_LOW - per_month[latest], 0)
        out += ["", f"直近（{latest}）の売上は {per_month[latest]:,}円。月10万円まで残り {gap:,}円"
                f"（500円の記事で約{-(-gap // 500)}部）。"]
    out += ["", f"累計売上：{total:,}円 ／ 公開本数：{len(published)}本", ""]

    rows = []
    for slug in published:
        m, a = meta[slug], per_article.get(slug, {"views": 0, "purchases": 0, "revenue": 0, "likes": 0, "comments": 0, "notes": []})
        minutes = to_int(m.get("production_minutes", 0))
        hourly = a["revenue"] * 60 // minutes if minutes else None
        rows.append((slug, m, a, hourly))
    rows.sort(key=lambda r: -r[2]["revenue"])

    out += ["## 2. 記事別の実績（売上順）", "",
            "| 記事 | ジャンル | 型 | 価格 | ビュー | 購入 | 購入率 | 売上 | スキ | コメント | 制作1時間あたり売上 |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for slug, m, a, hourly in rows:
        rate = pct(a["purchases"], a["views"]) if to_int(m["price_yen"]) else "（無料）"
        out.append(f"| {m['title']} | {m['genre_id']} | {m['title_type']} | {m['price_yen']} | {a['views']} | {a['purchases']} | "
                   f"{rate} | {a['revenue']:,}円 | {a['likes']} | {a['comments']} | {f'{hourly:,}円' if hourly is not None else '—'} |")

    genres = group(meta, per_article, "genre_id")
    types = group(meta, per_article, "title_type")
    out += ["", "## 3. ジャンル別", "", group_table(genres, "ジャンル"),
            "", "## 4. タイトルの型別", "", group_table(types, "型"), ""]

    paid = [r for r in rows if to_int(r[1]["price_yen"]) > 0]
    weak = [r for r in paid if r[2]["views"] >= 100 and r[2]["purchases"] == 0]
    out += ["## 5. 売れていない有料記事（ビュー100以上・購入0）", ""]
    out += [f"- {r[1]['title']}（{r[1]['genre_id']}／{r[1]['title_type']}／ビュー{r[2]['views']}）" for r in weak] or ["- 該当なし"]

    notes = [(r[1]["title"], n) for r in rows for n in r[2]["notes"]]
    out += ["", "## 6. 読者の反応メモ", ""]
    out += [f"- {t}：{n}" for t, n in notes] or ["- 記録なし"]

    comparable = [g for g in genres.values() if g["paid_articles"] >= MIN_ARTICLES and g["paid_views"] >= MIN_VIEWS]
    out += ["", "## 7. 解釈の注意", "",
            f"- 比較できるのは、有料記事が{MIN_ARTICLES}本以上、かつ有料記事の合計ビューが{MIN_VIEWS}以上のグループだけ。"
            "それ以外は「データ不足」とし、成功パターンとして扱わない。",
            f"- 現在、比較可能なジャンルは {len(comparable)} 件。"]
    if len(comparable) < 2:
        out.append("- ジャンル間の比較はまだできない。次の企画は、市場調査の評価点（ideas.csv の total）を主な基準にする。")

    stats = {name: g for name, g in genres.items()}
    return "\n".join(out) + "\n", stats


def main():
    report, stats = build()
    if "--stdout" in sys.argv:
        print(report)
        return
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{today()}_report.md"
    path.write_text(report, encoding="utf-8")
    fields = ["genre_id", "articles", "paid_articles", "views", "paid_views", "purchases", "revenue", "purchase_rate", "sufficient"]
    rows = []
    for name, g in stats.items():
        rows.append({
            "genre_id": name, **{k: g[k] for k in ["articles", "paid_articles", "views", "paid_views", "purchases", "revenue"]},
            "purchase_rate": f"{g['purchases'] / g['paid_views']:.4f}" if g["paid_views"] else "",
            "sufficient": "yes" if g["paid_articles"] >= MIN_ARTICLES and g["paid_views"] >= MIN_VIEWS else "no",
        })
    write_csv(REPORTS / "latest_genre_stats.csv", fields, rows)
    print(f"書き出しました: {path.relative_to(REPORTS.parent.parent)}")


if __name__ == "__main__":
    main()

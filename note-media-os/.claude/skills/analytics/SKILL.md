---
name: analytics
description: 販売実績を集計・分析し、売上上位の記事、ジャンル別・タイトルの型別の購入率、売れない記事の共通点、目標までの進捗をレポートする（Phase 4）。実績の手入力の補助もする。
argument-hint: "[入力する実績（任意。例：2026-11 i-g05-01 views=420 purchases=9）]"
---

# /analytics

引数：$ARGUMENTS

1. 引数に実績が書かれていれば、`analytics/sales/sales.csv` に行を追加する（列：period, slug, views, purchases, revenue_yen, likes, comments, reaction_notes）。同じ period と slug の行が既にあれば、上書きしてよいか確認する。
   - 実績は note のダッシュボードから人間が転記する。Claude は note の管理画面にアクセスしない。
2. `python3 scripts/analytics.py` を実行し、`analytics/reports/<今日の日付>_report.md` と `latest_genre_stats.csv` を作る。
3. レポートを読み、次の観点で考察を加えて、レポートの末尾に「## 8. 考察と次の打ち手」として追記する。
   - 売上上位の記事と、反応の良いテーマの共通点
   - タイトルの傾向（型別の購入率）
   - 売れない記事の共通点（無料部分の設計、テーマ、タイトル）
   - 次に制作すべき記事（`python3 scripts/ideas.py next 5` の結果）
   - 目標までの進捗と、そのために必要なこと
4. **「データ不足」と判定されたグループについて、成功パターンを断定しない。** 「仮説」として書き、検証方法（次に何本、どの条件で試すか）を添える。
5. 要点を5行以内で報告する。

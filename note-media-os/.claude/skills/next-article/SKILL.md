---
name: next-article
description: 企画の評価点と販売実績から、次に制作すべき記事を3本提案する。制作はしない。
argument-hint: "[genre_id（任意）]"
---

# /next-article

ジャンル指定：$ARGUMENTS

1. 販売実績を更新する：`python3 scripts/analytics.py`（公開記事がなければ省略してよい）。
2. `python3 scripts/ideas.py next 10` を実行する。
3. `genres/selected/top5.md` の配分と、`articles/index.csv` の既存記事の構成を比べる。
4. 次の観点で3本選んで提案する。
   - 評価点（販売実績による補正を含む）
   - ジャンル配分の偏りの是正
   - シリーズのつながり（無料の方法論記事 → 有料記事、など）
   - 直近の記事との重複がないこと
5. 各提案に、企画ID、タイトル、選んだ理由（2行以内）、想定価格を付ける。最後に「制作する場合は `/write-article <企画ID>`」と案内する。

# リサーチ層の使い方（Mac）

流れ：**リサーチ → 投稿案の提示 → あなたが承認 → 原稿データ → 既存エンジンで描画**。
承認はあなたが端末で行うコマンドだけでしか記録されません（Claude Code は承認できません）。

---

## A. まず見本で1回通してみる（テスト用データ・約10分）

商品・価格はすべて架空です。公開には使えません。`ig-pipeline` フォルダのターミナルで、1行ずつ実行します。

1. 最新の内容を取り込む

```bash
git pull
```

2. 見本のリサーチ結果を作る（今日の日付に合わせた、架空の商品3案）

```bash
npm run research:sample
```

3. 投稿案リストを開いて読む

```bash
open -e research/runs/*-sample/ideas.md
```

4. **承認する**（I01 と I02 を承認する例）。内容が表示されるので、確認して `y` を入力します。

```bash
npm run research:approve -- latest I01 I02
```

5. 承認の状況を確認する（I01・I02 に ✓ が付いていれば OK）

```bash
npm run research:approve -- status latest
```

6. 原稿データを作ってチェックする（見本は画像がレイアウト確認用なので `--allow-placeholder` を付けます）

```bash
npm run research:draft -- latest I01 --allow-placeholder
```

`✓ research/runs/…/drafts/…-i01-layout-only/` と出れば成功です。チェック結果を開きます。

```bash
open -e research/runs/*-sample/drafts/*-i01-layout-only/check.md
```

7. 既存エンジンの入力（data/）に取り込む

```bash
npm run research:install -- latest I01 --allow-placeholder
```

8. 描画して確認する（表示された投稿IDのフォルダが out/ にできます）

```bash
npm run cutout && npm run build -- data/posts/$(ls data/posts | grep i01-layout-only)
```

```bash
open out
```

9. 試したあとは片付ける（見本の商品・投稿・画像を data/ と assets/ から削除します）

```bash
npm run research:sample -- --clean
```

**試してみると良いこと**
- 承認していない I03 で `npm run research:draft -- latest I03` → 「承認されていません」で止まる
- `research/runs/*-sample/ideas.json` の I01 の `lead` を書き換えてから 6 を実行 → 「承認後に内容が変更されています」で止まる

---

## B. 本番のリサーチ（Claude Code で）

```bash
cd ~/Documents/flewby-motion/ig-pipeline && git pull && claude
```

Claude Code に送る文の例：

```
/research ドライヤー
```

1. Claude Code が調べて、`research/runs/<実行ID>/ideas.md`（投稿案リスト）を作り、内容を説明して**止まります**。
2. あなたが内容を確認し、端末で承認します（Claude Code の画面ではなく、別のターミナルのタブで実行）：
   `npm run research:approve -- latest I01 I03`
3. Claude Code に送ります：

```
/research-draft I01
```

4. Claude Code が原稿データを作ってチェックし、キャプション案とチェック結果を見せて、取り込むか聞きます。
5. 取り込んだら、描画を頼むか、自分で `npm run cutout && npm run build -- data/posts/<投稿ID>.json` を実行します。

**楽天のキーについて**：楽天ウェブサービスの管理画面が復旧してキーを `.env` に入れるまでは、楽天のデータなしで、メーカー公式サイトなどの
Web 調査だけで進みます。最初の本番実行時に、Claude Code が楽天の公式仕様を確認してから API を使います。

## C. 競合の投稿を記録する（半自動）

Instagram のアプリで競合（@cospa_biyou_lab など）の新しい投稿を見たら、Claude Code に次のように送ります。

```
/competitor-log
https://www.instagram.com/p/（投稿のURL）
（キャプション本文を貼る。またはスクリーンショットを添付。枚数・投稿日が分かれば添える）
```

Claude Code が「型」（テーマ・構成・見出しの作り方）を分類して見せるので、了承すると `research/competitors/log.csv` に記録されます。
キャプション本文は保存されません。Claude Code が Instagram を自分で見に行くことはありません。
記録表は Numbers や Excel で直接編集してもよく、編集後は `npm run research:competitors -- check` で形式を確認できます。

## D. 楽天のデータを本番で使い始める（管理画面の復旧後）

1. 楽天ウェブサービスでアプリを登録し、`.env` に4行を書く（`.env.example` を参照）。
2. 設定を確認する（キーの値は表示されません。すべて ✓ になれば OK。公式仕様の行は 4 で ✓ になります）

```bash
npm run research:rakuten -- --check-setup
```

3. 1件だけ取得して、キーが使えるか確かめる

```bash
npm run research:rakuten -- --ping
```

`✓ 楽天 API に接続できました` と出れば成功です。403 などが出た場合は、アプリの「許可されたWebサイト」と `RAKUTEN_REFERER` のドメインが同じか確認してください。

4. Claude Code で `/research` を実行すると、最初に楽天の公式仕様（接続先・認証・価格やセールの項目・回数制限）を確認して報告します。
   内容に問題がなければ了承してください。設定（`research/config.json` の `specVerified`）が「確認済み」になり、以降は楽天のデータを使ってリサーチします。

## E. 定期実行（週1回）

毎週決まった時間に、Mac が自動でリサーチして**投稿案リストを作り、通知して止まります**。承認・原稿データ・描画は今までどおり手動です。

1. 一度だけ手で試す（数分かかります。終わると通知が出ます）

```bash
zsh scripts/schedule/weekly-research.sh
```

2. 週1回の実行を登録する（例は毎週月曜 7:40。曜日は 0=日〜6=土）

```bash
zsh scripts/schedule/install-weekly.sh 1 7 40
```

3. やめるとき

```bash
zsh scripts/schedule/install-weekly.sh --remove
```

- Mac がスリープ中だった場合は、次に起きたときに実行されます。電源が切れていた場合は、その週は実行されません。
- 実行の記録は `research/logs/` に残ります（Git には上がりません）。
- 自動実行では、承認・原稿データの生成・取り込み・描画・data/ やテンプレートの編集・git への push を**禁止**した状態で Claude Code を動かします。
- 通知が来たら `research/runs/<実行ID>/ideas.md` を開き、承認する案を `npm run research:approve -- latest I01 …` で承認してから、Claude Code で `/research-draft I01` と送ってください。

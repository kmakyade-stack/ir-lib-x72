# scripts/learn — 1000本ノック（learn.html）のデータの作り方

設計の正本：`SCHEMA.md`（データ）・`LEARN_HTML_SPEC.md`（画面）・`prompts/`（Sonnetへの指示）。設計の経緯は vault の `IRライブラリ/_作業/learn/`（2026年10月28日 grill-me）。

## 一度に全社を作る／年1回の更新（8月1日・有報の提出後）

1. **有報の取得**（PC・公式EDINET API。環境変数 `EDINET_API_KEY`）
   ```
   cd "AI環境/運用ルール・仕組み/EDINET公式API"
   python edinet_yuho.py --codes <codes.txt> --out <edinet_out> --fin --rinji
   ```
   `codes.txt` は `data/companies.json` の全社を「EDINETコード\t社名\t証券コード」で1行ずつ。790社で約1時間（背景実行）
2. **入力の組み立て**：`python scripts/learn/build_inputs.py <repo> <edinet_out> <in_dir>` → 1社1ファイルの Markdown
3. **骨格（事業分割・分類）**：Sonnet のサブエージェントに `prompts/skeleton.md` と `<in_dir>/{code}.md` を10社ずつ渡し、`<skeleton_dir>/{code}.json` を書かせる。`python scripts/learn/validate.py skeleton <skeleton_dir>` でNGを直す
4. **本文**：区分ごと（IT04→IT05→IT01→IT03→残り）に `prompts/body.md` で同様に生成し、`validate.py body` で検査。区分ごとに高性能モデルが30社を抜き取り検品する
5. **統合**：`python scripts/learn/merge_profiles.py <repo> <edinet_out> <skeleton_dir> <body_dir>` → `data/profiles.json`・`data/fin.json`
6. commit → push → GitHub Pages で `learn.html` を確認

## 毎月1日（新規上場の反映）

日次更新タスクの月次手順で `data/companies.json` に加わった社について、上の1〜5を**その社だけ**行う（`build_inputs.py` の末尾に証券コードを並べる）。上場廃止で消えた社は `profiles.json`・`fin.json` からも消す。

## 守ること

- 出力は公開ページに載る。自社の案件・接触履歴・売り手の実名を書かない
- 数値は有報の値（円）をそのまま持ち、表示側で丸める
- `profiles.json` を手で直したときは、同じ内容を `<skeleton_dir>`／`<body_dir>` 側にも反映する（次回の merge で上書きされるため）

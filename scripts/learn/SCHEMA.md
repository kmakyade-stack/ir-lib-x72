# learn（IT上場企業 1000本ノック）のデータ仕様

- 対象：`data/companies.json` の全社（本則市場。PRO Marketは入れない）
- 本文の正本：`data/profiles.json`（1社1レコード・キーは証券コード4桁）
- 財務の正本：`data/fin.json`（公式EDINET APIの有報CSVから年1回。売上・営業利益・セグメント別売上）。時価総額は従来どおり `data/finance.json`（yfinance・日次）
- 作り方：`scripts/learn/README.md`

## profiles.json の1レコード

```json
{
  "code": "4198",
  "edinet": "E36637",
  "docID": "S100YXP8",
  "fy_end": "2026-05-31",
  "main_type": "IT05",
  "sub_type": "IT01",
  "non_it": false,
  "one_liner": "文系向けに社全体を1文で（60字以内）",
  "businesses": [
    {
      "name": "事業名（有報のセグメント名・事業系統図の単位。地域や担当子会社が違えば分ける）",
      "entity": "本体 | 子会社名（例：シードテック株式会社）| 本体＋子会社名",
      "segment_member": "有報XBRLのセグメントMember名。対応がなければ null",
      "share_pct": 62.3,
      "share_src": "有報セグメント情報 | 本文の記載 | null",
      "type": "IT01〜IT11 | 非IT-{業種}",
      "customer": ["大企業", "中小企業", "個人", "官公庁・公共"],
      "vertical": "業界特化があれば業界名（例：物流・医療・建設）。なければ \"\"",
      "pricing": ["月額", "従量", "人月・稼働", "成果報酬・手数料", "売り切り・請負", "広告"],
      "who": "誰に（文系向け・60〜120字）",
      "what": "何を（同）",
      "how": "どうやって売るか・届けるか（同）",
      "money_flow": {
        "players": [{"id": "co", "label": "当社"}, {"id": "cl", "label": "顧客（大手企業の開発部門）"}],
        "flows": [{"from": "cl", "to": "co", "what": "月額の業務委託費", "when": "毎月", "kind": "money"},
                  {"from": "co", "to": "cl", "what": "エンジニアの稼働（準委任）", "when": "常時", "kind": "value"}]
      },
      "sources": ["有報：事業の内容", "有報：関係会社の状況", "決算説明資料 2026-07-15"]
    }
  ],
  "glossary": [{"term": "準委任", "plain": "成果物ではなく作業時間に対して報酬を払う契約。完成責任は負わない"}],
  "ma_policy": {"text": "有報「経営方針と課題」等に書かれたM&A・提携の方針を1文。記載がなければ \"\"", "src": "有報：経営方針と課題"},
  "mnemonic": {"text": "覚え方のTips（80字以内）。作れない社はこの項目自体がない", "kind": "由来 | 成り立ち | 語の意味", "basis": "有報の沿革 | 社名の語の意味 など"},
  "status": {"skeleton": "done", "body": "pending"},
  "generated": {"skeleton": "2026-10-28", "body": ""},
  "model": "sonnet"
}
```

### 段階と埋まる項目

| 段階 | 埋める項目 | 担当 |
|---|---|---|
| 骨格（skeleton） | main_type・sub_type・non_it・businesses[].name/entity/segment_member/share_pct/share_src/type/customer/vertical/pricing・status.skeleton | Sonnet（区分を決めるため全社先に） |
| 本文（body） | one_liner・businesses[].who/what/how/money_flow/sources・glossary・ma_policy・status.body | Sonnet（区分ごと）→ Fableが区分ごとに30社を抜き取り検品 |
| 覚え方（tips） | mnemonic | Sonnet（`TIPS_PROMPT.md`・有報の沿革を入力）→ `tips_merge.py` が根拠の一節を原文と照合 → 高性能モデルが抜き取り検品 |

### 列挙の正本

- `type`：[[IT事業モデル類型]]（wiki/業界）の11区分 IT01〜IT11、または `非IT-{業種}`（業種はチートシートの10業種：飲食業・小売業・卸売業・建設業・製造業・運送業・サービス業・医療業・介護業・宿泊業。放送・通信キャリア・出版・金融などは `非IT-サービス業` ではなく `非IT-その他（放送）` のように括弧で実態を書く）
- `customer`：大企業／中小企業／個人／官公庁・公共（複数可・1つ以上）
- `pricing`：月額／従量／人月・稼働／成果報酬・手数料／売り切り・請負／広告（複数可・1つ以上）
- `main_type`：売上構成比が最大の事業の type。`sub_type` は売上20%以上の2番目の事業の type（なければ null）
- `non_it`：main_type が `非IT-` で始まるとき true

### 守ること

- 自社の案件・接触履歴・売り手の実名は書かない（公開ページに載るため）
- 数値は有報の値をそのまま（単位は円。表示側で百万円に丸める）
- 事業の分け方は、有報のセグメント・事業系統図・関係会社の状況に沿う。地域（国内・海外）や担当子会社が違えば別事業として分ける（ギークスの例：IT人材事業〈国内〉／IT人材事業〈海外〉／Seed Tech事業〈シードテック株式会社〉）
- 専門用語は文系ビジネスマン向けに `glossary` で解説する（1社あたり3〜8語）

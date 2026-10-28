"""骨格・本文の生成に使う1社1ファイルの入力（Markdown）を組み立てる。

使い方: python build_inputs.py <repo> <edinet_out> <out_dir> [codes...]
  <repo>       data/companies.json・documents.json のあるリポジトリ
  <edinet_out> edinet_yuho.py --fin の出力フォルダ（text/{EDINET}.txt・fin.json・index.jsonl）
  <out_dir>    出力先。{code}.md を1社1ファイルで書く
  codes        省略時は全社
"""
import json, os, sys

repo, edinet_out, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
only = set(sys.argv[4:])
os.makedirs(out_dir, exist_ok=True)

comps = json.load(open(f"{repo}/data/companies.json", encoding="utf-8"))
docs = json.load(open(f"{repo}/data/documents.json", encoding="utf-8"))
fin = json.load(open(f"{edinet_out}/fin.json", encoding="utf-8"))
by_code = {}
for d in docs:
    by_code.setdefault(d["code"], []).append(d)

def yen_m(v):
    return "" if v is None else f"{round(v / 1e6):,}百万円"

n = 0
for c in comps:
    code = c["code"]
    if only and code not in only:
        continue
    e = c.get("edinet", "")
    tpath = f"{edinet_out}/text/{e}.txt"
    if not os.path.exists(tpath):
        continue
    text = open(tpath, encoding="utf-8").read()
    f = fin.get(e, {})
    lines = [f"# {c['name']}（証券コード {code}・EDINET {e}・{c['market']}）", ""]
    lines += ["## 財務（有報・公式EDINET API）",
              f"- 決算期末：{f.get('periodEnd', '')}／会計基準：{f.get('standard', '')}",
              f"- 売上：{yen_m(f.get('sales'))}（{f.get('sales_scope', '')}）／営業利益：{yen_m(f.get('op'))}（{f.get('op_scope', '')}）"]
    segs = f.get("segments", {})
    if segs:
        lines.append("- 報告セグメント別（XBRLのMember名→外部顧客への売上／セグメント利益）：")
        for m, v in segs.items():
            lines.append(f"  - {m}：売上 {yen_m(v.get('sales'))}／利益 {yen_m(v.get('op'))}")
    else:
        lines.append("- 報告セグメント別の数値：なし（単一セグメント）")
    lines.append("")
    # IRライブラリの要約（新しい順に最大4件・M&A開示はタイトルのみ3件）
    ds = sorted(by_code.get(code, []), key=lambda d: d["date"], reverse=True)
    summ = [d for d in ds if d["kind"] != "M&A開示" and d.get("summary")][:4]
    ma = [d for d in ds if d["kind"] == "M&A開示"][:3]
    lines.append("## IRライブラリの要約（決算説明資料・中計・成長可能性）")
    if summ:
        for d in summ:
            lines.append(f"- {d['date']}｛{d['kind']}｝{d['title']}：{d['summary']}")
    else:
        lines.append("- なし")
    lines.append("## 直近のM&A開示（タイトルのみ）")
    lines += [f"- {d['date']} {d['title']}" for d in ma] or ["- なし"]
    lines.append("")
    lines.append("## 有報の本文（edinet_yuho.py の抜き出し）")
    lines.append(text)
    open(f"{out_dir}/{code}.md", "w", encoding="utf-8").write("\n".join(lines))
    n += 1
print("inputs:", n)

"""骨格・本文の生成に使う1社1ファイルの入力（Markdown）を組み立てる。

使い方: python build_inputs.py <repo> <edinet_out> <out_dir> [--mode skeleton|body] [codes...]
  <repo>       data/companies.json・documents.json のあるリポジトリ
  <edinet_out> edinet_yuho.py --fin の出力フォルダ（text/{EDINET}.txt・fin.json・index.jsonl）
  <out_dir>    出力先。{code}.md を1社1ファイルで書く
  --mode       skeleton＝事業分割・分類に要る節だけ（事業の内容・関係会社・報告セグメント・注記）
               body＝本文に要る節（skeleton＋経営方針・MD&A。リスク・人材・従業員は落とす）。既定は body
  codes        省略時は全社
"""
import json, os, re, sys

args = [a for a in sys.argv[1:]]
mode = "body"
if "--mode" in args:
    i = args.index("--mode")
    mode = args[i + 1]
    del args[i:i + 2]
repo, edinet_out, out_dir = args[0], args[1], args[2]
only = set(args[3:])
os.makedirs(out_dir, exist_ok=True)

KEEP = {
    "skeleton": ["事業の内容", "関係会社の状況", "報告セグメントの概要", "セグメント情報等（注記）"],
    "body": ["事業の内容", "関係会社の状況", "報告セグメントの概要", "セグメント情報等（注記）", "経営方針、経営環境及び対処すべき課題等",
             "経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析"],
}[mode]
CAP = {"セグメント情報等（注記）": 1500, "経営者による財政状態、経営成績及びキャッシュ・フローの状況の分析": 2500}

comps = json.load(open(f"{repo}/data/companies.json", encoding="utf-8"))
docs = json.load(open(f"{repo}/data/documents.json", encoding="utf-8"))
fin = json.load(open(f"{edinet_out}/fin.json", encoding="utf-8"))
by_code = {}
for d in docs:
    by_code.setdefault(d["code"], []).append(d)


def yen_m(v):
    return "" if v is None else f"{round(v / 1e6):,}百万円"


def sections(text):
    """edinet_yuho.py の text を【見出し】ごとに分ける。先頭のヘッダ行も返す"""
    parts = re.split(r"\n【([^】]+)】\n", "\n" + text)
    head = parts[0].strip()
    secs = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    return head, secs


n = 0
for c in comps:
    code = c["code"]
    if only and code not in only:
        continue
    e = c.get("edinet", "")
    tpath = f"{edinet_out}/text/{e}.txt"
    if not os.path.exists(tpath):
        continue
    head, secs = sections(open(tpath, encoding="utf-8").read())
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
    ds = sorted(by_code.get(code, []), key=lambda d: d["date"], reverse=True)
    summ = [d for d in ds if d["kind"] != "M&A開示" and d.get("summary")][:4]
    ma = [d for d in ds if d["kind"] == "M&A開示"][:3]
    lines.append("## IRライブラリの要約（決算説明資料・中計・成長可能性）")
    lines += [f"- {d['date']}｛{d['kind']}｝{d['title']}：{d['summary']}" for d in summ] or ["- なし"]
    lines.append("## 直近のM&A開示（タイトルのみ）")
    lines += [f"- {d['date']} {d['title']}" for d in ma] or ["- なし"]
    lines.append("")
    lines.append("## 有報の本文（公式EDINET API）")
    lines.append(head)
    for k in KEEP:
        v = secs.get(k, "（記載なし）")
        if k in CAP:
            v = v[:CAP[k]]
        lines += ["", f"【{k}】", v]
    open(f"{out_dir}/{code}.md", "w", encoding="utf-8").write("\n".join(lines))
    n += 1
print("inputs:", n, "mode:", mode)

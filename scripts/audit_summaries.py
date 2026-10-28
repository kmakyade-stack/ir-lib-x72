"""要約の金額と有報（fin.json）の桁を突合する月次検査（2026年10月28日新設。毎月1日の手順で実行）。
要約に書かれた最初の売上（売上高・売上収益・営業収益）の金額を円に直し、fin.json の年間売上との比を見る。
比が 5倍以上 または 0.04倍以下 の要約を「桁違いの疑い」として一覧に出す（四半期・計画値は比が0.2〜2程度に収まる）。
使い方: python3 audit_summaries.py <repoパス> [出力md]
"""
import json, re, sys, unicodedata
REPO = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else None
docs = json.load(open(f'{REPO}/data/documents.json', encoding='utf-8'))
fin = json.load(open(f'{REPO}/data/fin.json', encoding='utf-8'))
names = {c['code']: c.get('display') or c.get('name', '') for c in json.load(open(f'{REPO}/data/companies.json', encoding='utf-8'))}
UNIT = {'億円': 1e8, '百万円': 1e6, '千円': 1e3, '万円': 1e4, '兆円': 1e12}
PAT = re.compile(r'(?:売上高|売上収益|営業収益|売上)[^。、0-9]{0,12}?([0-9][0-9,]*(?:\.[0-9]+)?)\s*(億円|百万円|千円|万円|兆円)')
rows = []
for d in docs:
    s = d.get('summary') or ''
    if not s or d.get('kind') == 'M&A開示': continue
    f = fin.get(d['code'])
    if not f or not f.get('sales'): continue
    m = PAT.search(unicodedata.normalize('NFKC', s))
    if not m: continue
    v = float(m.group(1).replace(',', '')) * UNIT[m.group(2)]
    ratio = v / f['sales']
    if ratio >= 5 or ratio <= 0.04:
        rows.append((d['code'], names.get(d['code'], ''), d['date'], d.get('kind'), m.group(0), f['sales'] // 1_000_000, round(ratio, 2)))
rows.sort(key=lambda r: -abs(r[6] if r[6] >= 1 else 1 / max(r[6], 1e-9)))
lines = ['| コード | 社名 | 開示日 | 種別 | 要約の売上表記 | 有報の年間売上（百万円） | 比 |', '|---|---|---|---|---|---|---|']
lines += [f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]:,} | {r[6]} |' for r in rows]
txt = f'桁違いの疑い：{len(rows)} 件（要約あり {sum(1 for d in docs if d.get("summary"))} 件中）\n\n' + '\n'.join(lines)
print(txt if OUT is None else f'桁違いの疑い：{len(rows)} 件')
if OUT: open(OUT, 'w', encoding='utf-8').write(txt)

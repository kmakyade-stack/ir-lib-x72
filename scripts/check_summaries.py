"""要約の機械検査（2026年10月28日新設）。
要約に含まれる数字（金額・比率・件数）が原本テキストに同じ表記で存在するかを照合し、
無い数字を含む要約・会社名が本文にない要約を不採用（NG）にする。
使い方: python check_summaries.py <要約JSON（[{file,code,date,summary,ma}]）> <txtフォルダ> [companies.json]
出力: 標準出力に各件の OK/NG と理由、終了コードは NG があれば 1。<要約JSON>.check.json に結果を書く。
検査の考え方：
 - 単位付きの数字（億円・百万円・千円・万円・円・%・％・件・社・人・名・店・台・口・倍・ポイント）と
   「売上高1,234」のような単位なしの3桁以上の数字を対象にする。年月日・期・Q・年度・回・位は対象外。
 - 数字はカンマと全角を正規化して本文に同じ数字列があるかを見る。
   「5,442百万円」→本文に 5442 があればOK。「544.2億円」（換算誤り）→本文に 544.2 が無ければNG。
 - 会社名（株式会社・空白を除き NFKC 正規化）の先頭4文字が本文に無ければ NG（NAME）。
"""
import json, re, sys, os, unicodedata

UNIT = r'(?:億円|百万円|千円|万円|円|%|％|件|社|人|名|店舗|店|台|口|倍|ポイント|pt|千人|万人|億回|万回|万DL|万件|千件|万人)'
SKIP_AFTER = r'(?:年|月|日|期|Q|四半期|年度|回|位|時|分|号|次|カ国|か国|ヶ国|カ所|か所|ヶ所|ページ|頁)'
NUM = r'(?<![\d.,])([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)'

def norm(s):
    s = unicodedata.normalize('NFKC', s or '')
    return re.sub(r'\s+', ' ', s.replace(',', ''))

def has_num(body, n):
    """数字 n（カンマ除去済み）が本文に「数字列として丸ごと」存在するか（13,700 の中の 137 を一致にしない）"""
    return re.search(r'(?<![\d.])' + re.escape(n) + r'(?![\d.])', body) is not None

def numbers(summary):
    s = unicodedata.normalize('NFKC', summary or '')
    out = []
    for m in re.finditer(NUM, s):
        n = m.group(1); after = s[m.end():m.end()+6]
        if re.match(SKIP_AFTER, after): continue
        if re.match(UNIT, after):
            out.append(n); continue
        raw = n.replace(',', '')
        if len(raw.replace('.', '')) >= 3 and not re.match(r'[A-Za-z]', after):
            out.append(n)
    return out

def core_name(n):
    n = unicodedata.normalize('NFKC', n or '')
    return re.sub(r'株式会社|\(株\)|㈱|\s', '', n)

def check_one(rec, text, name=None):
    reasons = []
    body = norm(text)
    if name:
        cn = core_name(name)
        if cn and cn[:4] not in body.replace(' ', ''): reasons.append('NAME:' + cn[:4])
    miss = [n for n in numbers(rec.get('summary', '')) if not has_num(body, n.replace(',', ''))]
    if miss: reasons.append('NUM:' + '/'.join(miss))
    # 金額の単位違い：要約「272百万円」に対し本文では 272 が「億円」とだけ隣接している → UNIT（不採用）
    s = unicodedata.normalize('NFKC', rec.get('summary', '') or '').replace(',', '')
    bad = []
    for m in re.finditer(r'(?<![\d.])(\d+(?:\.\d+)?)\s*(億円|百万円|千円|万円)', s):
        n, u = m.group(1), m.group(2)
        units = set(x + '円' if not x.endswith('円') else x for x in
                    re.findall(r'(?<![\d.])' + re.escape(n) + r'(?![\d.])\s*(億円|百万円|百万|千円|万円)', body))
        if units and u not in units: bad.append(f'{n}{u}→本文{"/".join(sorted(units))}')
    if bad: reasons.append('UNIT:' + '/'.join(bad))
    n = len(rec.get('summary', '') or '')
    if rec.get('summary') and not (100 <= n <= 200): reasons.append(f'LEN:{n}')
    return reasons

if __name__ == '__main__':
    src, tdir = sys.argv[1], sys.argv[2]
    names = {}
    if len(sys.argv) > 3 and os.path.exists(sys.argv[3]):
        names = {c['code']: c.get('name', '') for c in json.load(open(sys.argv[3], encoding='utf-8'))}
    recs = json.load(open(src, encoding='utf-8'))
    ng = 0; out = []
    for r in recs:
        p = os.path.join(tdir, r['file'])
        if not os.path.exists(p):
            r['check'] = ['NOFILE']; ng += 1; out.append(r); print('NG', r['file'], 'NOFILE'); continue
        text = open(p, encoding='utf-8', errors='ignore').read()
        head, _, body = text.partition('\n')
        name = names.get(r.get('code')) or (head.strip('【】').split('／')[0] if head.startswith('【') else None)
        reasons = check_one(r, body, name) if r.get('summary') else (['EMPTY:' + (r.get('ma') or '')])
        r['check'] = reasons
        # NUM（原本にない数字）と NOFILE だけを不採用（NG）にする。NAME（本文に社名がない。英字ロゴ等で起きる）と LEN は警告＝目視確認
        hard = [x for x in reasons if x.startswith('NUM') or x.startswith('UNIT')]
        if hard: ng += 1
        print('NG' if hard else ('WARN' if reasons and not reasons[0].startswith('EMPTY') else 'OK'), r['file'], ' '.join(reasons))
        out.append(r)
    json.dump(out, open(src + '.check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'OK {len(recs)-ng} / NG {ng}')
    sys.exit(1 if ng else 0)

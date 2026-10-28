# -*- coding: utf-8 -*-
"""
有報（profiles.json の docID）から「沿革」だけを公式EDINET APIで取り出し、{out}/{code}.txt に保存する。
覚え方のTips（mnemonic）の根拠に使う。取得済みの社は飛ばす（途中で止めても再開できる）。

使い方: python fetch_history.py <repo> <out_dir> [--codes 4198,3799] [--reverse]
キーは環境変数 EDINET_API_KEY（値は表示しない）
"""
import os, sys, io, csv, json, time, zipfile, html, re, urllib.request, urllib.error

API = 'https://api.edinet-fsa.go.jp/api/v2'
WAIT = 1.5
ELEM = 'jpcrp_cor:CompanyHistoryTextBlock'


def clean(s):
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s))
    return re.sub(r'[ \t　]+', ' ', re.sub(r'\s*\n\s*', '\n', s)).strip()


def fetch(url):
    for attempt in range(3):
        try:
            return urllib.request.urlopen(url, timeout=180).read()
        except (urllib.error.URLError, TimeoutError) as e:
            print('retry', attempt, type(e).__name__, flush=True)
            time.sleep(10)
    return None


def main():
    repo, out = sys.argv[1], sys.argv[2]
    only = None
    if '--codes' in sys.argv:
        only = set(sys.argv[sys.argv.index('--codes') + 1].split(','))
    k = os.environ.get('EDINET_API_KEY')
    if not k:
        sys.exit('環境変数 EDINET_API_KEY がありません')
    os.makedirs(out, exist_ok=True)
    prof = json.load(open(os.path.join(repo, 'data', 'profiles.json'), encoding='utf-8'))
    ok = skip = ng = 0
    items = list(prof.items())
    if '--reverse' in sys.argv:  # 2本並行で取るときに逆順から
        items.reverse()
    for code, p in items:
        if only and code not in only:
            continue
        path = os.path.join(out, code + '.txt')
        if os.path.exists(path):
            skip += 1
            continue
        doc = p.get('docID')
        if not doc:
            ng += 1
            continue
        b = fetch(f'{API}/documents/{doc}?type=5&Subscription-Key={k}')
        time.sleep(WAIT)
        if b is None or not b.startswith(b'PK'):
            print('NG', code, doc, flush=True)
            ng += 1
            continue
        z = zipfile.ZipFile(io.BytesIO(b))
        main_csv = [n for n in z.namelist() if 'jpcrp030000-asr' in n and n.endswith('.csv')]
        text = ''
        if main_csv:
            for row in csv.reader(io.StringIO(z.read(main_csv[0]).decode('utf-16')), delimiter='\t'):
                if row and row[0] == ELEM and len(row) >= 9:
                    text = clean(row[-1])
                    break
        open(path, 'w', encoding='utf-8').write(text)
        ok += 1
        if ok % 50 == 0:
            print('progress', ok, flush=True)
    print(f'DONE 取得 {ok}・取得済み {skip}・失敗 {ng}', flush=True)


if __name__ == '__main__':
    main()

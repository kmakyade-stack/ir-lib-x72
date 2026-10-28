# -*- coding: utf-8 -*-
"""
覚え方のTips（tips_dir/*.json）を照合し、合格したものだけ data/profiles.json の mnemonic に入れる。

照合：
- kind が 由来・成り立ち のときは、evidence が その社の沿革・1行説明・事業名・社名のどれかに実在すること
  （全角半角と空白の違いは無視して照合）
- text が 80字以内、kind が 由来・成り立ち・語の意味 のどれか
null（Tipsなし）の社は mnemonic を消す。NG の社は mnemonic を入れず、一覧を出す。

使い方: python tips_merge.py <repo> <history_dir> <tips_dir> [--dry]
"""
import os, sys, json, glob, unicodedata, re

repo, hist, tips_dir = sys.argv[1:4]
dry = '--dry' in sys.argv
ppath = os.path.join(repo, 'data', 'profiles.json')
prof = json.load(open(ppath, encoding='utf-8'))
comp = {c['code']: c for c in json.load(open(os.path.join(repo, 'data', 'companies.json'), encoding='utf-8'))}


def norm(s):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s or ''))


ok = none = 0
ng = []
seen = set()
for f in sorted(glob.glob(os.path.join(tips_dir, '*.json'))):
    for r in json.load(open(f, encoding='utf-8')):
        code = r.get('code')
        if code not in prof:
            ng.append((code, '未知の証券コード', os.path.basename(f)))
            continue
        seen.add(code)
        m = r.get('mnemonic')
        if not m:
            prof[code].pop('mnemonic', None)
            none += 1
            continue
        text, kind, ev = m.get('text', ''), m.get('kind'), m.get('evidence')
        why = None
        if not text or len(text) > 80:
            why = f'text の長さ {len(text)}'
        elif kind not in ('由来', '成り立ち', '語の意味'):
            why = f'kind が不正（{kind}）'
        elif kind in ('由来', '成り立ち'):
            hp = os.path.join(hist, code + '.txt')
            src = (open(hp, encoding='utf-8').read() if os.path.exists(hp) else '')
            p, c = prof[code], comp.get(code, {})
            src += p.get('one_liner', '') + ''.join(b.get('name', '') for b in p.get('businesses', [])) + c.get('name', '') + c.get('display', '')
            if not ev or norm(ev) not in norm(src):
                why = 'evidence が原文に見つからない'
        if why:
            ng.append((code, why, text))
            prof[code].pop('mnemonic', None)
            continue
        prof[code]['mnemonic'] = {'text': text, 'kind': kind, 'basis': m.get('basis') or ''}
        ok += 1

print(f'Tipsあり {ok}社・Tipsなし {none}社・NG {len(ng)}社（照合した社 {len(seen)}）')
for x in ng:
    print('NG', *x)
if not dry:
    json.dump(prof, open(ppath, 'w', encoding='utf-8'), ensure_ascii=False)
    print('profiles.json に書き込みました')

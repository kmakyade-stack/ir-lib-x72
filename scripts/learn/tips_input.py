# -*- coding: utf-8 -*-
"""
覚え方のTips（mnemonic）を作るための入力を、1束 n 社の md にまとめる。
使い方: python tips_input.py <repo> <history_dir> <out_dir> <codes_file|all> [--per 20] [--prefix b]
"""
import os, sys, json

repo, hist, out, codes_arg = sys.argv[1:5]
per = int(sys.argv[sys.argv.index('--per') + 1]) if '--per' in sys.argv else 20
prefix = sys.argv[sys.argv.index('--prefix') + 1] if '--prefix' in sys.argv else 'b'
prof = json.load(open(os.path.join(repo, 'data', 'profiles.json'), encoding='utf-8'))
comp = {c['code']: c for c in json.load(open(os.path.join(repo, 'data', 'companies.json'), encoding='utf-8'))}
if codes_arg == 'all':
    codes = sorted(prof)
else:
    codes = [l.strip() for l in open(codes_arg, encoding='utf-8') if l.strip()]
os.makedirs(out, exist_ok=True)
batches = [codes[i:i + per] for i in range(0, len(codes), per)]
for bi, bc in enumerate(batches, 1):
    lines = []
    for code in bc:
        p, c = prof.get(code, {}), comp.get(code, {})
        hp = os.path.join(hist, code + '.txt')
        h = open(hp, encoding='utf-8').read() if os.path.exists(hp) else ''
        h = h[:3000] + ('…（以下略）' if len(h) > 3000 else '')
        lines.append(f'# {code}｜{c.get("display", "")}（正式商号：{c.get("name", "")}）')
        lines.append(f'- 1行説明：{p.get("one_liner", "")}')
        lines.append('- 事業：' + '／'.join(b.get('name', '') for b in p.get('businesses', [])))
        lines.append('- 有報の沿革：')
        lines.append(h if h else '（沿革なし）')
        lines.append('')
    name = f'{prefix}{bi:02d}.md'
    open(os.path.join(out, name), 'w', encoding='utf-8').write('\n'.join(lines))
print(f'{len(codes)}社・{len(batches)}束 → {out}')

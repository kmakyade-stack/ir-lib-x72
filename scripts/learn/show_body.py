"""検品用：本文JSONを読みやすく表示する。
使い方: python show_body.py <body_dir> <skeleton_dir> <companies.json> code1 code2 ...   （codes の代わりに --random N --type IT05 も可）
"""
import json, os, random, re, sys

body_dir, sk_dir, comp_path = sys.argv[1], sys.argv[2], sys.argv[3]
args = sys.argv[4:]
comp = {c["code"]: c for c in json.load(open(comp_path, encoding="utf-8"))}
codes = [a for a in args if not a.startswith("--") and a not in ("IT01", "IT02", "IT03", "IT04", "IT05", "IT06", "IT07", "IT08", "IT09", "IT10", "IT11")]
if "--random" in args:
    n = int(args[args.index("--random") + 1])
    t = args[args.index("--type") + 1] if "--type" in args else None
    pool = []
    for f in os.listdir(body_dir):
        if not re.fullmatch(r"[0-9A-Z]{4}\.json", f):
            continue
        c = f[:-5]
        if t:
            sk = json.load(open(os.path.join(sk_dir, c + ".json"), encoding="utf-8"))
            if sk["main_type"] != t:
                continue
        pool.append(c)
    random.seed(int(args[args.index("--seed") + 1]) if "--seed" in args else 1)
    codes = random.sample(pool, min(n, len(pool)))
for c in codes:
    p = os.path.join(body_dir, c + ".json")
    if not os.path.exists(p):
        print("==", c, "本文なし"); continue
    d = json.load(open(p, encoding="utf-8"))
    sk = json.load(open(os.path.join(sk_dir, c + ".json"), encoding="utf-8"))
    print(f"\n==== {c} {comp.get(c, {}).get('display', '')} [{sk['main_type']}]")
    print("一言:", d.get("one_liner"))
    for b in d.get("businesses", []):
        print(f"  ■ {b['name']}")
        print("    誰に:", b.get("who")); print("    何を:", b.get("what")); print("    どう:", b.get("how"))
        mf = b.get("money_flow") or {}
        pl = {x["id"]: x["label"] for x in mf.get("players", [])}
        for f in mf.get("flows", []):
            print(f"    {'¥' if f.get('kind') == 'money' else '→'} {pl.get(f.get('from'), f.get('from'))} → {pl.get(f.get('to'), f.get('to'))}: {f.get('what')}（{f.get('when')}）")
    print("  用語:", "、".join(g["term"] for g in d.get("glossary", [])))
    print("  M&A:", (d.get("ma_policy") or {}).get("text") or "記載なし", "|", (d.get("ma_policy") or {}).get("src"))
    if d.get("notes"):
        print("  notes:", d["notes"][:200])

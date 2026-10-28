"""骨格・本文の1社1ファイルJSONを data/profiles.json に統合し、fin.json を data/fin.json に写す。

使い方: python merge_profiles.py <repo> <edinet_out> <skeleton_dir> [body_dir]
"""
import datetime, json, os, sys

repo, edinet_out, sk_dir = sys.argv[1], sys.argv[2], sys.argv[3]
body_dir = sys.argv[4] if len(sys.argv) > 4 else None
today = datetime.date.today().isoformat()

comps = json.load(open(f"{repo}/data/companies.json", encoding="utf-8"))
code2ed = {c["code"]: c.get("edinet", "") for c in comps}
fin_src = json.load(open(f"{edinet_out}/fin.json", encoding="utf-8"))

# fin.json（公開用）：証券コードをキーに、円のまま
fin_out = {}
for e, f in fin_src.items():
    code = (f.get("secCode") or "")[:4]
    if not code:
        continue
    fin_out[code] = {"sales": f["sales"], "op": f["op"], "scope": f["sales_scope"], "standard": f["standard"],
                     "fy_end": f["periodEnd"], "docID": f["docID"], "url": f["url"],
                     "segments": f["segments"]}
json.dump(fin_out, open(f"{repo}/data/fin.json", "w", encoding="utf-8"), ensure_ascii=False)

ppath = f"{repo}/data/profiles.json"
profiles = json.load(open(ppath, encoding="utf-8")) if os.path.exists(ppath) else {}

n_sk = n_body = 0
for f in sorted(os.listdir(sk_dir)):
    if not f.endswith(".json"):
        continue
    sk = json.load(open(os.path.join(sk_dir, f), encoding="utf-8"))
    code = sk["code"]
    e = code2ed.get(code, "")
    rec = profiles.get(code, {})
    rec.update({"code": code, "edinet": e, "docID": fin_src.get(e, {}).get("docID", ""), "fy_end": fin_src.get(e, {}).get("periodEnd", ""),
                "main_type": sk["main_type"], "sub_type": sk.get("sub_type"), "non_it": sk["non_it"]})
    # 事業は骨格を正とし、既存の本文（who 等）が同じ事業名にあれば引き継ぐ
    old = {b["name"]: b for b in rec.get("businesses", [])}
    bs = []
    for b in sk["businesses"]:
        nb = {k: b.get(k) for k in ("name", "entity", "segment_member", "share_pct", "share_src", "type", "customer", "vertical", "pricing")}
        o = old.get(b["name"], {})
        for k in ("who", "what", "how", "money_flow", "sources"):
            if k in o:
                nb[k] = o[k]
        bs.append(nb)
    rec["businesses"] = bs
    rec.setdefault("status", {})["skeleton"] = "done"
    rec.setdefault("generated", {})["skeleton"] = today
    rec.setdefault("model", "sonnet")
    rec.setdefault("status", {}).setdefault("body", "pending")
    if sk.get("notes"):
        rec["skeleton_notes"] = sk["notes"]
    profiles[code] = rec
    n_sk += 1

if body_dir and os.path.isdir(body_dir):
    for f in sorted(os.listdir(body_dir)):
        if not f.endswith(".json"):
            continue
        bd = json.load(open(os.path.join(body_dir, f), encoding="utf-8"))
        code = bd["code"]
        rec = profiles.get(code)
        if not rec:
            continue
        rec["one_liner"] = bd.get("one_liner", "")
        rec["glossary"] = bd.get("glossary", [])
        rec["ma_policy"] = bd.get("ma_policy", {"text": "", "src": ""})
        bmap = {b["name"]: b for b in bd.get("businesses", [])}
        for b in rec["businesses"]:
            src = bmap.get(b["name"])
            if src:
                for k in ("who", "what", "how", "money_flow", "sources"):
                    b[k] = src.get(k)
        rec["status"]["body"] = "done" if all(b.get("who") for b in rec["businesses"]) else "partial"
        rec["generated"]["body"] = today
        n_body += 1

json.dump(profiles, open(ppath, "w", encoding="utf-8"), ensure_ascii=False)
print(f"profiles: {len(profiles)}社（骨格 {n_sk}・本文 {n_body}）／fin: {len(fin_out)}社")

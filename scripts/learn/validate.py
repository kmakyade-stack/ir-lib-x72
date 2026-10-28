"""骨格・本文JSONの機械検査。

使い方: python validate.py skeleton <dir> [--fin fin.json]   … {code}.json を全件検査し、結果を標準出力とNGの一覧（validate_ng.txt）に出す
        python validate.py body <dir>
"""
import json, os, re, sys

TYPES = {f"IT{i:02d}" for i in range(1, 12)}
CUSTOMER = {"大企業", "中小企業", "個人", "官公庁・公共"}
PRICING = {"月額", "従量", "人月・稼働", "成果報酬・手数料", "売り切り・請負", "広告"}
GYOSHU = {"飲食業", "小売業", "卸売業", "建設業", "製造業", "運送業", "サービス業", "医療業", "介護業", "宿泊業"}


def ok_type(t):
    if t in TYPES:
        return True
    m = re.fullmatch(r"非IT-(.+)", t or "")
    if not m:
        return False
    g = m.group(1)
    return g in GYOSHU or re.fullmatch(r"その他（.+）", g) is not None


def check_skeleton(d, fin=None):
    errs = []
    if not re.fullmatch(r"[0-9A-Z]{4}", str(d.get("code", ""))):
        errs.append("code")
    bs = d.get("businesses")
    if not isinstance(bs, list) or not 1 <= len(bs) <= 8:
        errs.append("businesses 1〜8件")
        bs = bs if isinstance(bs, list) else []
    if not ok_type(d.get("main_type")):
        errs.append(f"main_type={d.get('main_type')}")
    if d.get("sub_type") is not None and not ok_type(d.get("sub_type")):
        errs.append(f"sub_type={d.get('sub_type')}")
    if d.get("non_it") != str(d.get("main_type", "")).startswith("非IT-"):
        errs.append("non_it と main_type の不一致")
    types = [b.get("type") for b in bs]
    if d.get("main_type") not in types:
        errs.append("main_type が businesses に無い")
    shares = []
    for i, b in enumerate(bs):
        p = f"businesses[{i}]"
        if not b.get("name"):
            errs.append(p + ".name")
        if not b.get("entity"):
            errs.append(p + ".entity")
        if not ok_type(b.get("type")):
            errs.append(f"{p}.type={b.get('type')}")
        cu = b.get("customer")
        if not isinstance(cu, list) or not cu or not set(cu) <= CUSTOMER:
            errs.append(f"{p}.customer={cu}")
        pr = b.get("pricing")
        if not isinstance(pr, list) or not pr or not set(pr) <= PRICING:
            errs.append(f"{p}.pricing={pr}")
        if "vertical" not in b or not isinstance(b.get("vertical"), str):
            errs.append(p + ".vertical")
        sp = b.get("share_pct")
        if sp is not None:
            if not isinstance(sp, (int, float)) or not 0 <= sp <= 100.5:
                errs.append(f"{p}.share_pct={sp}")
            else:
                shares.append(sp)
            if b.get("share_src") not in ("有報セグメント情報", "本文の記載"):
                errs.append(f"{p}.share_src={b.get('share_src')}")
        if fin is not None and b.get("segment_member"):
            segs = fin.get("segments", {}) if fin else {}
            if b["segment_member"] not in segs:
                errs.append(f"{p}.segment_member が fin に無い")
    if shares and sum(shares) > 115:
        errs.append(f"share_pct 合計 {sum(shares):.1f}")
    return errs


def check_body(d):
    errs = []
    if not d.get("one_liner") or len(d["one_liner"]) > 80:
        errs.append("one_liner（80字以内）")
    for i, b in enumerate(d.get("businesses", [])):
        p = f"businesses[{i}]"
        for k in ("who", "what", "how"):
            v = b.get(k, "")
            if not 20 <= len(v) <= 200:
                errs.append(f"{p}.{k} 字数{len(v)}")
        mf = b.get("money_flow") or {}
        pl, fl = mf.get("players"), mf.get("flows")
        if not isinstance(pl, list) or len(pl) < 2:
            errs.append(p + ".money_flow.players")
        if not isinstance(fl, list) or not fl:
            errs.append(p + ".money_flow.flows")
        else:
            ids = {x.get("id") for x in pl or []}
            for f in fl:
                if f.get("from") not in ids or f.get("to") not in ids or f.get("kind") not in ("money", "value"):
                    errs.append(p + ".money_flow.flows の参照")
                    break
            if not any(f.get("kind") == "money" for f in fl):
                errs.append(p + ".money_flow にお金の矢印が無い")
        if not b.get("sources"):
            errs.append(p + ".sources")
    g = d.get("glossary")
    if not isinstance(g, list) or not 1 <= len(g) <= 12 or any(not x.get("term") or not x.get("plain") for x in g):
        errs.append("glossary 1〜12語・term/plain")
    mp = d.get("ma_policy")
    if not isinstance(mp, dict) or "text" not in mp or "src" not in mp:
        errs.append("ma_policy")
    return errs


def main():
    mode, d = sys.argv[1], sys.argv[2]
    fin = None
    if "--fin" in sys.argv:
        fin = json.load(open(sys.argv[sys.argv.index("--fin") + 1], encoding="utf-8"))
    ng, n = [], 0
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        n += 1
        try:
            j = json.load(open(os.path.join(d, f), encoding="utf-8"))
        except Exception as e:
            ng.append((f, [f"JSONとして読めない: {e}"]))
            continue
        if mode == "skeleton":
            fe = None
            if fin:
                # fin は EDINETコードがキー。code→edinet の対応は呼び出し側で companies.json を使う
                fe = fin.get(j.get("_edinet", ""), None)
            errs = check_skeleton(j, fe)
        else:
            errs = check_body(j)
        if errs:
            ng.append((f, errs))
    with open(os.path.join(d, "validate_ng.txt"), "w", encoding="utf-8") as fo:
        for f, errs in ng:
            fo.write(f"{f}\t{'；'.join(errs)}\n")
    print(f"{mode}: {n}件中 NG {len(ng)}件 → {os.path.join(d, 'validate_ng.txt')}")
    for f, errs in ng[:30]:
        print(" ", f, "；".join(errs)[:200])


if __name__ == "__main__":
    main()

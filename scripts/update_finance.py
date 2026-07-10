"""時価総額の全社更新（毎日）＋売上の更新（新しい決算があった社のみ検出は省略し全社上書き可）。
使い方: python3 update_finance.py <repoパス> [mode=mcap|full] [budget秒]"""
import json, sys, time, warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore")
import yfinance as yf

REPO = sys.argv[1]
MODE = sys.argv[2] if len(sys.argv) > 2 else "mcap"
BUDGET = int(sys.argv[3]) if len(sys.argv) > 3 else 25
comps = json.load(open(f"{REPO}/data/companies.json"))
fin = json.load(open(f"{REPO}/data/finance.json"))
prog_key = "_progress_" + MODE
start_idx = fin.get(prog_key, 0)
start = time.time()

def fetch(c):
    code = c["code"]
    rec = fin.get(code, {"mcap": None, "rev": None, "fy": ""})
    try:
        t = yf.Ticker(code + ".T")
        m = t.fast_info.get("marketCap")
        if m: rec["mcap"] = m
        if MODE == "full":
            st = t.income_stmt
            if st is not None and "Total Revenue" in st.index:
                for col in st.columns:
                    v = st.loc["Total Revenue", col]
                    if v == v and v is not None:
                        rec["rev"] = float(v); rec["fy"] = str(col)[:7]; break
    except Exception: pass
    return code, rec

i = start_idx
while i < len(comps) and time.time() - start < BUDGET:
    batch = comps[i:i+12]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for code, rec in ex.map(fetch, batch):
            fin[code] = rec
    i += len(batch)
fin[prog_key] = 0 if i >= len(comps) else i
json.dump(fin, open(f"{REPO}/data/finance.json", "w"))
print(("DONE" if i >= len(comps) else f"PARTIAL@{i}"), MODE)

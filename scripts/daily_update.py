"""日次更新：新着開示の取込＋PDF保存＋時価総額更新。
使い方: python3 daily_update.py <repoパス> [days=4]
要約はこのスクリプトでは行わない（Claudeが別途実施）。"""
import json, re, sys, time, os, base64, urllib.request
from datetime import date, timedelta

REPO = sys.argv[1]
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 4
KW = re.compile(r"中期経営計画|中期計画|中計(?!画)|決算説明|成長可能性|事業計画及び成長")
EXCLUDE = re.compile(r"訂正|延期|開催|動画|書き起こし|質疑応答")
KW2 = re.compile(r"株式取得|株式の取得|子会社化|株式譲受|事業譲受|吸収合併|合併契約|株式交換|株式移転|資本業務提携|公開買付|買収|株式譲渡|事業譲渡|持分取得|グループ化")
EX2 = re.compile(r"自己株式|自社株|譲渡制限付|ストック・?オプション|新株予約権|訂正|進捗|買付け?の?結果|決済の開始|変更|終了|完了の?お知らせに関する|質疑")
import html as _html
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def kind(t):
    if "成長可能性" in t or "事業計画及び成長" in t: return "成長可能性"
    if "中期" in t or "中計" in t: return "中期経営計画"
    return "決算説明資料"

def get(url, timeout=30):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

comps = json.load(open(f"{REPO}/data/companies.json"))
codes = {c["code"] for c in comps}
docs = json.load(open(f"{REPO}/data/documents.json"))
seen = {(d["code"], d["url"]) for d in docs}
cfg = json.load(open(f"{REPO}/../.secrets/github.json")) if os.path.exists(f"{REPO}/../.secrets/github.json") else None

new = []
for i in range(DAYS):
    day = (date.today() - timedelta(days=i)).strftime("%Y%m%d")
    try:
        data = json.loads(get(f"https://webapi.yanoshin.jp/webapi/tdnet/list/{day}.json?limit=3000"))
    except Exception as e:
        print("day NG", day, str(e)[:60]); continue
    for it in data.get("items", []):
        t = it["Tdnet"]
        code = t["company_code"][:4]
        title = t["title"]
        if code not in codes: continue
        url = (t.get("document_url") or "").replace("https://webapi.yanoshin.jp/rd.php?", "")
        if (code, url) in seen: continue
        title_u = _html.unescape(title)
        if KW.search(title) and not EXCLUDE.search(title):
            new.append({"code": code, "date": t["pubdate"][:10], "title": title_u,
                        "kind": kind(title), "url": url, "summary": ""})
            seen.add((code, url))
        elif KW2.search(title) and not EX2.search(title):
            new.append({"code": code, "date": t["pubdate"][:10], "title": title_u,
                        "kind": "M&A開示", "url": url, "summary": "", "ma": title_u})
            seen.add((code, url))
    time.sleep(0.5)

# 中計・成長可能性はReleasesへ永続保存
if cfg:
    TOK = base64.b64decode(cfg["token_b64"]).decode()
    OWNER, REPONAME = cfg["owner"], cfg["repo"]
    rel = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPONAME}/releases/tags/pdf-archive",
        headers={"Authorization": f"Bearer {TOK}"}), timeout=30).read())["id"]
    for d in new:
        if d["kind"] not in ("中期経営計画", "成長可能性"): continue
        try:
            pdf = get(d["url"], timeout=60)
            if not pdf.startswith(b"%PDF"): continue
            fn = d["url"].rsplit("/", 1)[-1]
            req = urllib.request.Request(
                f"https://uploads.github.com/repos/{OWNER}/{REPONAME}/releases/{rel}/assets?name={fn}",
                data=pdf, method="POST",
                headers={"Authorization": f"Bearer {TOK}", "Content-Type": "application/pdf"})
            try:
                r = json.loads(urllib.request.urlopen(req, timeout=120).read())
                d["archive"] = r["browser_download_url"]
            except urllib.error.HTTPError as e:
                if e.code == 422:
                    d["archive"] = f"https://github.com/{OWNER}/{REPONAME}/releases/download/pdf-archive/{fn}"
            time.sleep(0.3)
        except Exception as e:
            print("pdf NG", d["title"][:30], str(e)[:50])

docs = new + docs
docs.sort(key=lambda x: x["date"], reverse=True)
json.dump(docs, open(f"{REPO}/data/documents.json", "w"), ensure_ascii=False, indent=1)
print(f"新着 {len(new)} 件追加 → 合計 {len(docs)} 件")
for d in new: print(" +", d["date"], d["kind"], d["title"][:50])

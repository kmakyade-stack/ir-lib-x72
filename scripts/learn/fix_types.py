"""骨格の区分を、learn ページの境界ルール（prompts/skeleton.md「追加の境界ルール」）に合わせて直す。

使い方: python fix_types.py <skeleton_dir>
  - 対象の事業（会社コード＋事業名の一部）を新しい区分に付け替え、main_type／sub_type／non_it を売上構成比から計算し直す
  - 比率が無い社は、付け替えた事業が main_type だった場合だけ main_type を更新する
"""
import json, os, sys

RULES = [
    # (code, 事業名に含まれる語, 新しい区分)
    ("2317", "ビジネスソリューション", "IT07"), ("2334", "AIデータセンター", "IT07"), ("3968", "ソリューションプロダクト", "IT07"),
    ("4015", "デジタルサイネージ", "IT07"), ("4288", "ネットワークセキュリティ", "IT07"), ("4341", "情報通信システム", "IT07"),
    ("4429", "テクノロジーソリューション", "IT07"), ("4434", "リセール", "IT07"), ("5036", "ライセンス", "IT07"),
    ("5133", "ネットワーク・セキュリティ", "IT07"), ("6597", "HPC事業", "IT07"), ("7595", "PLM", "IT07"),
    ("3817", "販売事業", "IT07"), ("5026", "GPUサーバー", "IT07"), ("5129", "リセール", "IT07"), ("9889", "システム", "IT07"),
    ("3678", "電子書籍流通", "IT09"), ("4051", "決済", "IT09"), ("4819", "決済", "IT09"), ("3691", "ギフト", "IT09"),
    ("3807", "情報サービス", "IT09"), ("4171", "市場調査", "IT09"), ("336A", "地図", "IT05"), ("290A", "衛星", "IT05"),
]


def recompute(d):
    bs = d["businesses"]
    known = [b for b in bs if b.get("share_pct") is not None]
    if known:
        top = max(known, key=lambda b: b["share_pct"])
        d["main_type"] = top["type"]
        rest = [b for b in known if b is not top and b["share_pct"] >= 20 and b["type"] != top["type"]]
        d["sub_type"] = max(rest, key=lambda b: b["share_pct"])["type"] if rest else None
    d["non_it"] = str(d["main_type"]).startswith("非IT-")


def main():
    sk_dir = sys.argv[1]
    n_changed, missed = 0, []
    for code, key, new in RULES:
        p = os.path.join(sk_dir, code + ".json")
        if not os.path.exists(p):
            missed.append((code, key, "ファイルなし")); continue
        d = json.load(open(p, encoding="utf-8"))
        hit = [b for b in d["businesses"] if key in b["name"]]
        if not hit:
            missed.append((code, key, "事業名が一致しない")); continue
        for b in hit:
            if b["type"] != new:
                old = b["type"]; b["type"] = new; n_changed += 1
                d["notes"] = (d.get("notes") or "") + f"／fix_types: 「{b['name'][:20]}」{old}→{new}（IT商材の販売＋構築・運用・決済基盤・データ配信はITに含める）"
        before = (d["main_type"], d["sub_type"], d["non_it"])
        if d["main_type"] not in {b["type"] for b in d["businesses"]} or any(b in hit for b in d["businesses"] if b["type"] == new):
            recompute(d)
            if not any(b.get("share_pct") is not None for b in d["businesses"]) and before[0] not in {b["type"] for b in d["businesses"]}:
                d["main_type"] = new; d["non_it"] = new.startswith("非IT-")
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("付け替え:", n_changed, "件／一致せず:", missed)


if __name__ == "__main__":
    main()

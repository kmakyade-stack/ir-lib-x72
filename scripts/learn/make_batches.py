"""骨格・本文の生成を n 社ずつの束に分け、束ごとのファイル一覧（manifest）を書く。

使い方: python make_batches.py <in_dir> <out_dir> <batches_dir> [n=10] [--only codes.txt] [--skip-done]
  <in_dir>      build_inputs.py の出力（{code}.md）
  <out_dir>     生成物の置き場（{code}.json）。--skip-done で既にあるものを除く
  <batches_dir> 束ごとの一覧 batch_001.txt … を書く
"""
import os, sys

in_dir, out_dir, batches_dir = sys.argv[1], sys.argv[2], sys.argv[3]
n = 10
only = None
skip_done = "--skip-done" in sys.argv
for i, a in enumerate(sys.argv[4:], 4):
    if a.isdigit():
        n = int(a)
    if a == "--only":
        only = {l.strip().split("\t")[0] for l in open(sys.argv[i + 1], encoding="utf-8") if l.strip()}
os.makedirs(batches_dir, exist_ok=True)
for f in os.listdir(batches_dir):
    if f.startswith("batch_"):
        os.remove(os.path.join(batches_dir, f))
codes = sorted(f[:-3] for f in os.listdir(in_dir) if f.endswith(".md"))
if only is not None:
    codes = [c for c in codes if c in only]
if skip_done:
    codes = [c for c in codes if not os.path.exists(os.path.join(out_dir, c + ".json"))]
k = 0
for i in range(0, len(codes), n):
    k += 1
    with open(os.path.join(batches_dir, f"batch_{k:03d}.txt"), "w", encoding="utf-8") as fo:
        fo.write("\n".join(codes[i:i + n]) + "\n")
print(f"{len(codes)}社 → {k}束（{n}社ずつ）")

import json, sys
path = "docs/data/v1/tools/pps/shk_pairs.json"
b = json.load(open(path, "r", encoding="utf-8"))
print("Stats:", b["stats"])
print("Default trans:", b["defaultTrans"])
# show 3 example X keys and their counts
for i,k in enumerate(list(b["index"]["x"].keys())[:3], 1):
    print(f"X[{i}]: {k} -> {len(b['index']['x'][k])} pairs")
# print first entry + first pair preview
e = b["entries"][0]
p = e["pairs"][0]
print("\nSample:", e["ref"], "—", p["x"]["key"], "→", p["y"]["key"])
print("X roots:", p["x"]["roots"])
print("Y roots:", p["y"]["roots"])

import csv, json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
keys={}
with open("vp116_keys.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        keys[int(r["idx"])]={"id":r["id"],"subj":r["subj"],"exam":r["exam"],"key":r["key"].strip().upper()}
res=json.load(open(sys.argv[1], encoding="utf-8"))
items=res["results"] if isinstance(res,dict) else res
conf=wrong=unsolv=0; confirmed_ids=[]; disagree=[]; by=collections.defaultdict(lambda:[0,0,0])
for it in items:
    i=it["idx"]; maj=str(it.get("majority","")).upper(); k=keys[i]["key"]; grp=f'{keys[i]["exam"]}-{keys[i]["subj"]}'
    if maj=="UNSOLVABLE": unsolv+=1; by[grp][2]+=1
    elif maj==k: conf+=1; by[grp][0]+=1; confirmed_ids.append(keys[i]["id"])
    else: wrong+=1; by[grp][1]+=1; disagree.append((i,grp,maj,k,it.get("answers"),keys[i]["id"]))
solv=conf+wrong; prec=100*conf/solv if solv else 0
print(f"=== VP116 STATUS VALIDATION (n={len(items)}) ===")
print(f"CONFIRMED={conf}  WRONG={wrong}  UNSOLVABLE={unsolv}  PRECISION={prec:.1f}% [{conf}/{solv}]  unanimous={res.get('unanimous','?')}")
print("--- per subject (conf/wrong/unsolv) ---")
for g in sorted(by): c,w,u=by[g]; print(f"  {g}: {c}/{w}/{u}")
print("--- disagreements ---")
for d in disagree: print(f"  #{d[0]} {d[1]}: maj={d[2]} key={d[3]} all={d[4]} {d[5]}")
Path("vp116_confirmed_ids.json").write_text(json.dumps(confirmed_ids), encoding="utf-8")
print(f"\nvp116_confirmed_ids.json yazildi ({len(confirmed_ids)})")

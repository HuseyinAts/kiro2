import csv, json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

keys={}
with open("tier1_keys.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        keys[int(r["idx"])]={"id":r["id"],"subj":r["subj"],"exam":r["exam"],"key":r["key"].strip().upper()}

res=json.load(open(sys.argv[1], encoding="utf-8"))
items=res["results"] if isinstance(res,dict) else res

conf=wrong=unsolv=split=0
by_subj=collections.defaultdict(lambda:[0,0,0])  # confirmed, wrong, unsolvable
disagree=[]
for it in items:
    i=it["idx"]; maj=str(it.get("majority","")).upper(); k=keys[i]["key"]
    grp=f'{keys[i]["exam"]}-{keys[i]["subj"]}'
    if maj=="UNSOLVABLE":
        unsolv+=1; by_subj[grp][2]+=1
    elif maj==k:
        conf+=1; by_subj[grp][0]+=1
    else:
        wrong+=1; by_subj[grp][1]+=1
        disagree.append((i,grp,maj,k,it.get("answers"),keys[i]["id"]))
    if it.get("agree",3)<2: split+=1

solvable=conf+wrong
prec=100*conf/solvable if solvable else 0
print(f"=== TIER1 BLIND VALIDATION (n={len(items)}) ===")
print(f"CONFIRMED (majority==key) = {conf}")
print(f"WRONG (majority!=key)     = {wrong}")
print(f"UNSOLVABLE (needs figure) = {unsolv}")
print(f"PRECISION (solvable)      = {prec:.1f}%  [{conf}/{solvable}]")
print(f"3-way unanimous           = {res.get('unanimous','?') if isinstance(res,dict) else '?'}")
print("\n--- per subject (confirmed / wrong / unsolvable) ---")
for g in sorted(by_subj):
    c,w,u=by_subj[g]
    p=100*c/(c+w) if (c+w) else 0
    print(f"  {g}: {c}/{w}/{u}  prec={p:.0f}%")
print("\n--- WRONG/disagreements (idx, grp, majority, key, all3, id) ---")
for d in disagree:
    print(f"  #{d[0]} {d[1]}: maj={d[2]} key={d[3]} all={d[4]} {d[5]}")

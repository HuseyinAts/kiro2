import importlib, sys
sys.path.insert(0, '/app')
from routers.loader import ROUTER_MAPPING

loaded, failed, no_router = [], [], []
for old, (cat, mod) in ROUTER_MAPPING.items():
    try:
        m = importlib.import_module(mod)
        if hasattr(m, 'router'):
            loaded.append(mod)
        else:
            no_router.append(mod)
    except Exception as e:
        failed.append((mod, str(e)[:100]))

print(f'LOADED: {len(loaded)}')
print(f'NO_ROUTER: {len(no_router)}')
print(f'FAILED: {len(failed)}')
print('--- FAILED LIST ---')
for m, e in failed:
    print(f'  {m}: {e}')
print('--- NO_ROUTER ---')
for m in no_router:
    print(f'  {m}')

import traceback, importlib
try:
    importlib.import_module("api.ocr_api")
    print("OK")
except Exception as e:
    traceback.print_exc()

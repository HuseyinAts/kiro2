"""
Export OpenAPI schema from FastAPI app to JSON file
This script generates openapi.json for TypeScript type generation
"""
import json
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

try:
    from fastapi.openapi.utils import get_openapi

    from main import app

    # Generate OpenAPI schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Export to JSON file
    output_path = backend_path / "openapi.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"[OK] OpenAPI schema exported successfully to: {output_path}")
    print(f"[INFO] Total paths: {len(schema.get('paths', {}))}")
    print(f"[INFO] Total schemas: {len(schema.get('components', {}).get('schemas', {}))}")

except Exception as e:
    print(f"[ERROR] Error exporting OpenAPI schema: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

import json
from app.main import app

def export():
    openapi_schema = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported openapi.json")

if __name__ == "__main__":
    export()

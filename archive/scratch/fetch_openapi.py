import json
from app.main import app

def generate_openapi():
    schema = app.openapi()
    print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    generate_openapi()

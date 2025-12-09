import sys
import json
import os

# Add the parent directory to sys.path to find the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

with open("openapi-fastapi.json", "w") as f:
    json.dump(app.openapi(), f)
    
print("✅ OpenAPI spec exported to openapi-fastapi.json")
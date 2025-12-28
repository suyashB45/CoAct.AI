import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

print("--- REGISTERED ROUTES ---")
print(app.url_map)
print("-------------------------")

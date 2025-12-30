# agent_tools/genai_client.py

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 1) Load environment variables from .env in the project root
# Get the project root (parent of agent_tools directory)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# 2) Read GEMINIAPIKEY from environment
GEMINIAPIKEY = os.getenv("GEMINIAPIKEY")
if not GEMINIAPIKEY:
    print(f"ERROR: GEMINIAPIKEY not found in .env file")
    print(f"Expected .env file at: {env_path}")
    if env_path.exists():
        print(f".env file exists but GEMINIAPIKEY not found in it")
        with open(env_path, 'r') as f:
            content = f.read()
            print(f"File contents: {repr(content[:200])}")
    else:
        print(f".env file does not exist at that path")
    sys.exit(1)

# 3) Create a shared API-key client
client = genai.Client(api_key=GEMINIAPIKEY)

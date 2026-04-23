import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val

GREEN_API_URL = _require("GREEN_API_URL")
GREEN_API_INSTANCE = _require("GREEN_API_INSTANCE")
GREEN_API_TOKEN = _require("GREEN_API_TOKEN")

LLM_PROVIDER = _require("LLM_PROVIDER")
LLM_MODEL = _require("LLM_MODEL")

if LLM_PROVIDER == "anthropic":
    API_KEY = _require("ANTHROPIC_API_KEY")
elif LLM_PROVIDER == "openai":
    API_KEY = _require("OPENAI_API_KEY")
elif LLM_PROVIDER == "google":
    API_KEY = _require("GOOGLE_API_KEY")
else:
    raise RuntimeError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/conversations.db")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

_spec_path = Path(__file__).parent / "spec.json"
with open(_spec_path, encoding="utf-8") as f:
    SPEC = json.load(f)

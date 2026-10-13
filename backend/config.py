
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def get_index_path() -> Path:
    configured = Path(
        os.getenv("FAISS_INDEX_PATH", "indexes/faiss")
    )
    if not configured.is_absolute():
        configured = ROOT / configured
    return configured.resolve()


INDEX_PATH = get_index_path()
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)
TRUST_LOCAL_INDEX = (
    os.getenv("TRUST_LOCAL_INDEX", "false").lower()
    == "true"
)
EMBEDDING_CONFIG_VERIFIED = (
    os.getenv("EMBEDDING_CONFIG_VERIFIED", "false")
    .lower() == "true"
)

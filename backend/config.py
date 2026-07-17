"""Central configuration. All tunables live here, sourced from .env."""
import os
import pathlib

from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(key: str, default: str = "false") -> bool:
    return os.getenv(key, default).strip().lower() in {"1", "true", "yes", "on"}


# --- Paths -----------------------------------------------------------------
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTORSTORE_DIR = BASE_DIR / "backend" / "vectorstore" / "index"

# --- LLM -------------------------------------------------------------------
# Provider: groq | openai | gemini | ollama | mock
# "mock" needs no API key and no network. The whole app runs end to end on it,
# which is what makes the test suite runnable in CI and on a laptop on a train.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").strip().lower()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "700"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
    "ollama": "llama3",
    "mock": "mock-llm",
}

# --- Embeddings / RAG ------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))          # characters
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))    # characters
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
# Cosine similarity below this and we treat retrieval as a miss -> escalate
# rather than let the LLM improvise. Tune with: python -m backend.eval.run_eval
RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.25"))

# --- Database --------------------------------------------------------------
# If Mongo is unreachable we fall back to an in-memory store so the app still
# boots. Fine for the demo; the fallback is logged loudly at startup.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "techmart_support")

# --- Auth ------------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "1440"))

# --- App -------------------------------------------------------------------
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:3000"
).split(",") if o.strip()]
MEMORY_TURNS = int(os.getenv("MEMORY_TURNS", "6"))  # prior turns fed to the LLM


def active_model() -> str:
    return LLM_MODEL or DEFAULT_MODELS.get(LLM_PROVIDER, "mock-llm")

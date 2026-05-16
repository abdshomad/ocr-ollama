import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").strip().lower()
DEFAULT_VLLM_HOST = os.getenv("VLLM_HOST", "http://localhost:8100").rstrip("/")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT / "upload"))
RESULT_DIR = Path(os.getenv("RESULT_DIR", ROOT / "result"))
SAMPLE_IMAGES_DIR = Path(os.getenv("SAMPLE_IMAGES_DIR", ROOT / "SAMPLES" / "IMAGES"))
PROMPTS_PATH = Path(__file__).resolve().parents[1] / "config" / "prompts.json"
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", 10 * 1024 * 1024))
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_OCR_UPLOAD_TYPES = ALLOWED_CONTENT_TYPES | {"application/pdf"}
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
VLLM_TIMEOUT = float(os.getenv("VLLM_TIMEOUT", "600"))
# Probes for /api/models listing (per-host /v1/models). Too low marks healthy vLLM as offline when the API is slow.
MODEL_LIST_HTTP_TIMEOUT = float(os.getenv("MODEL_LIST_HTTP_TIMEOUT", "30"))
# Output cap only; model ctx is 8192 and the image consumes most of it.
VLLM_MAX_TOKENS = int(os.getenv("VLLM_MAX_TOKENS", "2048"))
VLLM_MODEL = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-OCR")
# OCR model for text-only tier product extraction (two-step pipeline)
DEFAULT_OCR_MODEL = os.getenv("DEFAULT_OCR_MODEL", VLLM_MODEL).strip()
# glm-ocr defaults to 131072 ctx; Ollama 0.23.x CUDA load can abort (ggml_nbytes > INT_MAX).
OCR_NUM_CTX = int(os.getenv("OCR_NUM_CTX", "8192"))
VLLM_XARGS = {
    "ngram_size": int(os.getenv("VLLM_XARGS_NGRAM_SIZE", "30")),
    "window_size": int(os.getenv("VLLM_XARGS_WINDOW_SIZE", "90")),
    "whitelist_token_ids": [128821, 128822],
}


def cors_allow_origins() -> list[str]:
    """Origins allowed for credentialed browser API calls (dev server + split hosting)."""
    raw = os.getenv("CORS_ALLOW_ORIGINS")
    if raw is None:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [o.strip() for o in raw.split(",") if o.strip()]


def cors_allow_origin_regex() -> str | None:
    """Optional regex (e.g. https://.*\\.example\\.com) merged with CORS_ALLOW_ORIGINS."""
    v = os.getenv("CORS_ALLOW_ORIGIN_REGEX", "").strip()
    return v or None

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

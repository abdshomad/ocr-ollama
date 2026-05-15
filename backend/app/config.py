import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INFERENCE_BACKEND = os.getenv("INFERENCE_BACKEND", "vllm").strip().lower()
DEFAULT_VLLM_HOST = os.getenv("VLLM_HOST", "http://localhost:8100").rstrip("/")
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT / "upload"))
RESULT_DIR = Path(os.getenv("RESULT_DIR", ROOT / "result"))
PROMPTS_PATH = Path(__file__).resolve().parents[1] / "config" / "prompts.json"
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", 10 * 1024 * 1024))
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
VLLM_TIMEOUT = float(os.getenv("VLLM_TIMEOUT", "600"))
# Output cap only; model ctx is 8192 and the image consumes most of it.
VLLM_MAX_TOKENS = int(os.getenv("VLLM_MAX_TOKENS", "2048"))
VLLM_MODEL = os.getenv("VLLM_MODEL", "deepseek-ai/DeepSeek-OCR")
# glm-ocr defaults to 131072 ctx; Ollama 0.23.x CUDA load can abort (ggml_nbytes > INT_MAX).
OCR_NUM_CTX = int(os.getenv("OCR_NUM_CTX", "8192"))
VLLM_XARGS = {
    "ngram_size": int(os.getenv("VLLM_XARGS_NGRAM_SIZE", "30")),
    "window_size": int(os.getenv("VLLM_XARGS_WINDOW_SIZE", "90")),
    "whitelist_token_ids": [128821, 128822],
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

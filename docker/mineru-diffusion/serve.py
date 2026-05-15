#!/usr/bin/env python3
"""HTTP sidecar for MinerU-Diffusion nano_dvlm inference."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

REPO_DIR = Path(os.getenv("MINERU_REPO_DIR", "/opt/MinerU-Diffusion"))
NANO_DIR = REPO_DIR / "engines" / "nano_dvlm"
if str(NANO_DIR) not in sys.path:
    sys.path.insert(0, str(NANO_DIR))

from nanovllm import LLM, SamplingParams  # noqa: E402


def _patch_nanovllm_eager_warmup() -> None:
    """Skip inductor/triton warmup when enforce_eager (runtime image has no CUDA dev libs)."""
    if not _enforce_eager:
        return
    import nanovllm.engine.model_runner as model_runner

    if getattr(model_runner.ModelRunner.warmup_model, "_ocr_skip_patch", False):
        return

    _orig_warmup = model_runner.ModelRunner.warmup_model

    def _warmup_model(self):  # type: ignore[no-untyped-def]
        if getattr(self, "enforce_eager", False):
            torch.cuda.empty_cache()
            return
        return _orig_warmup(self)

    _warmup_model._ocr_skip_patch = True  # type: ignore[attr-defined]
    model_runner.ModelRunner.warmup_model = _warmup_model  # type: ignore[method-assign]

STOP_STRINGS = ("<|endoftext|>", "<|im_end|>")
SYSTEM_PROMPT = "You are a helpful assistant."
DEFAULT_MODEL_ID = "opendatalab/MinerU-Diffusion-V1-0320-2.5B"

_llm: LLM | None = None
_model_id = os.getenv("MINERU_MODEL_ID", DEFAULT_MODEL_ID).strip()
_model_path = os.getenv("MODEL_PATH", _model_id).strip()
_port = int(os.getenv("MINERU_PORT", "8200"))
_gen_length = int(os.getenv("MINERU_GEN_LENGTH", "1024"))
_block_size = int(os.getenv("MINERU_BLOCK_SIZE", "32"))
_max_length = int(os.getenv("MINERU_MAX_LENGTH", "4096"))
_gpu_mem = float(os.getenv("MINERU_GPU_MEMORY_UTILIZATION", "0.8"))
_dynamic_threshold = float(os.getenv("MINERU_DYNAMIC_THRESHOLD", "0.95"))
_remask = os.getenv("MINERU_REMASK_STRATEGY", "low_confidence_dynamic")
_enforce_eager = os.getenv("MINERU_ENFORCE_EAGER", "1").lower() in ("1", "true", "yes")


def _resolve_model_dir() -> Path:
    path = Path(_model_path)
    if path.is_dir():
        return path.resolve()
    try:
        from huggingface_hub import snapshot_download

        cache = os.getenv("HF_HOME", "/root/.cache/huggingface")
        local = snapshot_download(
            repo_id=_model_path,
            cache_dir=cache,
            token=os.getenv("HUGGING_FACE_HUB_TOKEN") or None,
        )
        return Path(local).resolve()
    except Exception as e:
        raise RuntimeError(f"Failed to resolve MODEL_PATH '{_model_path}': {e}") from e


def _load_mask_token_id(model_dir: Path) -> int:
    with open(model_dir / "config.json", encoding="utf-8") as fh:
        config = json.load(fh)
    mask_token_id = config.get("mask_token_id")
    if mask_token_id is None:
        raise ValueError(f"mask_token_id missing in {model_dir / 'config.json'}")
    return int(mask_token_id)


def _build_message(image_path: str, prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": prompt},
            ],
        },
    ]


def _clean_response(text: str) -> str:
    out = text
    for stop in STOP_STRINGS:
        out = out.split(stop, 1)[0]
    return out.strip()


def _run_ocr(image_bytes: bytes, prompt: str) -> tuple[str, int]:
    global _llm
    if _llm is None:
        raise RuntimeError("Model not loaded")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(image_bytes)
        image_path = tmp.name

    try:
        sampling = SamplingParams(
            temperature=1.0,
            max_new_tokens=_gen_length,
            denoising_strategy=_remask,
            dynamic_threshold=_dynamic_threshold,
            stop_tokens=list(STOP_STRINGS),
        )
        start = time.perf_counter()
        results = _llm.generate_messages(
            [_build_message(image_path, prompt)],
            sampling_params=sampling,
            use_tqdm=False,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        text = _clean_response(results[0]["text"])
        return text, duration_ms
    finally:
        Path(image_path).unlink(missing_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global _llm
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required for MinerU-Diffusion sidecar")
    # Avoid torch.compile/inductor during nano_dvlm warmup when eager mode is on.
    if _enforce_eager:
        os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
        os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
    model_dir = _resolve_model_dir()
    mask_token_id = _load_mask_token_id(model_dir)
    _patch_nanovllm_eager_warmup()
    _llm = LLM(
        str(model_dir),
        enforce_eager=_enforce_eager,
        tensor_parallel_size=1,
        mask_token_id=mask_token_id,
        block_size=_block_size,
        max_model_len=_max_length,
        gpu_memory_utilization=_gpu_mem,
    )
    yield


app = FastAPI(title="MinerU-Diffusion", version="1.0.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _llm is not None, "model_id": _model_id}


@app.get("/v1/models")
async def list_models():
    return {"data": [{"id": _model_id, "object": "model"}]}


@app.post("/v1/ocr")
async def ocr(
    image: UploadFile = File(...),
    prompt: str = Form(default="\nText Recognition:"),
    model: str = Form(default=""),
):
    if model and model.strip() != _model_id:
        raise HTTPException(status_code=400, detail=f"Unknown model '{model}'")
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image")
    try:
        text, duration_ms = _run_ocr(data, prompt.strip() or "\nText Recognition:")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"text": text, "duration_ms": duration_ms, "model": _model_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=_port, log_level="info")

#!/usr/bin/env bash
# Select vLLM serve flags from VLLM_MODEL (one model per container).
set -euo pipefail

MODEL="${VLLM_MODEL:-deepseek-ai/DeepSeek-OCR}"
GPU_UTIL="${VLLM_GPU_MEMORY_UTILIZATION:-0.72}"
PORT="${VLLM_PORT:-8100}"
MTP_TOKENS="${VLLM_MTP_SPECULATIVE_TOKENS:-1}"
GLM_MAX_LEN="${VLLM_GLM_MAX_MODEL_LEN:-8192}"
CHANDRA_MAX_LEN="${VLLM_CHANDRA_MAX_MODEL_LEN:-8192}"
GEMMA4_MAX_LEN="${VLLM_GEMMA4_MAX_MODEL_LEN:-8192}"
QWEN3_VL_MAX_LEN="${VLLM_QWEN3_VL_MAX_MODEL_LEN:-8192}"
HUNYUAN_MAX_LEN="${VLLM_HUNYUAN_OCR_MAX_MODEL_LEN:-8192}"
DOTS_MOCR_MAX_LEN="${VLLM_DOTS_MOCR_MAX_MODEL_LEN:-8192}"
PHI4_MM_MAX_LEN="${VLLM_PHI4_MM_MAX_MODEL_LEN:-8192}"
ROLMOCR_MAX_LEN="${VLLM_ROLMOCR_MAX_MODEL_LEN:-8192}"
NUMARKDOWN_MAX_LEN="${VLLM_NUMARKDOWN_MAX_MODEL_LEN:-8192}"
SMOLDOCLING_MAX_LEN="${VLLM_SMOLDOCLING_MAX_MODEL_LEN:-8192}"

COMMON=(
  --host "0.0.0.0"
  --port "$PORT"
  --gpu-memory-utilization "$GPU_UTIL"
)

model_lower="$(echo "$MODEL" | tr '[:upper:]' '[:lower:]')"

if [[ "$model_lower" == *"glm-ocr"* ]]; then
  # https://docs.vllm.ai/projects/recipes/en/latest/GLM/GLM-OCR.html
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --max-model-len "$GLM_MAX_LEN" \
    --speculative-config.method mtp \
    --speculative-config.num_speculative_tokens "$MTP_TOKENS"
elif [[ "$model_lower" == *"deepseek-ocr"* ]]; then
  # https://docs.vllm.ai/projects/recipes/en/latest/DeepSeek/DeepSeek-OCR.html
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --logits-processors vllm.model_executor.models.deepseek_ocr:NGramPerReqLogitsProcessor \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
elif [[ "$model_lower" == *"lightonocr"* ]]; then
  # https://huggingface.co/lightonai/LightOnOCR-2-1B
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --limit-mm-per-prompt '{"image": 1}' \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching
elif [[ "$model_lower" == *"chandra"* ]]; then
  # https://huggingface.co/datalab-to/chandra-ocr-2 (see chandra.scripts.vllm)
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --dtype bfloat16 \
    --max-model-len "$CHANDRA_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --mm-processor-kwargs '{"min_pixels": 3136, "max_pixels": 6291456}' \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching
elif [[ "$model_lower" == *"gemma-4"* ]]; then
  # https://docs.vllm.ai/projects/recipes/en/latest/Google/Gemma4.html
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --max-model-len "$GEMMA4_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1, "audio": 0}' \
    --mm-processor-kwargs '{"max_soft_tokens": 560}' \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching
elif [[ "$model_lower" == *"qwen3-vl"* ]]; then
  # https://github.com/vllm-project/recipes/blob/main/Qwen/Qwen3-VL.md (image-only OCR path)
  # --enforce-eager: first-load torch.compile can otherwise sit many minutes with no HTTP listener yet.
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --max-model-len "$QWEN3_VL_MAX_LEN" \
    --limit-mm-per-prompt.video 0 \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching \
    --enforce-eager
elif [[ "$model_lower" == *"hunyuanocr"* ]]; then
  # https://docs.vllm.ai/projects/recipes/en/latest/Tencent-Hunyuan/HunyuanOCR.html
  # Cap max-model-len — HF default 32k balloons KV cache on mid-range GPUs.
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --max-model-len "$HUNYUAN_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --mm-processor-cache-gb 0 \
    --no-enable-prefix-caching
elif [[ "$model_lower" == *"paddleocr-vl"* ]]; then
  # https://github.com/vllm-project/recipes/blob/main/PaddlePaddle/PaddleOCR-VL.md
  PADDLE_BATCH="${VLLM_PADDLEOCR_VL_MAX_NUM_BATCHED_TOKENS:-16384}"
  SERVED_EXTRA=()
  PADDLE_MAX_LEN_EXTRA=()
  # HF config for -1.5 advertises a huge max length; cap KV on mid-range GPUs (override via env).
  if [[ "$model_lower" == *"paddleocr-vl-1.5"* ]]; then
    PADDLE_MAX_LEN_EXTRA=(--max-model-len "${VLLM_PADDLEOCR_VL_15_MAX_MODEL_LEN:-8192}")
  fi
  if [[ -n "${VLLM_PADDLEOCR_VL_SERVED_MODEL_NAME:-}" ]]; then
    SERVED_EXTRA=(--served-model-name "${VLLM_PADDLEOCR_VL_SERVED_MODEL_NAME}")
  fi
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    "${SERVED_EXTRA[@]}" \
    "${PADDLE_MAX_LEN_EXTRA[@]}" \
    --trust-remote-code \
    --max-num-batched-tokens "$PADDLE_BATCH" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
elif [[ "$model_lower" == *"dots.mocr"* ]]; then
  # https://github.com/rednote-hilab/dots.mocr — vLLM ≥ 0.11; align with upstream serve line.
  SERVED_EXTRA=()
  if [[ -n "${VLLM_DOTS_MOCR_SERVED_MODEL_NAME:-}" ]]; then
    SERVED_EXTRA=(--served-model-name "${VLLM_DOTS_MOCR_SERVED_MODEL_NAME}")
  fi
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    "${SERVED_EXTRA[@]}" \
    --trust-remote-code \
    --chat-template-content-format string \
    --max-model-len "$DOTS_MOCR_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
elif [[ "$model_lower" == *"phi-4-multimodal"* ]]; then
  # https://docs.vllm.ai/projects/recipes/en/latest/Microsoft/Phi-4.html — vision via remote code; cap ctx for mid-GPU KV.
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --trust-remote-code \
    --max-model-len "$PHI4_MM_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
elif [[ "$model_lower" == *"rolmocr"* ]]; then
  # https://huggingface.co/reducto/RolmOCR — Qwen2.5-VL-7B doc OCR; upstream recommends VLLM_USE_V1=1 (set in compose).
  export VLLM_USE_V1="${VLLM_USE_V1:-1}"
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --max-model-len "$ROLMOCR_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0
elif [[ "$model_lower" == *"numarkdown"* ]]; then
  # https://huggingface.co/numind/NuMarkdown-8B-Thinking — Qwen2.5-VL reasoning doc → markdown (upstream vLLM serve recipe).
  # --enforce-eager: first-load compile can otherwise sit with no HTTP listener (same class of issue as Qwen3-VL).
  export VLLM_USE_V1="${VLLM_USE_V1:-1}"
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    --trust-remote-code \
    --max-model-len "$NUMARKDOWN_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0 \
    --enforce-eager
elif [[ "$model_lower" == *"smoldocling"* ]]; then
  # https://huggingface.co/docling-project/SmolDocling-256M-preview — IDEFICS3 DocTags pipeline; HF card documents vLLM serve.
  SERVED_EXTRA=()
  if [[ -n "${VLLM_SMOLDOCLING_SERVED_MODEL_NAME:-}" ]]; then
    SERVED_EXTRA=(--served-model-name "${VLLM_SMOLDOCLING_SERVED_MODEL_NAME}")
  fi
  exec vllm serve "$MODEL" \
    "${COMMON[@]}" \
    "${SERVED_EXTRA[@]}" \
    --trust-remote-code \
    --max-model-len "$SMOLDOCLING_MAX_LEN" \
    --limit-mm-per-prompt '{"image": 1}' \
    --no-enable-prefix-caching \
    --mm-processor-cache-gb 0 \
    --enforce-eager
else
  exec vllm serve "$MODEL" "${COMMON[@]}"
fi

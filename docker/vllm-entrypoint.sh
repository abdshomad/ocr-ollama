#!/usr/bin/env bash
# Select vLLM serve flags from VLLM_MODEL (one model per container).
set -euo pipefail

MODEL="${VLLM_MODEL:-deepseek-ai/DeepSeek-OCR}"
GPU_UTIL="${VLLM_GPU_MEMORY_UTILIZATION:-0.72}"
PORT="${VLLM_PORT:-8100}"
MTP_TOKENS="${VLLM_MTP_SPECULATIVE_TOKENS:-1}"
GLM_MAX_LEN="${VLLM_GLM_MAX_MODEL_LEN:-8192}"

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
else
  exec vllm serve "$MODEL" "${COMMON[@]}"
fi

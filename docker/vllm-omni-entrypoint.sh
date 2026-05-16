#!/usr/bin/env bash
# vLLM-Omni: Qwen3-Omni and similar --omni serves (see https://docs.vllm.ai/projects/vllm-omni/)
set -euo pipefail

MODEL="${VLLM_MODEL:-Qwen/Qwen3-Omni-30B-A3B-Instruct}"
GPU_UTIL="${VLLM_GPU_MEMORY_UTILIZATION:-0.85}"
PORT="${VLLM_PORT:-8112}"
OMNI_MAX_LEN="${VLLM_QWEN3_OMNI_MAX_MODEL_LEN:-8192}"

EXTRA_DEPLOY=()
if [[ -n "${VLLM_QWEN3_OMNI_DEPLOY_CONFIG:-}" ]]; then
  EXTRA_DEPLOY=(--deploy-config "${VLLM_QWEN3_OMNI_DEPLOY_CONFIG}")
fi

# --enforce-eager: avoid long silent period before HTTP listener (same class as Qwen3-VL).
exec vllm serve "$MODEL" \
  --omni \
  "${EXTRA_DEPLOY[@]}" \
  --host "0.0.0.0" \
  --port "$PORT" \
  --gpu-memory-utilization "$GPU_UTIL" \
  --max-model-len "$OMNI_MAX_LEN" \
  --enforce-eager

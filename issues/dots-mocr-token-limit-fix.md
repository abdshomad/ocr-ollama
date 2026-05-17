# Issue: dots.mocr vLLM 400 Error (Token Limit)

## Summary
The `rednote-hilab/dots.mocr` model failed with a `vLLM error (400)` stating that the requested `max_tokens` (8192) plus the prompt length exceeded the model's maximum context length (8192).

## Symptoms
- OCR runs for `dots.mocr` returned a 400 error.
- Error message: `vLLM error (400) for model 'rednote-hilab/dots.mocr': This model's maximum context length is 8192 tokens. However, you requested 8192 output tokens and your prompt contains 105 characters...`

## Analysis
The backend was incorrectly defaulting or overriding `max_tokens` to `8192` for this model. Since the image and prompt also consume context budget, `max_tokens` must be significantly less than the total context length.

## Resolution
Updated `backend/app/vllm_client.py` to ensure `rednote-hilab/dots.mocr` uses a default `max_tokens` of `2048` (configurable via `VLLM_DOTS_MOCR_MAX_TOKENS`).

## Repo Impact
- Modified `backend/app/vllm_client.py`.
- Rebuilt `backend` image.

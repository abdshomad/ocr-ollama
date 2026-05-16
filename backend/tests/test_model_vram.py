from app.model_vram import (
    default_model_for_endpoint,
    lookup_model_vram,
    model_details_for_service,
    service_vram_summary,
)


def test_lookup_deepseek():
    info = lookup_model_vram("deepseek-ai/DeepSeek-OCR")
    assert info is not None
    assert info["vram_gib"] == 14
    assert info["params_b"] == 3.0


def test_qwen3vl_default_when_stopped():
    details = model_details_for_service(
        endpoint_id="qwen3vl",
        configured_models=[
            "Qwen/Qwen3-VL-8B-Instruct",
            "Qwen/Qwen3-VL-4B-Instruct",
            "Qwen/Qwen3-VL-2B-Instruct",
        ],
        live_models=[],
    )
    assert len(details) == 1
    assert details[0]["id"] == default_model_for_endpoint("qwen3vl")
    summary = service_vram_summary(details)
    assert summary["vram_estimate_gib"] == 20


def test_live_model_overrides_config():
    details = model_details_for_service(
        endpoint_id="qwen3vl",
        configured_models=[
            "Qwen/Qwen3-VL-8B-Instruct",
            "Qwen/Qwen3-VL-2B-Instruct",
        ],
        live_models=["Qwen/Qwen3-VL-2B-Instruct"],
    )
    assert len(details) == 1
    assert details[0]["vram_gib"] == 8

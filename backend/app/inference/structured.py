from __future__ import annotations

from app.inference.factory import ocr_chat, text_chat
from app.schemas.scan import ProductScanExtraction, parse_extraction

PRODUCT_EXTRACT_PROMPT = (
    "Extract the product SKU (product name or product code) and expiry date from the input. "
    'Return ONLY a JSON object with keys "sku" (non-empty string) and "expiry_date" '
    '("YYYY-MM-DD" or null). No markdown, no explanation.'
)

PRODUCT_EXTRACT_FROM_TEXT_PROMPT = (
    "From this OCR text from a product package, extract SKU and expiry date. "
    'Return ONLY a JSON object with keys "sku" (non-empty string) and "expiry_date" '
    '("YYYY-MM-DD" or null).\n\n'
)


async def structured_extract_from_image(model: str, image_bytes: bytes) -> tuple[ProductScanExtraction, dict, int]:
    raw, meta, duration_ms = await ocr_chat(model, PRODUCT_EXTRACT_PROMPT, image_bytes)
    try:
        extraction = parse_extraction(raw)
    except (ValueError, Exception) as e:
        raise ValueError(f"Failed to parse structured product JSON: {e}") from e
    return extraction, meta, duration_ms


async def structured_extract_from_text(model: str, ocr_text: str) -> tuple[ProductScanExtraction, dict, int]:
    prompt = PRODUCT_EXTRACT_FROM_TEXT_PROMPT + ocr_text
    raw, meta, duration_ms = await text_chat(model, prompt)
    try:
        extraction = parse_extraction(raw)
    except (ValueError, Exception) as e:
        raise ValueError(f"Failed to parse structured product JSON: {e}") from e
    return extraction, meta, duration_ms

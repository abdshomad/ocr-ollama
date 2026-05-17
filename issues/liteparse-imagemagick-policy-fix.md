# Issue: LiteParse ImageMagick Security Policy Block

## Summary
The `litparse` engine failed because the ImageMagick security policy in the backend container was blocking PDF operations, which LiteParse uses internally.

## Symptoms
- OCR runs for `litparse` returned a 502/500 error.
- Error message: `lit parse failed: Conversion failed: Command failed with code 1: convert: attempt to perform an operation not allowed by the security policy 'PDF' @ error/constitute.c/IsCoderAuthorized/426.`

## Analysis
The default ImageMagick policy on Debian/Bookworm (used in the backend base image) blocks PDF/PS/XPS for security reasons. LiteParse (via `@llamaindex/liteparse`) relies on ImageMagick's `convert` for some processing steps, even when the input is an image, triggering this block.

## Resolution
Modified `backend/Dockerfile` to update `/etc/ImageMagick-6/policy.xml`, changing the PDF policy from `rights="none"` to `rights="read|write"`.

## Repo Impact
- Modified `backend/Dockerfile`.
- Rebuilt `backend` image.

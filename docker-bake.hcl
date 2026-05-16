# Registry prefix for tags (override: REGISTRY_PREFIX=ghcr.io/myorg/ocr-ollama docker buildx bake)
variable "REGISTRY_PREFIX" {
  default = "ocr-ollama"
}

group "default" {
  targets = ["cpu-sidecars"]
}

group "cpu-bases" {
  targets = ["ocr-base-cv", "ocr-base-torch-cpu"]
}

group "cpu-sidecars" {
  targets = [
    "ocr-base-cv",
    "ocr-base-torch-cpu",
    "sidecar-onnxtr",
    "sidecar-rapidocr",
    "sidecar-easyocr",
    "sidecar-doctr",
    "sidecar-paddleocr",
    "sidecar-docling",
    "sidecar-lanyocr",
  ]
}

target "ocr-base-cv" {
  context    = "."
  dockerfile = "docker/Dockerfile.base-cv"
  tags       = ["${REGISTRY_PREFIX}-base-cv:bookworm"]
}

target "ocr-base-torch-cpu" {
  context    = "."
  dockerfile = "docker/Dockerfile.base-torch-cpu"
  args = {
    OCR_BASE_CV_IMAGE = "${REGISTRY_PREFIX}-base-cv:bookworm"
  }
  tags       = ["${REGISTRY_PREFIX}-base-torch-cpu:bookworm"]
  depends_on = ["ocr-base-cv"]
}

target "sidecar-onnxtr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "onnxtr"
  tags       = ["${REGISTRY_PREFIX}-onnxtr:latest"]
}

target "sidecar-rapidocr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "rapidocr"
  tags       = ["${REGISTRY_PREFIX}-rapidocr:latest"]
}

target "sidecar-easyocr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "easyocr"
  tags       = ["${REGISTRY_PREFIX}-easyocr:latest"]
}

target "sidecar-doctr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "doctr"
  tags       = ["${REGISTRY_PREFIX}-doctr:latest"]
}

target "sidecar-paddleocr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "paddleocr"
  tags       = ["${REGISTRY_PREFIX}-paddleocr:latest"]
}

target "sidecar-docling" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "docling"
  tags       = ["${REGISTRY_PREFIX}-docling:latest"]
}

target "sidecar-lanyocr" {
  context    = "."
  dockerfile = "docker/Dockerfile.cpu-ocr-sidecars"
  target     = "lanyocr"
  tags       = ["${REGISTRY_PREFIX}-lanyocr:latest"]
}

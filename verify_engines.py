import requests
import json
import os
import time

PORT = 3036
BASE_URL = f"http://127.0.0.1:{PORT}"
SAMPLE_IMAGE = "SAMPLES/IMAGES/1.jpeg"

def test_model(model_name):
    print(f"Testing {model_name}...", end=" ", flush=True)
    try:
        with open(SAMPLE_IMAGE, "rb") as f:
            files = {"image": (os.path.basename(SAMPLE_IMAGE), f, "image/jpeg")}
            data = {"model": model_name}
            start = time.time()
            r = requests.post(f"{BASE_URL}/api/ocr", files=files, data=data, timeout=300)
            duration = time.time() - start
            
            if r.status_code == 200:
                res = r.json()
                text = res.get("text", "")
                if text.strip():
                    print(f"PASS ({duration:.1f}s, {len(text)} chars)")
                    return True, text
                else:
                    print(f"FAIL (Empty result, {duration:.1f}s)")
                    return False, "Empty result"
            else:
                try:
                    err = r.json().get("detail", r.text)
                except:
                    err = r.text
                print(f"FAIL ({r.status_code}: {err[:100]}...)")
                return False, err
    except Exception as e:
        print(f"ERROR ({str(e)})")
        return False, str(e)

def main():
    # 1. Get models
    r = requests.get(f"{BASE_URL}/api/models")
    models = [m["name"] for m in r.json()["models"] if m["ocr_capable"] and m["available"]]
    print(f"Found {len(models)} available OCR models.")
    
    results = {}
    for m in models:
        success, output = test_model(m)
        results[m] = {"success": success, "output": output}
    
    # 2. Summary
    passed = [m for m, r in results.items() if r["success"]]
    failed = [m for m, r in results.items() if not r["success"]]
    
    print("\nSummary:")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    for f in failed:
        print(f"  - {f}: {results[f]['output'][:100]}")

if __name__ == "__main__":
    main()

"""
Downloads ChromaDB's embedding model with retry + resume support.

Run at Docker build time (see Dockerfile) so the app never needs to
download this over the network while actually running. Retries
automatically on any connection failure, and resumes partial
downloads instead of restarting from zero each time.
"""

import os
import time
import urllib.request

URL = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"
DEST = "/root/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx.tar.gz"
MAX_ATTEMPTS = 25
RETRY_DELAY_SECONDS = 5


def get_remote_size() -> int | None:
    try:
        req = urllib.request.Request(URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return int(resp.headers.get("Content-Length", 0))
    except Exception:
        return None


def download_with_resume() -> None:
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    remote_size = get_remote_size()

    for attempt in range(1, MAX_ATTEMPTS + 1):
        existing_size = os.path.getsize(DEST) if os.path.exists(DEST) else 0

        if remote_size and existing_size >= remote_size:
            print(f"Already fully downloaded ({existing_size} bytes). Done.")
            return

        print(f"Attempt {attempt}/{MAX_ATTEMPTS} — resuming from byte {existing_size}...")
        try:
            req = urllib.request.Request(URL)
            if existing_size:
                req.add_header("Range", f"bytes={existing_size}-")

            with urllib.request.urlopen(req, timeout=30) as resp, open(DEST, "ab") as f:
                while True:
                    chunk = resp.read(1024 * 256)  # 256KB at a time
                    if not chunk:
                        break
                    f.write(chunk)

            final_size = os.path.getsize(DEST)
            if not remote_size or final_size >= remote_size:
                print(f"Download complete: {final_size} bytes.")
                return

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(f"Failed to download model after {MAX_ATTEMPTS} attempts.")


if __name__ == "__main__":
    download_with_resume()

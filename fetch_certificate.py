"""Download the authors' certificate at its pinned commit and verify its SHA-256.

    python3 -I fetch_certificate.py            (from the repository root)

Writes cert/c006_31bbf628_int56.json and exits 0 only if the bytes have the expected SHA-256.
The certificate is not stored in this repository; it belongs to its authors. Standard library only.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

REPO = "ArthurAnache/Hackathon-AI-Reasearch"
COMMIT = "c0f8d1837e65d9194350edb7c029897cf031908d"
PATH = "records/1d/autonomous/c006_31bbf628_int56.json"
SHA256 = "dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3"
URL = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{PATH}"
OUT = Path(__file__).resolve().parent / "cert" / "c006_31bbf628_int56.json"


def main() -> int:
    if OUT.exists() and hashlib.sha256(OUT.read_bytes()).hexdigest() == SHA256:
        print(f"already present, sha256 {SHA256} OK: {OUT.name}")
        return 0
    req = urllib.request.Request(URL, headers={"User-Agent": "replay-checks-fetch"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read(64 * 1024 * 1024)
    got = hashlib.sha256(data).hexdigest()
    if got != SHA256:
        print(f"SHA-256 MISMATCH: got {got}, expected {SHA256}; nothing written", file=sys.stderr)
        return 1
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"fetched {len(data)} bytes, sha256 {got} OK: cert/{OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

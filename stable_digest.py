"""Print a SHA-256 of each output file with its run-dependent fields removed.

    python3 -I stable_digest.py out/*.txt out/controls_report.json

Checker A reports timings and the four random points of its identity check, which change from run to run;
those top-level keys (names starting with "seconds" or "identity_points") are dropped, the rest is
re-serialised with sorted keys, and the final VERDICT line (if any) is appended. The digests are compared
with expected/digests.txt by run.sh.
"""

import hashlib
import json
import sys
from pathlib import Path

DROP = ("seconds", "identity_points")


def stable(text: str) -> str:
    lines = text.rstrip("\n").split("\n")
    verdict = lines.pop() if lines and lines[-1].startswith("VERDICT:") else ""
    body = json.loads("\n".join(lines))
    if isinstance(body, dict):
        body = {k: v for k, v in body.items() if not k.startswith(DROP)}
    return json.dumps(body, sort_keys=True) + ("\n" + verdict if verdict else "")


def main() -> int:
    for name in sys.argv[1:]:
        p = Path(name)
        print(f"{hashlib.sha256(stable(p.read_text()).encode()).hexdigest()}  {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

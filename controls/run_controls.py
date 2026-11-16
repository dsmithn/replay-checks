"""Negative and positive controls for the 1d-pr372 replay. Runs checker A and checker B on altered copies of
the certificate and records whether each verdict is the expected one.

    python3 -I controls/run_controls.py CERT OUTDIR      (from replays/1d-pr372)

Altered files are written to OUTDIR (scratch, not committed); their SHA-256 values are in the report.
Every altered certificate is passed with its OWN hash, so the refusal must come from the mathematics or
the format, not from the hash comparison (except control C9, which tests the hash itself).
"""

import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CHECKERS = {"A": HERE / "checker_a" / "check_1d.py", "B": HERE / "checker_b" / "check_b.py"}
SHA = "dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3"
FRAC = "21267647941510998263770007610303168512/14626277862557668614837367632277156521"
K = 12511
GOOD_PRINTED = "1.4540711000681049"


def main() -> int:
    cert, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    raw = cert.read_bytes()
    v = json.loads(raw)["values"]
    q = Fraction(FRAC)
    below = q - Fraction(1, 10**15)
    below_str = f"{below.numerator // below.denominator}." + str((below - below.numerator // below.denominator) * 10**18 // 1)[:18].rjust(18, "0")

    def dump(vals: list[int]) -> bytes:
        return json.dumps({"values": vals}, separators=(",", ":")).encode()

    cases = []  # (id, description, bytes, sha to pass, printed, claim_k, expect)
    cases.append(("P0", "genuine certificate, bound rounded up", raw, SHA, GOOD_PRINTED, K, "ACCEPT"))
    w = list(v); w[100] += 1
    cases.append(("C1", "one height changed by +1 (cell 100)", dump(w), None, GOOD_PRINTED, K, "REJECT"))
    w = list(v); w[12511 // 2] -= 2**40
    cases.append(("C2", "one height near the deciding diagonal lowered by 2^40", dump(w), None, GOOD_PRINTED, K, "REJECT"))
    floaty = raw.replace(b"[" + str(v[0]).encode() + b",", b"[" + str(v[0]).encode() + b".0,", 1)
    cases.append(("C3", "first height written as a float (x.0)", floaty, None, GOOD_PRINTED, K, "REJECT"))
    w = list(v); w[-1] -= sum(w)
    cases.append(("C4", "last height changed so that the integral S is 0", dump(w), None, GOOD_PRINTED, K, "REJECT"))
    cases.append(("C5", "last cell removed (n = 51199)", dump(v[:-1]), None, GOOD_PRINTED, K, "REJECT"))
    cases.append(("C6", "cells reversed (Q unchanged, maximum moves to k = 2n-2-12511)", dump(v[::-1]), None, GOOD_PRINTED, K, "REJECT"))
    extra = raw.rstrip()[:-1] + b',"note":0}'
    cases.append(("C7", "an extra top-level key", extra, None, GOOD_PRINTED, K, "REJECT"))
    cases.append(("C8", "genuine certificate, bound 1e-15 below the exact value", raw, SHA, below_str, K, "REJECT"))
    cases.append(("C9", "genuine certificate, wrong stated hash", raw, "0" * 64, GOOD_PRINTED, K, "REJECT"))
    cases.append(("C10", "genuine certificate, bound as printed in the PR", raw, SHA, "1.4540711000681048", K, "REJECT"))
    cases.append(("P1", "every height negated (Q is invariant)", dump([-x for x in v]), None, GOOD_PRINTED, K, "ACCEPT"))
    cases.append(("C11", "a height written as a JSON string", raw.replace(b"[" + str(v[0]).encode(), b'["' + str(v[0]).encode() + b'"', 1), None, GOOD_PRINTED, K, "REJECT"))

    report, ok_all = [], True
    for cid, desc, data, sha, printed, k, expect in cases:
        path = outdir / f"{cid}.json"
        path.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        row = {"id": cid, "control": desc, "sha256": digest, "printed": printed, "expect": expect}
        for name, prog in CHECKERS.items():
            p = subprocess.run(["python3", "-I", str(prog), str(path), "--sha256", sha or digest, "--claim-fraction", FRAC,
                                "--claim-k", str(k), "--printed", printed], capture_output=True, text=True, timeout=1200)
            verdict = "ACCEPT" if "VERDICT: ACCEPT" in p.stdout and p.returncode == 0 else ("REJECT" if "VERDICT: REJECT" in p.stdout and p.returncode == 1 else f"ERROR rc={p.returncode}")
            reason = ""
            for line in (p.stdout + p.stderr).splitlines():
                if "reason" in line or "VERDICT: REJECT" in line and "F" in line:
                    reason = line.strip()[:160]
            row[name] = verdict
            row[name + "_reason"] = reason
            ok_all &= verdict == expect
        report.append(row)
        print(f"{cid:4} expect {expect:6} A={row['A']:6} B={row['B']:6} {desc}", flush=True)
    (HERE / "out" / "controls_report.json").write_text(json.dumps(report, indent=1))
    print("ALL CONTROLS AS EXPECTED" if ok_all else "SOME CONTROL NOT AS EXPECTED")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())

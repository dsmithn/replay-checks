"""Checker A for STATEMENT.md (C_1d step-function upper bound). Written from STATEMENT.md only.

Exact integer arithmetic throughout (Python int and fractions.Fraction); no floating point is used in any
decision. Standard library only.

    python3 -I check_1d.py CERT.json --sha256 HEX --claim-fraction P/Q --claim-k K --printed DECIMAL [--n N]

Exit 0 and "VERDICT: ACCEPT" only if (F1)-(F5) of STATEMENT.md all hold; otherwise "VERDICT: REJECT"
with the failing item, exit 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from fractions import Fraction

MERSENNE = (1 << 61) - 1


class Reject(Exception):
    def __init__(self, msg: str, report: dict[str, object] | None = None) -> None:
        super().__init__(msg)
        self.report = report or {}


def parse_strict(raw: bytes) -> list[int]:
    """(F1): a JSON object with the single key 'values', a list of JSON integers."""

    def no_floats(s: str) -> int:
        raise Reject(f"F1: non-integer number {s[:40]!r}")

    def no_consts(s: str) -> int:
        raise Reject(f"F1: non-finite constant {s!r}")

    def pairs(kv: list[tuple[str, object]]) -> dict[str, object]:
        keys = [k for k, _ in kv]
        if len(keys) != len(set(keys)):
            raise Reject("F1: duplicate key")
        return dict(kv)

    try:
        obj = json.loads(raw.decode("utf-8"), parse_float=no_floats, parse_constant=no_consts, object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Reject(f"F1: not valid JSON: {e}") from e
    if not isinstance(obj, dict) or set(obj) != {"values"}:
        raise Reject("F1: top level must be an object with exactly the key 'values'")
    vals = obj["values"]
    if not isinstance(vals, list) or not vals:
        raise Reject("F1: 'values' must be a non-empty list")
    for i, x in enumerate(vals):
        if type(x) is not int:  # excludes bool, float, str
            raise Reject(f"F1: values[{i}] is {type(x).__name__}, not an integer")
    return vals


def conv_nonneg(a: list[int], b: list[int], slot_bytes: int) -> list[int]:
    """Exact convolution of two non-negative integer sequences by Kronecker substitution."""
    pa = int.from_bytes(b"".join(x.to_bytes(slot_bytes, "little") for x in a), "little")
    pb = int.from_bytes(b"".join(x.to_bytes(slot_bytes, "little") for x in b), "little")
    out_len = len(a) + len(b) - 1
    prod = (pa * pb).to_bytes(out_len * slot_bytes + slot_bytes, "little")
    return [int.from_bytes(prod[k * slot_bytes:(k + 1) * slot_bytes], "little") for k in range(out_len)]


def autoconv(v: list[int]) -> list[int]:
    n = len(v)
    p = [x if x > 0 else 0 for x in v]
    q = [-x if x < 0 else 0 for x in v]
    bound_bits = 2 * max(abs(x) for x in v).bit_length() + n.bit_length() + 2  # every nonneg coefficient < 2^bound_bits
    slot_bytes = (bound_bits + 7) // 8 + 1
    pp, qq, pq = conv_nonneg(p, p, slot_bytes), conv_nonneg(q, q, slot_bytes), conv_nonneg(p, q, slot_bytes)
    return [pp[k] + qq[k] - 2 * pq[k] for k in range(2 * n - 1)]


def direct_coeff(v: list[int], k: int) -> int:
    n = len(v)
    return sum(v[i] * v[k - i] for i in range(max(0, k - n + 1), min(k, n - 1) + 1))


def poly_eval(coeffs: list[int], x: int, mod: int) -> int:
    acc = 0
    for c in reversed(coeffs):
        acc = (acc * x + c) % mod
    return acc


def check(raw: bytes, sha: str, claim: Fraction, claim_k: int, printed: str, n_expected: int, seed: int) -> dict[str, object]:
    rep: dict[str, object] = {}
    digest = hashlib.sha256(raw).hexdigest()
    rep["sha256"] = digest
    if digest != sha.lower():
        raise Reject(f"F1: sha256 {digest} != stated {sha}")
    v = parse_strict(raw)
    n = len(v)
    rep["n"] = n
    if n != n_expected:
        raise Reject(f"F1: n = {n}, expected {n_expected}")
    rep["max_abs_v"] = max(abs(x) for x in v)
    s = sum(v)
    rep["S"] = s
    if s == 0:
        raise Reject("F2: S = 0")

    t0 = time.perf_counter()
    c = autoconv(v)
    rep["seconds_autoconv"] = round(time.perf_counter() - t0, 2)
    if len(c) != 2 * n - 1:
        raise Reject("F3: wrong coefficient count")

    # Cross-check the whole sequence: sum c_k x^k == (sum v_i x^i)^2 modulo 2^61-1 at random points.
    rng = random.Random(seed)
    points = [rng.randrange(2, MERSENNE - 1) for _ in range(4)]
    for x in points:
        if poly_eval(c, x, MERSENNE) != pow(poly_eval(v, x, MERSENNE), 2, MERSENNE):
            raise Reject(f"F3: internal error: polynomial identity fails at x = {x}")
    rep["identity_points_mod_2^61-1"] = points
    if sum(c) != s * s:  # x = 1, exactly
        raise Reject("F3: internal error: sum of c != S^2")

    m = max(abs(x) for x in c)
    arg = [k for k, x in enumerate(c) if abs(x) == m]
    rep["M"] = m
    rep["argmax_k"] = arg
    rep["c_at_argmax"] = [c[k] for k in arg]
    for k in arg:  # the deciding coefficient again, by the definition
        if direct_coeff(v, k) != c[k]:
            raise Reject(f"F3: internal error: direct sum at k = {k} disagrees")
    second = max(abs(x) for k, x in enumerate(c) if abs(x) != m) if len(set(map(abs, c))) > 1 else m
    rep["second_largest_abs_c"] = second

    q = Fraction(2 * n * m, s * s)
    rep["Q"] = f"{q.numerator}/{q.denominator}"
    rep["Q_decimal_30"] = decimal_str(q, 30)
    if q != claim:
        raise Reject(f"F4: Q = {q} differs from the claimed {claim}")
    if claim_k not in arg:
        raise Reject(f"F4: claimed k = {claim_k} does not attain M (argmax {arg[:5]})")
    pb = Fraction(printed)
    gap = pb - q
    rep["printed"] = printed
    rep["printed_minus_Q"] = f"{gap.numerator}/{gap.denominator}"
    rep["printed_minus_Q_decimal"] = sci(gap)
    if q > pb:
        raise Reject(f"F5: Q exceeds the printed bound {printed} by {sci(-gap)}", rep)
    return rep


def decimal_str(x: Fraction, digits: int) -> str:
    sign = "-" if x < 0 else ""
    x = abs(x)
    whole = x.numerator // x.denominator
    frac = (x - whole) * 10**digits
    return f"{sign}{whole}.{frac.numerator // frac.denominator:0{digits}d}"


def sci(x: Fraction) -> str:
    if x == 0:
        return "0"
    e = 0
    y = abs(x)
    while y < 1:
        y *= 10
        e -= 1
    while y >= 10:
        y /= 10
        e += 1
    d = decimal_str(y, 3)
    return f"{'-' if x < 0 else ''}{d}e{e}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cert")
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--claim-fraction", required=True)
    ap.add_argument("--claim-k", type=int, required=True)
    ap.add_argument("--printed", required=True)
    ap.add_argument("--n", type=int, default=51200)
    ap.add_argument("--seed", type=int, default=20261115)
    a = ap.parse_args()
    raw = open(a.cert, "rb").read()
    t0 = time.perf_counter()
    try:
        rep = check(raw, a.sha256, Fraction(a.claim_fraction), a.claim_k, a.printed, a.n, a.seed)
    except Reject as e:
        print(json.dumps({**e.report, "verdict": "REJECT", "reason": str(e)}, indent=1, default=str))
        print("VERDICT: REJECT")
        return 1
    rep["seconds_total"] = round(time.perf_counter() - t0, 2)
    rep["verdict"] = "ACCEPT"
    print(json.dumps(rep, indent=1, default=str))
    print("VERDICT: ACCEPT")
    return 0


if __name__ == "__main__":
    sys.exit(main())

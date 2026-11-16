#!/usr/bin/env python3
"""Independent exact certificate checker; Python standard library only."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys


# Certificate integers have no specified digit limit. Python 3.11+ otherwise
# rejects some valid integers during parsing or report serialization.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


class Rejection(Exception):
    def __init__(self, item, message):
        super().__init__(message)
        self.item = item


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Rejection("F1", "command line: " + message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Rejection("F1", "duplicate JSON key: " + key)
        result[key] = value
    return result


def forbidden_number(token):
    raise Rejection("F1", "non-integer JSON number: " + token)


def load_values(path, expected_hash, n):
    if n <= 0:
        raise Rejection("F1", "expected n must be positive")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        raise Rejection("F1", "SHA-256 must contain exactly 64 hexadecimal digits")
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise Rejection("F1", "cannot read certificate: " + str(exc)) from exc
    if hashlib.sha256(raw).hexdigest() != expected_hash.lower():
        raise Rejection("F1", "SHA-256 mismatch")
    try:
        obj = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                         parse_float=forbidden_number,
                         parse_constant=forbidden_number)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Rejection("F1", "invalid JSON: " + str(exc)) from exc
    if type(obj) is not dict or set(obj) != {"values"}:
        raise Rejection("F1", "expected object with exactly the key 'values'")
    values = obj["values"]
    if type(values) is not list or len(values) != n:
        raise Rejection("F1", "values must be a list of exactly " + str(n) + " entries")
    if any(type(value) is not int for value in values):
        raise Rejection("F1", "every value must be a JSON integer, excluding booleans")
    return values


def autoconvolution(values):
    """Kronecker substitution with nonnegative digits and exact shift removal.

    For A=max|v_i|, w_i=v_i+A lies in [0,2A]. Every coefficient
    of w*w is <= n*(2A)**2 < B. Thus squaring sum(w_i*B**i)
    has no carries between base-B coefficients. B is a power of 256,
    allowing linear-time packing/unpacking via bytes (no repeated giant shifts).
    """
    n = len(values)
    if not n:
        raise ValueError("convolution requires at least one entry")
    a = max(abs(value) for value in values)
    coefficient_bound = n * (2 * a) ** 2
    width = max(1, (coefficient_bound.bit_length() + 7) // 8)
    if coefficient_bound >= 1 << (8 * width):
        raise Rejection("F3", "packing bound failed")
    packed = b"".join((value + a).to_bytes(width, "little") for value in values)
    integer = int.from_bytes(packed, "little")
    product = (integer * integer).to_bytes((2 * n - 1) * width, "little")
    prefix = [0]
    for value in values:
        prefix.append(prefix[-1] + value)
    coefficients = []
    for k in range(2 * n - 1):
        lo = max(0, k - n + 1)
        hi = min(n - 1, k)
        shifted = int.from_bytes(product[k * width:(k + 1) * width], "little")
        if shifted > coefficient_bound:
            raise Rejection("F3", "decoded coefficient exceeds proven bound")
        window_sum = prefix[hi + 1] - prefix[lo]
        coefficients.append(shifted - 2 * a * window_sum - (hi - lo + 1) * a * a)
    return coefficients


def direct_coefficient(values, k):
    n = len(values)
    return sum(values[i] * values[k - i]
               for i in range(max(0, k - n + 1), min(n - 1, k) + 1))


def exact_decimal(text):
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", text):
        raise Rejection("F5", "printed value must be a finite decimal literal")
    return Fraction(text)


def fraction_text(value):
    return str(value.numerator) + "/" + str(value.denominator)


def decimal_30(value):
    """Nearest decimal with 30 places, ties to even, using only integers."""
    sign = "-" if value < 0 else ""
    scale = 10 ** 30
    quotient, remainder = divmod(abs(value.numerator) * scale, value.denominator)
    twice = 2 * remainder
    if twice > value.denominator or (twice == value.denominator and quotient % 2):
        quotient += 1
    whole, fractional = divmod(quotient, scale)
    return sign + str(whole) + "." + str(fractional).zfill(30)


def check(args, report):
    values = load_values(args.certificate, args.sha256, args.n)
    n = len(values)
    total = sum(values)
    report.update(n=n, S=total, passed=["F1"])
    if total == 0:
        raise Rejection("F2", "sum of heights is zero")
    report["passed"].append("F2")
    coefficients = autoconvolution(values)
    if len(coefficients) != 2 * n - 1:
        raise Rejection("F3", "incorrect convolution length")
    maximum = max(map(abs, coefficients))
    maximizers = [k for k, value in enumerate(coefficients) if abs(value) == maximum]
    # Independently check every deciding coefficient and the claimed index.
    direct_indices = set(maximizers)
    if 0 <= args.claim_k < len(coefficients):
        direct_indices.add(args.claim_k)
    for k in sorted(direct_indices):
        if direct_coefficient(values, k) != coefficients[k]:
            raise Rejection("F3", "direct-sum mismatch at k=" + str(k))
    report.update(M=maximum, maximizing_k=maximizers,
                  direct_sum_checked_k=sorted(direct_indices))
    report["passed"].append("F3")
    ratio = Fraction(2 * n * maximum, total * total)
    report.update(Q=fraction_text(ratio), Q_30_decimals=decimal_30(ratio),
                  Q_30_decimals_rounding="nearest, ties to even")
    # Compute the printable gap even if the claimed ratio/index is wrong.
    printed_error = None
    try:
        gap = exact_decimal(args.printed) - ratio
        report["printed_minus_Q"] = fraction_text(gap)
    except Rejection as exc:
        printed_error = exc
    if not re.fullmatch(r"[+-]?[0-9]+/[1-9][0-9]*", args.claim_fraction):
        raise Rejection("F4", "claim fraction must have form P/Q with positive denominator")
    if ratio != Fraction(args.claim_fraction):
        raise Rejection("F4", "exact ratio differs from claimed fraction")
    if args.claim_k not in maximizers:
        raise Rejection("F4", "claimed k does not attain M")
    report["passed"].append("F4")
    if printed_error is not None:
        raise printed_error
    if gap < 0:
        raise Rejection("F5", "printed bound is below the exact ratio")
    report["passed"].append("F5")


def main(argv=None):
    report = {}
    try:
        parser = Parser(description=__doc__)
        parser.add_argument("certificate")
        parser.add_argument("--sha256", required=True)
        parser.add_argument("--claim-fraction", required=True)
        parser.add_argument("--claim-k", required=True, type=int)
        parser.add_argument("--printed", required=True)
        parser.add_argument("--n", type=int, default=51200)
        args = parser.parse_args(argv)
        check(args, report)
    except Rejection as exc:
        report.update(failing_item=exc.item, error=str(exc))
        print(json.dumps(report, sort_keys=True))
        print("VERDICT: REJECT")
        return 1
    print(json.dumps(report, sort_keys=True))
    print("VERDICT: ACCEPT")
    return 0


if __name__ == "__main__":
    sys.exit(main())

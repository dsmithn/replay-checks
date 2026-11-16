"""Tests for checker_a/check_1d.py on small cases.

The knot formula is tested against f*f computed from the definition (exact rational integration of the
product of two step functions) on a fine rational grid of t, for random signed step functions.
"""

import hashlib
import importlib.util
import json
import random
import unittest
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_1d", HERE / "check_1d.py")
assert spec and spec.loader
ck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ck)


def ff_from_definition(v: list[int], t: Fraction) -> Fraction:
    """(f*f)(t) = integral of f(t-x) f(x) dx, f = sum v_i 1_[ -1/4 + i h, -1/4 + (i+1) h ), exactly."""
    n = len(v)
    h = Fraction(1, 2 * n)
    total = Fraction(0)
    for i in range(n):
        a0, a1 = -Fraction(1, 4) + i * h, -Fraction(1, 4) + (i + 1) * h
        for j in range(n):
            # f(t-x) = v_j when t-x in [b0,b1) i.e. x in (t-b1, t-b0]
            b0, b1 = -Fraction(1, 4) + j * h, -Fraction(1, 4) + (j + 1) * h
            lo, hi = max(a0, t - b1), min(a1, t - b0)
            if hi > lo:
                total += v[i] * v[j] * (hi - lo)
    return total


def cert(vals: list[int]) -> bytes:
    return json.dumps({"values": vals}).encode()


class TestAutoconv(unittest.TestCase):
    def test_should_match_direct_sums_on_random_signed_inputs(self) -> None:
        rng = random.Random(1)
        for n in (1, 2, 3, 7, 50, 257):
            v = [rng.randint(-(2**60), 2**60) for _ in range(n)]
            c = ck.autoconv(v)
            self.assertEqual(c, [ck.direct_coeff(v, k) for k in range(2 * n - 1)])

    def test_should_handle_all_negative_and_zero_entries(self) -> None:
        v = [-3, 0, -5, 0, 0, -1]
        self.assertEqual(ck.autoconv(v), [ck.direct_coeff(v, k) for k in range(11)])


class TestKnotFormula(unittest.TestCase):
    def test_should_equal_sup_of_ff_from_definition(self) -> None:
        rng = random.Random(7)
        for n in (1, 2, 3, 5, 6):
            v = [rng.randint(-9, 9) for _ in range(n)]
            if sum(v) == 0:
                v[0] += 1
            h = Fraction(1, 2 * n)
            grid = [Fraction(-1, 2) + Fraction(m, 8) * h for m in range(0, 8 * 2 * n + 1)]
            sup_def = max(abs(ff_from_definition(v, t)) for t in grid)
            c = ck.autoconv(v)
            self.assertEqual(sup_def, h * max(abs(x) for x in c))
            ratio_def = sup_def / (h * sum(v)) ** 2
            self.assertEqual(ratio_def, Fraction(2 * n * max(abs(x) for x in c), sum(v) ** 2))

    def test_should_give_two_for_the_constant_function(self) -> None:
        v = [1] * 10
        c = ck.autoconv(v)
        self.assertEqual(Fraction(2 * 10 * max(c), 100), 2)


class TestCheck(unittest.TestCase):
    def setUp(self) -> None:
        self.vals = [5, -2, 7, 3, 1]
        c = ck.autoconv(self.vals)
        m = max(abs(x) for x in c)
        self.k = [k for k, x in enumerate(c) if abs(x) == m][0]
        self.q = Fraction(2 * 5 * m, sum(self.vals) ** 2)
        self.raw = cert(self.vals)
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.printed = ck.decimal_str(self.q + Fraction(1, 10**12), 12)

    def run_check(self, raw: bytes, sha: str | None = None, claim: Fraction | None = None, k: int | None = None, printed: str | None = None, n: int = 5) -> dict:
        return ck.check(raw, sha or hashlib.sha256(raw).hexdigest(), claim if claim is not None else self.q, self.k if k is None else k, printed or self.printed, n, 1)

    def test_should_accept_a_correct_small_certificate(self) -> None:
        rep = self.run_check(self.raw)
        self.assertEqual(rep["Q"], f"{self.q.numerator}/{self.q.denominator}")

    def test_should_reject_wrong_sha(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F1: sha256"):
            self.run_check(self.raw, sha="0" * 64)

    def test_should_reject_float_entry(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F1"):
            self.run_check(b'{"values": [5, -2, 7.0, 3, 1]}')

    def test_should_reject_bool_and_extra_keys(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F1"):
            self.run_check(b'{"values": [5, -2, true, 3, 1]}')
        with self.assertRaisesRegex(ck.Reject, "F1"):
            self.run_check(b'{"values": [5, -2, 7, 3, 1], "x": 1}')
        with self.assertRaisesRegex(ck.Reject, "F1"):
            self.run_check(b'{"values": [5, -2, 7, 3, 1], "values": [5, -2, 7, 3, 1]}')

    def test_should_reject_zero_integral(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F2"):
            self.run_check(cert([1, -1, 2, -2, 0]))

    def test_should_reject_wrong_length(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F1: n"):
            self.run_check(cert(self.vals + [0]))

    def test_should_reject_printed_bound_below_exact_value(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F5"):
            self.run_check(self.raw, printed=ck.decimal_str(self.q, 12))  # truncation rounds down unless exact

    def test_should_reject_wrong_claimed_fraction_or_k(self) -> None:
        with self.assertRaisesRegex(ck.Reject, "F4"):
            self.run_check(self.raw, claim=self.q + Fraction(1, 10**20))
        with self.assertRaisesRegex(ck.Reject, "F4"):
            self.run_check(self.raw, k=(self.k + 1) % 9)


if __name__ == "__main__":
    unittest.main()

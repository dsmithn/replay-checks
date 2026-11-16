"""Small exhaustive and adversarial tests for checker B."""

import contextlib
from fractions import Fraction
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_b", HERE / "check_b.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def brute(values):
    result = [0] * (2 * len(values) - 1)
    for i, left in enumerate(values):
        for j, right in enumerate(values):
            result[i + j] += left * right
    return result


class ConvolutionTests(unittest.TestCase):
    def test_exhaustive_signed_small(self):
        for n in range(1, 6):
            for values in itertools.product((-2, 0, 3), repeat=n):
                with self.subTest(values=values):
                    self.assertEqual(checker.autoconvolution(values), brute(values))

    def test_edges_and_large_integers(self):
        cases = [[0], [7], [-7], [8], [0, 2, 0], [-2, 3],
                 [1, 1, -1], [1, -1], [0] * 12,
                 [2**56, 0, -(2**56), 2**56 - 1, -7],
                 [-(2**200), 2**201 + 1, 0, -1],
                 [1] * 257, [-1] * 257]
        for values in cases:
            with self.subTest(values=values):
                expected = brute(values)
                self.assertEqual(checker.autoconvolution(values), expected)
                self.assertEqual([checker.direct_coefficient(values, k)
                                  for k in range(len(expected))], expected)

    def test_exact_decimal_rounding(self):
        self.assertEqual(checker.decimal_30(Fraction(1, 3)), "0." + "3" * 30)
        self.assertEqual(checker.decimal_30(Fraction(2, 3)), "0." + "6" * 29 + "7")
        self.assertEqual(checker.decimal_30(Fraction(1, 2 * 10**30)), "0." + "0" * 30)
        self.assertEqual(checker.decimal_30(Fraction(3, 2 * 10**30)), "0." + "0" * 29 + "2")


class CertificateTests(unittest.TestCase):
    def run_case(self, raw=b'{"values":[1,2]}', *, digest=None,
                 fraction="16/9", k=1, printed="1.8", n=2, cli=False):
        # Keep all test artifacts within the authorized current directory.
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(raw)
            args = [str(path), "--sha256", digest or hashlib.sha256(raw).hexdigest(),
                    "--claim-fraction", fraction, "--claim-k", str(k),
                    "--printed", printed, "--n", str(n)]
            if cli:
                proc = subprocess.run([sys.executable, "-I", str(HERE / "check_b.py"), *args],
                                      text=True, capture_output=True, check=False)
                self.assertEqual(proc.stderr, "")
                code, output = proc.returncode, proc.stdout
            else:
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream):
                    code = checker.main(args)
                output = stream.getvalue()
        lines = output.splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[1], "VERDICT: ACCEPT" if code == 0 else "VERDICT: REJECT")
        self.assertIn(code, (0, 1))
        return code, json.loads(lines[0])

    def assert_rejected(self, item, **kwargs):
        code, report = self.run_case(**kwargs)
        self.assertEqual(code, 1)
        self.assertEqual(report["failing_item"], item)
        return report

    def test_accept_and_all_maximizers(self):
        code, report = self.run_case(cli=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["passed"], ["F1", "F2", "F3", "F4", "F5"])
        self.assertEqual(report["maximizing_k"], [1, 2])
        self.assertEqual(report["direct_sum_checked_k"], [1, 2])
        self.assertEqual(report["Q"], "16/9")
        self.assertEqual(report["printed_minus_Q"], "1/45")

    def test_signed_maxima(self):
        code, report = self.run_case(raw=b'{"values":[1,1,-1]}', n=3,
                                     fraction="12/1", k=3, printed="12")
        self.assertEqual(code, 0)
        self.assertEqual(report["maximizing_k"], [1, 3])

    def test_wrong_hash(self):
        self.assert_rejected("F1", digest="0" * 64)

    def test_long_exact_integer_literals(self):
        raw = ('{"values":[1' + '0' * 5000 + ']}').encode("ascii")
        code, report = self.run_case(raw=raw, n=1, k=0,
                                     fraction="0" * 5000 + "2/1",
                                     printed="2." + "0" * 5000)
        self.assertEqual(code, 0)
        self.assertEqual(report["Q"], "2/1")

    def test_float_entry(self):
        self.assert_rejected("F1", raw=b'{"values":[1,2.0]}')

    def test_zero_sum(self):
        self.assert_rejected("F2", raw=b'{"values":[1,-1]}')

    def test_printed_below_exact(self):
        report = self.assert_rejected("F5", printed="1.7777777777777777", cli=True)
        self.assertLess(Fraction(report["printed_minus_Q"]), 0)

    def test_bad_structure_or_types(self):
        cases = [b'{"values":[1,true]}', b'{"values":[1,"2"]}',
                 b'{"values":[1,null]}', b'{"values":[1,[]]}',
                 b'{"values":[1,{}]}', b'{"values":[1,2],"extra":0}',
                 b'{"values":[1,2],"values":[1,2]}', b'[1,2]',
                 b'{"values":{"a":1}}', b'{"values":[1]}',
                 b'{"values":[1,2,3]}', b'{"values":[1,2e0]}',
                 b'{"values":[1,NaN]}', b'{"values":[1,Infinity]}',
                 b'{"values":[1,2]} trailing', b'\xff', b'{}']
        for raw in cases:
            with self.subTest(raw=raw):
                self.assert_rejected("F1", raw=raw)

    def test_wrong_claims(self):
        self.assert_rejected("F4", fraction="17/9")
        self.assert_rejected("F4", k=0)
        self.assert_rejected("F4", k=-1)
        self.assert_rejected("F4", k=3)
        self.assert_rejected("F4", fraction="1/0")
        self.assert_rejected("F5", printed="NaN")

    def test_default_length_and_bad_cli(self):
        self.assert_rejected("F1", n=51200)
        self.assert_rejected("F1", n=0)
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(checker.main([]), 1)
        self.assertEqual(json.loads(stream.getvalue().splitlines()[0])["failing_item"], "F1")


if __name__ == "__main__":
    unittest.main()

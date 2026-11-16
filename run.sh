#!/bin/sh
# Run both checkers on the certificate (bound as printed in PR #372, and rounded up), the 13 controls,
# both test suites, then compare the outputs with expected/digests.txt.
# Usage: python3 -I fetch_certificate.py && sh run.sh        (from the repository root; about a minute)
set -u
cd "$(dirname "$0")" || exit 2
CERT=cert/c006_31bbf628_int56.json
SHA=dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3
FRAC=21267647941510998263770007610303168512/14626277862557668614837367632277156521
[ -f "$CERT" ] || { echo "no certificate: run python3 -I fetch_certificate.py first"; exit 2; }
mkdir -p out
for C in a b; do
  if [ "$C" = a ]; then PROG=checker_a/check_1d.py; else PROG=checker_b/check_b.py; fi
  for P in 1.4540711000681048 1.4540711000681049; do
    python3 -I "$PROG" "$CERT" --sha256 "$SHA" --claim-fraction "$FRAC" --claim-k 12511 --printed "$P" \
      > "out/checker_${C}_printed_$P.txt"
    echo "checker $C, printed $P: exit $? ($(tail -1 "out/checker_${C}_printed_$P.txt"))"
  done
done
python3 -I controls/run_controls.py "$CERT" out/controls_scratch
FAIL=0
for D in checker_a checker_b; do
  if python3 -I -m unittest discover -s "$D" -p 'test_*.py' > "out/tests_$D.txt" 2>&1; then
    echo "$D tests: $(grep '^Ran ' "out/tests_$D.txt"), OK"
  else
    echo "$D tests FAILED (see out/tests_$D.txt)"; FAIL=1
  fi
done
python3 -I stable_digest.py out/checker_*_printed_*.txt out/controls_report.json > out/digests.txt
if diff expected/digests.txt out/digests.txt && [ "$FAIL" = 0 ]; then
  echo "ALL OUTPUTS MATCH expected/digests.txt"
else
  echo "OUTPUTS DIFFER from expected/digests.txt, or a test failed"; exit 1
fi

# REPLAY: C_1d ≤ 1.4540711000681048* (PR #372, Monteiro, Anache, Delort, Verny)

**Result: the certificate is correct; the printed bound is not.** The step function's exact value is the
fraction the PR states, at the knot it states. That value is 1.45407110006810483548…, which is
3.548 × 10⁻¹⁷ **above** the printed 1.4540711000681048. As printed, the bound is not an upper bound;
1.4540711000681049 is (6.45 × 10⁻¹⁷ above the exact value). The printed decimal is the binary64 display of
the fraction (`float(score)` in the authors' checker), which rounds down here. The same defect was found
and corrected for [CERT2026] on the same page (#243).

## What was checked

STATEMENT.md items (F1)–(F5) on the authors' certificate:

| item | checker A (Claude) | checker B (Codex) |
|---|---|---|
| F1 format, sha256 `dbca822b…02d3`, 51,200 JSON integers | pass | pass |
| F2 S = 19122158522613018945 ≠ 0 | pass | pass |
| F3 exact autoconvolution; M = 5192296860720458560490724514234172 | pass; unique maximiser k = 12511 | pass; unique maximiser k = 12511 |
| F4 Q = 21267647941510998263770007610303168512/14626277862557668614837367632277156521, the PR's fraction; k = 12511 | pass | pass |
| F5 Q ≤ 1.4540711000681048 | **fail** (gap −3.548e−17) | **fail** |
| F5 Q ≤ 1.4540711000681049 | pass (gap 6.451e−17) | pass |

Second-largest |c_k| is 1.907 × 10²¹ below M (relative 3.7 × 10⁻¹³); the maximiser is unique. The exact
step from (F1)–(F5) to the bound is proved in STATEMENT.md §5 and is also tested in
`checker_a/test_check_1d.py` against f∗f computed directly from the definition (exact rational integration)
for small random step functions.

## Programs, machine, versions

- Machine: Apple M4, 16 GB, macOS 26.5.2 (25F84). Python 3.14.7, standard library only.
- Checker A: `checker_a/check_1d.py` (sha256 `fec09843…a3f`), written by Claude from STATEMENT.md and the
  certificate format, and committed (in the private working copy this repository was cut from) before the
  authors' checkers were read. Method: sign split
  v = p − q, three Kronecker products of non-negative packed integers, whole sequence confirmed by the
  polynomial identity at four random points mod 2⁶¹−1 and Σc_k = S² exactly; the deciding knot re-summed
  directly. After the first run, only the reporting was changed (a failed F5 now prints the full report);
  the decision logic is unchanged.
- Checker B: `checker_b/check_b.py` (sha256 `0a76d5bf…54ae`), written by OpenAI Codex (codex-cli 0.160.0,
  model gpt-6-astra, reasoning effort high) in one writing session, in a scratch directory holding only
  STATEMENT.md, BRIEF.md and the certificate; no repair session was needed. Method: offset packing
  w_i = v_i + max|v| with a carry-free slot bound n(2A)² < 256^d, one exact squaring, the offset removed
  with prefix sums; every maximiser and the claimed k re-summed directly. Its 13 tests pass. The writing
  session's log (kept private) shows no path outside its scratch directory. Its brief is `checker_b/BRIEF.md`.
- Third data point: the authors' `records/1d/highres/check_independent.py` (sha256 `f44ad31b…c5c`) and
  `c1d_exact.py` (sha256 `f2a2d135…99`), run with `python3 -I` from the authors' clone (no code of ours
  there). Both print the same fraction and k = 12511. Neither compares the printed
  decimal with the fraction; `check_independent.py` prints `float(score)`, the source of the rounding.

## Exact commands (from the repository root)

```
python3 -I fetch_certificate.py   # downloads the certificate at the pinned commit, checks its sha256
sh run.sh                         # both checkers on both printings, the 13 controls, both test suites,
                                  # and a comparison with expected/digests.txt
```

`run.sh` runs, for C in A, B and P in 1.4540711000681048, 1.4540711000681049:

```
python3 -I checker_a/check_1d.py CERT --sha256 dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3 --claim-fraction 21267647941510998263770007610303168512/14626277862557668614837367632277156521 --claim-k 12511 --printed P
python3 -I checker_b/check_b.py  (same arguments)
python3 -I controls/run_controls.py CERT out/controls_scratch
```

The authors' checker, for the third data point, from a clone of their repository at the commit below:
`python3 -I records/1d/highres/check_independent.py records/1d/autonomous/c006_31bbf628_int56.json`.

CERT = `cert/c006_31bbf628_int56.json`, the file `records/1d/autonomous/c006_31bbf628_int56.json` of
https://github.com/ArthurAnache/Hackathon-AI-Reasearch at `c0f8d1837e65d9194350edb7c029897cf031908d`.

## Outputs (sha256) and timings

| file (as recorded, in `recorded/`) | sha256 | wall time | peak footprint |
|---|---|---|---|
| `checker_a_printed_1.4540711000681048.txt` (REJECT F5) | `0f7a1d0f…62b5` | 4.4 s | 41 MB |
| `checker_a_printed_1.4540711000681049.txt` (ACCEPT) | `1a1fa2fe…22ab` | 4.4 s | 39 MB |
| `checker_b_printed_1.4540711000681048.txt` (REJECT F5) | `31f2bc7a…12cf` | ~1 s | 7 MB |
| `checker_b_printed_1.4540711000681049.txt` (ACCEPT) | `29448dc3…856e` | 1.1 s | 7 MB |
| `controls_report.json` | `5b33e9ec…2167` | 38.2 s | 68 MB |
| the authors' `check_independent.py` (output not stored here) | — | 48.0 s | 32 MB |
| the authors' `c1d_exact.py` (output not stored here) | — | 3.8 s | 37 MB |

Total compute for this replay: well under one CPU-hour; every run went through a process guard (2 GB
footprint cap, wall-clock cap). Checker A's output holds timings and the random points of its identity check,
so its byte hash changes from run to run; `stable_digest.py` drops those fields, and the digests of the
recorded outputs are in `expected/digests.txt`. A fresh run must reproduce them exactly.

## Controls (`controls/run_controls.py`, `recorded/controls_report.json`)

Each altered certificate is passed with its own hash, so a refusal comes from the format or the
mathematics, not from the hash. All 13 came out as expected in both checkers.

| id | control | expected | A | B |
|---|---|---|---|---|
| P0 | genuine certificate, bound rounded up | accept | accept | accept |
| C1 | one height +1 (cell 100) | refuse (F4) | refuse | refuse |
| C2 | one height near the deciding diagonal −2⁴⁰ | refuse (F4) | refuse | refuse |
| C3 | a height written as `x.0` | refuse (F1) | refuse | refuse |
| C4 | last height changed so S = 0 | refuse (F2) | refuse | refuse |
| C5 | last cell removed | refuse (F1) | refuse | refuse |
| C6 | cells reversed (Q unchanged, maximum at k = 89887) | refuse (F4, k) | refuse | refuse |
| C7 | extra top-level key | refuse (F1) | refuse | refuse |
| C8 | bound 10⁻¹⁵ below the exact value | refuse (F5) | refuse | refuse |
| C9 | wrong stated hash | refuse (F1) | refuse | refuse |
| C10 | bound as printed in the PR | refuse (F5) | refuse | refuse |
| P1 | every height negated (Q invariant) | accept | accept | accept |
| C11 | a height written as a string | refuse (F1) | refuse | refuse |

## Hostile read: ways either checker could accept a false certificate

1. **Shared trust base.** Both checkers, and both of the authors', rely on CPython's big-integer
   multiplication and `json` integer parsing. A bug there would be shared. Mitigation: A's polynomial
   identity mod 2⁶¹−1 uses only small modular arithmetic, and A's tests compare against f∗f from the
   definition; still the same interpreter.
2. **Shared statement.** Both were written from the same STATEMENT.md. An error in §5 (the knot formula)
   would be shared. Mitigation: the formula is the one used on the 1d page and in #243, and A's tests
   check it against direct integration of f∗f on a fine rational grid (n ≤ 6).
3. **Checker B, non-deciding coefficients.** B re-sums only the maximisers directly. If its packing were
   wrong and *understated* the true maximum somewhere else, B would accept a wrong M. Its slot bound is
   proved in its notes and checked at run time (`shifted > bound` refuses), and A's whole-sequence
   identity check covers this case independently; but B alone has no whole-sequence check.
4. **Checker A, probabilistic part.** The whole-sequence check in A is the identity at four random
   points modulo a prime (a wrong sequence passes all four with probability at most (2n/(2⁶¹−3))⁴ ≈ 10⁻⁵³,
   given the random points are independent of the data), plus the
   exact check Σc_k = S². The maximiser itself is re-summed exactly. Not a hole in practice; stated for
   completeness.
5. **The claimed numbers are inputs.** F4 compares against the fraction and k typed from the PR body;
   a transcription error would show as a refusal, not a false acceptance.
6. **Interpretation of the certificate.** Neither checker takes the cell geometry from the file; the
   bound is about the f we build from the integers (§5), so it holds whatever the authors intended.
7. **Not checked:** the PR's history claims (independent lineage, search procedure, "5.966 × 10⁻⁴
   below #371") and the certificate's permanence (non-default branch `ws4-research-map` of a personal
   repository).

## What this replay establishes, and what it does not

- Establishes: the bytes with sha256 `dbca822b…02d3` define a step function f with
  max_t |f∗f| / (∫f)² = 21267647941510998263770007610303168512/14626277862557668614837367632277156521
  exactly, so C_1d ≤ 1.4540711000681049 (and ≤ that fraction). The deduction from the computation to the
  bound is short and is proved in STATEMENT.md §5, not taken from the authors.
- Does not establish: C_1d ≤ 1.4540711000681048 (false as a consequence of this certificate); anything
  about the search history; the permanence of the link.

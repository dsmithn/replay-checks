# replay-checks

An independent, exact replay of one entry on the
[optimisation-constants leaderboard](https://github.com/teorth/optimizationproblems): the upper bound
$C_{1d} \le 1.4540711000681048$\* proposed in
[pull request #372](https://github.com/teorth/optimizationproblems/pull/372) (Monteiro, Anache, Delort,
Verny), from a 51,200-cell integer step function.

**Result.** The certificate is correct: its exact value is the fraction the pull request states,
21267647941510998263770007610303168512/14626277862557668614837367632277156521 = 1.45407110006810483548…,
with the maximum at the single knot k = 12511. The printed bound 1.4540711000681048 is 3.5 × 10⁻¹⁷ *below*
that value, so as printed it is not an upper bound; 1.4540711000681049 is. Details: [REPLAY.md](REPLAY.md).

## Run it

Python 3 (tested with 3.14.7 on macOS, Apple M4), standard library only, no other dependencies.

```
python3 -I fetch_certificate.py
sh run.sh
```

The first command downloads the authors' certificate from
[ArthurAnache/Hackathon-AI-Reasearch @ `c0f8d18`](https://github.com/ArthurAnache/Hackathon-AI-Reasearch/blob/c0f8d1837e65d9194350edb7c029897cf031908d/records/1d/autonomous/c006_31bbf628_int56.json)
and refuses it unless its SHA-256 is
`dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3`. The certificate is not stored here.

The second runs both checkers against the bound as printed and rounded up, the 13 controls and both test
suites (about a minute). Expected output:

```
checker a, printed 1.4540711000681048: exit 1 (VERDICT: REJECT)
checker a, printed 1.4540711000681049: exit 0 (VERDICT: ACCEPT)
checker b, printed 1.4540711000681048: exit 1 (VERDICT: REJECT)
checker b, printed 1.4540711000681049: exit 0 (VERDICT: ACCEPT)
... 13 control lines, then ALL CONTROLS AS EXPECTED
checker_a tests: Ran 12 tests in …, OK
checker_b tests: Ran 13 tests in …, OK
ALL OUTPUTS MATCH expected/digests.txt
```

`expected/digests.txt` holds the SHA-256 of each output with its run-dependent fields (timings, random
evaluation points) removed by `stable_digest.py`:

```
02ae900ecba83f627d4b8a9cfab12cc98702b756df36fb4408232d4e45b8e31e  checker_a_printed_1.4540711000681048.txt
46568aef8ccb40bd123d57cb532042ef63e57225e67c62ed91e7e50b06522de2  checker_a_printed_1.4540711000681049.txt
9f1ab5a83d6fe52cb7c7362a07d3d30876087605de7788d5ab61de27a8a1a103  checker_b_printed_1.4540711000681048.txt
67dfc2ad0e88b2ae952a2701ebba104ea9d25bb533ae2ac2d30c965859501166  checker_b_printed_1.4540711000681049.txt
0474b8a65ae709119cdebc8ab53b5567f531e3f7ed5244df52878fcc78b11b6f  controls_report.json
```

## Contents

| path | what |
|---|---|
| `STATEMENT.md` | the definition, the claim, the certificate format, what a checker must establish (F1)–(F5), and the proof that they give the bound |
| `checker_a/` | checker A and its tests, written from `STATEMENT.md` before the authors' checkers were read |
| `checker_b/` | checker B and its tests, written by a different model (OpenAI Codex) from `STATEMENT.md` and the certificate only, in one session; `BRIEF.md` is the brief it was given, `NOTES_B.md` its own notes |
| `controls/run_controls.py` | generates 11 altered certificates that must be refused and 2 that must be accepted, and runs both checkers on each |
| `recorded/` | the outputs of the recorded run described in `REPLAY.md` |
| `expected/digests.txt` | the digests a fresh run must reproduce |
| `REPLAY.md` | the full write-up: method, machine, timings, controls, and the ways either checker could be wrong |
| `suggested-change.diff` | the Markdown change suggested for pull request #372 (bound rounded up, a replay note and reference); `<COMMIT>` stands for this repository's commit named in the pull-request comment |

The two checkers share no code with each other or with the authors' checkers. Both use exact integer
arithmetic only (Python `int` and `fractions.Fraction`); no floating point enters any decision.

## AI assistance

This replay was prepared with AI assistance. The statement, checker A, the controls, the scripts and this
README were written with Claude (Anthropic); checker B was written by OpenAI Codex from the same statement.
The numbers in the write-up are read from the program outputs in this repository.

## Licence

MIT; see [LICENSE](LICENSE). The certificate is the authors' and is not covered by it.

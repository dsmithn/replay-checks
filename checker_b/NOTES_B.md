# Checker B

`check_b.py` uses only the Python standard library and exact integers and
`fractions.Fraction`. Certificate content is parsed as data, never executed.
It checks the raw-byte SHA-256, duplicate keys, exact object shape, integer
types (excluding booleans and all floating-point syntax), and list length.

## Exact convolution

Let `A = max(abs(v_i))` and `w_i = v_i + A`. Choose a byte width `d` such that
`B = 256**d > n*(2*A)**2`. Pack `W = sum(w_i*B**i)` and square it using Python
integer multiplication. Each coefficient of `w*w` lies between zero and
`n*(2*A)**2`, strictly below `B`, so no carries cross coefficient boundaries.
Fixed-width byte decoding recovers all `2*n-1` coefficients, including zeros.

For coefficient `k`, let `L = max(0,k-n+1)`, `H = min(n-1,k)`, and
`m = H-L+1`. The decoded coefficient is

`t_k = c_k + 2*A*sum(v_i, i=L..H) + m*A*A`.

Prefix sums give the correction exactly. No modular reconstruction, floating
point, approximate transform, or probabilistic check is involved. Every index
attaining the largest absolute coefficient, plus the claimed index when in
range, is independently checked by its defining direct sum.

## Verification and result

`python3 -I test_check_b.py` passes all 13 tests. They include 363 exhaustive
signed vectors of lengths 1–5, additional boundary/large-integer cases, all
maximizers of both signs, isolated CLI execution, and rejection of wrong hashes,
floating entries, booleans, duplicate keys, extra keys, wrong lengths, zero
sums, false ratio/index claims, and printed bounds below the exact value.
Long integer and decimal literals are also tested; Python's optional integer
string conversion limit is disabled to preserve exact parsing and reporting.

Running the requested certificate with the SHA-256 and claims in STATEMENT.md
passes F1–F4 and exits 1 with `VERDICT: REJECT`, failing **F5**:

- `n = 51200`
- `S = 19122158522613018945`
- `M = 5192296860720458560490724514234172`
- The only maximizing index is `12511`, also verified by direct summation.
- `Q = 21267647941510998263770007610303168512/14626277862557668614837367632277156521`
- Q to 30 decimal places, rounded to nearest with ties to even:
  `1.454071100068104835482988050926`.
- Printed minus Q is exactly
  `-648730053283317190086893309513210749/18282847328197085768546709540346445651250000000000000`.

Thus the printed bound `1.4540711000681048` is too small. The certificate proves
the exact rational upper bound Q; `1.4540711000681049` is a valid upward-rounded
16-place decimal bound. The step-function proof itself is sound, but its final
inequality using the original printed decimal does not hold.

## Interpretations and scope

- The optional `--n` sets the required length for small test certificates;
  its default is the statement's required 51,200. The supplied claim arguments
  are the expected values, not instructions sourced from the certificate.
- F2 requires a nonzero sum, not equality with the parenthetically quoted sum;
  the actual sum nevertheless agrees with the quote.
- The statement does not specify how to render Q to 30 decimals. The report
  labels its integer-only rounding rule; the F5 decision uses the exact fraction.
- Scaling invariance is correct. The phrase “integer heights lose nothing”
  should not be read as asserting that an arbitrary real vector can be scaled
  to integers; that is unnecessary for validating this integer certificate.
- No other checker or external source was consulted. Independent mathematical
  review was delegated to `/root/check_math`, which confirmed the packing proof
  and independently identified the F5 discrepancy.

Reproduce the certificate check:

```sh
python3 -I check_b.py certificate.json \
  --sha256 dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3 \
  --claim-fraction 21267647941510998263770007610303168512/14626277862557668614837367632277156521 \
  --claim-k 12511 --printed 1.4540711000681048
```

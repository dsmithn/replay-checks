# STATEMENT: C_1d ≤ 1.4540711000681048 (open PR #372, murilo-lm and team)

## 1. What the leaderboard defines (quoted)

From `constants/1d.md` of teorth/optimizationproblems at `87b4ebbd426ff8db597a2004cc45da17903bdcf2`:

> $C_{1d}$ is the largest constant for which one has
> $$\max_{t \in \mathbb{R}} \left|\int_{\mathbb{R}} f(t-x) f(x)\ dx\right| \geq C_{1d} \left(\int_{-1/4}^{1/4} f(x)\ dx\right)^2$$
> for all real-valued (not necessarily non-negative) $f \colon \mathbb{R} \to \mathbb{R}$ supported on $[-1/4,1/4]$.
>
> This is the maximum of $\lvert f*f \rvert$ over $t$, for signed $f$. It is not the quantity
> $\lvert \max_t f*f \rvert$, whose records are smaller and which is a different constant.

## 2. What the entry claims (quoted)

From the body of https://github.com/teorth/optimizationproblems/pull/372 (opened 2026-11-15T21:18:56Z):

> - **Construction:** a step function with $n = 51200$ equal cells on $[-1/4,1/4]$ and signed integer
>   heights $v_i$ (largest $|v_i| = 2^{56}$, $S = \sum_i v_i = 19122158522613018945$).
> - **Exact value:** $2n \max_k |(v*v)_k| / S^2 = 21267647941510998263770007610303168512/14626277862557668614837367632277156521 = 1.4540711000681048\ldots$,
>   the maximum of $|\sum_{i+j=k} v_i v_j|$ (indices from $0$) being at $k = 12511$.

> `records/1d/autonomous/c006_31bbf628_int56.json`: SHA-256 `dbca822baa7c8a20d05451b56de2dd77c032e88fa945d4e243d0a785787202d3`

at commit `c0f8d1837e65d9194350edb7c029897cf031908d` of https://github.com/ArthurAnache/Hackathon-AI-Reasearch.
The PR prints the bound as $C_{1d} \le 1.4540711000681048$\* (title and README cell).

## 3. The certificate format

A JSON object with exactly one key, `"values"`, whose value is a list of 51,200 JSON integers
(the signed heights $v_0, \dots, v_{n-1}$, cell $i$ being the $i$-th from the left). Each integer is
read exactly. `fetch_certificate.py` downloads it to `cert/c006_31bbf628_int56.json`
(the file at the pinned commit; it is on the branch `ws4-research-map`, not on the repository's
default branch `main`).

## 4. What a checker must establish

Given the file, with $n$ = the list length:

- **(F1) Format.** The file's SHA-256 is the stated one; it parses as a JSON object with the single key
  `values`; every entry is a JSON integer (not a float, not a boolean, not a string); $n = 51200$.
- **(F2) Nonzero integral.** $S = \sum_i v_i \ne 0$ (the PR states $S = 19122158522613018945$).
- **(F3) Exact autoconvolution.** $c_k = \sum_{i+j=k,\ 0 \le i,j < n} v_i v_j$ for $k = 0, \dots, 2n-2$,
  computed exactly as integers; $M = \max_k |c_k|$ and the set of $k$ attaining it.
- **(F4) Exact ratio.** $Q = 2nM/S^2$ as a reduced fraction; it must equal the fraction the PR states,
  and the PR's $k = 12511$ must attain $M$.
- **(F5) Printed bound.** $Q \le 1.4540711000681048$ when the decimal is read as an exact rational
  (an upper bound must not be printed below the exact value). Report the gap.

## 5. From (F1)–(F5) to the bound (proved here)

Let $h = 1/(2n)$ and $I_i = [-1/4 + ih,\ -1/4 + (i+1)h)$ for $0 \le i < n$; the $I_i$ partition
$[-1/4, 1/4)$. Let $f = \sum_i v_i \mathbf 1_{I_i}$. Then $f$ is real-valued, bounded and supported on
$[-1/4, 1/4]$, so it is admissible in the definition, and for it
$C_{1d} \le \max_t |f*f(t)| / (\int f)^2$ whenever $\int f \ne 0$ (directly from §1: the inequality must
hold for this $f$).

1. $\int f = h S$. By (F2) this is nonzero.
2. For $a, b \in \mathbb R$, $(\mathbf 1_{[a,a+h)} * \mathbf 1_{[b,b+h)})(t) = \Lambda(t - a - b)$ with
   $\Lambda(u) = \max(0,\ h - |u - h|)$: the length of $[a, a+h) \cap (t - b - h, t - b]$, a "tent"
   supported on $[0, 2h]$ with peak $h$ at $u = h$.
3. Writing $a_i = -1/4 + ih$, we have $a_i + a_j = -1/2 + (i+j)h$, so with $u = t + 1/2$,
   $f*f(t) = \sum_{k=0}^{2n-2} c_k\, \Lambda(u - kh)$.
4. On each interval $u \in [mh, (m+1)h]$ every $\Lambda(u - kh)$ is affine, so $f*f$ is continuous and
   piecewise affine with breakpoints at $u = mh$; it vanishes for $u \le 0$ and $u \ge 2nh$.
   At $u = mh$, $\Lambda(mh - kh) = h$ if $k = m-1$ and $0$ otherwise. So $f*f = h\,c_{m-1}$ at
   $u = mh$ for $1 \le m \le 2n-1$, and $0$ at $u = 0$ and $u = 2nh$.
5. $|g|$ of an affine $g$ on a closed interval is maximised at an endpoint, so
   $\max_t |f*f(t)| = h M$.
6. Therefore $\max_t |f*f| / (\int f)^2 = hM/(h^2S^2) = M/(hS^2) = 2nM/S^2 = Q$, and
   $C_{1d} \le Q \le 1.4540711000681048$ by (F5).

Scale: multiplying every $v_i$ by $\lambda \ne 0$ multiplies numerator and denominator by $\lambda^2$,
so integer heights lose nothing.

## 6. What is OPEN

Nothing in the chain above is taken on trust from the authors. Not covered: whether the PR's other
statements (the search history, the "independent lineage" claim, the comparison with #371's 1.4546676818)
are accurate, and the permanence of the certificate (it sits on a non-default branch of a personal
repository).

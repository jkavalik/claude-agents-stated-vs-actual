"""Small-sample statistics for round v3 (PREREG.md): Fisher's exact test (two-sided), Wilson score CI,
Newcombe hybrid-score CI for a difference of proportions, Holm adjustment. Standard library only."""
from math import comb, sqrt

Z95 = 1.959963984540054


def wilson(k, n, z=Z95):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher(k1, n1, k2, n2):
    """Two-sided Fisher exact p for the 2x2 table [[k1, n1-k1], [k2, n2-k2]] (sum of tables as or less likely)."""
    if n1 == 0 or n2 == 0:
        return None
    K, N = k1 + k2, n1 + n2

    def p(x):
        return comb(K, x) * comb(N - K, n1 - x) / comb(N, n1)

    p0 = p(k1)
    return min(1.0, sum(p(x) for x in range(max(0, K - n2), min(K, n1) + 1) if p(x) <= p0 * (1 + 1e-9)))


def newcombe(k1, n1, k2, n2):
    """Risk difference p1 - p2 with Newcombe's hybrid score 95% CI (method 10)."""
    if n1 == 0 or n2 == 0:
        return (None, None, None)
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d, d - sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def holm(pvals):
    """Holm-adjusted p-values, same order as input; None entries are skipped."""
    idx = sorted((p, i) for i, p in enumerate(pvals) if p is not None)
    m, out, run = len(idx), [None] * len(pvals), 0.0
    for rank, (p, i) in enumerate(idx):
        run = max(run, min(1.0, (m - rank) * p))
        out[i] = run
    return out


def fisher_2xk(ks, ns):
    """Exact two-sided test of equal proportions across k groups (Fisher-Freeman-Halton for a 2 x k table):
    sum of probabilities of all tables with the same margins that are no more likely than the observed one."""
    from math import lgamma, exp
    K, N = sum(ks), sum(ns)
    if N == 0 or K in (0, N):
        return 1.0

    def lp(xs):  # log multivariate hypergeometric probability
        lc = lambda n, k: lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)
        return sum(lc(n, x) for n, x in zip(ns, xs)) - lc(N, K)

    p0, total = lp(ks), 0.0

    def rec(i, left, xs):
        nonlocal total
        if i == len(ns) - 1:
            if left <= ns[i]:
                v = lp(xs + [left])
                if v <= p0 + 1e-9:
                    total += exp(v)
            return
        for x in range(0, min(ns[i], left) + 1):
            if left - x <= sum(ns[i + 1:]):
                rec(i + 1, left - x, xs + [x])
    rec(0, K, [])
    return min(1.0, total)


def perm_test_mean(a, b, n_perm=100000, seed=20261118):
    """Two-sided permutation test for a difference in means (items completed, 0-5). Monte Carlo with a fixed seed;
    p = (1 + #|perm diff| >= |observed diff|) / (1 + n_perm)."""
    import random
    rng = random.Random(seed)
    obs = abs(sum(a) / len(a) - sum(b) / len(b))
    pooled, na, hits = list(a) + list(b), len(a), 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        x, y = pooled[:na], pooled[na:]
        if abs(sum(x) / len(x) - sum(y) / len(y)) >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def bootstrap_mean_diff(a, b, n_boot=20000, seed=20261118):
    """Mean difference a - b with a percentile bootstrap 95% CI (fixed seed)."""
    import random
    rng = random.Random(seed)
    d = sum(a) / len(a) - sum(b) / len(b)
    ds = sorted(sum(rng.choice(a) for _ in a) / len(a) - sum(rng.choice(b) for _ in b) / len(b) for _ in range(n_boot))
    return d, ds[int(0.025 * n_boot)], ds[int(0.975 * n_boot) - 1]


if __name__ == "__main__":  # self-check against known values
    assert abs(fisher(0, 40, 2, 20) - 0.107) < 0.001, fisher(0, 40, 2, 20)
    assert abs(fisher(1, 80, 2, 20) - 0.101) < 0.001
    lo, hi = wilson(2, 10)
    assert abs(lo - 0.0567) < 0.001 and abs(hi - 0.5098) < 0.001, (lo, hi)
    d, lo, hi = newcombe(0, 40, 2, 20)
    assert abs(d + 0.1) < 1e-9 and lo < -0.1 < 0 < hi
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert perm_test_mean([5] * 10, [5] * 10, 2000) == 1.0
    assert perm_test_mean([5] * 10, [0] * 10, 2000) < 0.001
    d, lo, hi = bootstrap_mean_diff([5, 4, 5, 3], [2, 1, 2, 3], 2000)
    assert lo <= d <= hi and d == 2.25
    print("stats self-check ok", wilson(2, 10), newcombe(0, 40, 2, 20))


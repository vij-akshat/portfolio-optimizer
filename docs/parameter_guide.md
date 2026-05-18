# Parameter Calibration Guide — Portfolio Optimizer

---

## Expected Returns (μ)

### Historical Mean
The simplest estimate: annualized sample mean of daily log returns.

**Problem**: Extremely noisy. With 3 years of daily data, the standard error on $\hat{\mu}$ is $\sigma / \sqrt{T} \approx 20\% / \sqrt{756} \approx 0.73\%$ — larger than most return differences between assets.

**Practical rule**: Treat $\mu$ as a signal, not a precise measurement. Use the optimizer primarily as a risk-structuring tool, not a return-maximizer.

### Alternatives
| Method | Description | Use case |
|--------|-------------|----------|
| Equal expected returns | $\mu_i = \bar{\mu}$ for all $i$ | Pure risk-based allocation |
| CAPM | $\mu_i = r_f + \beta_i \cdot \text{ERP}$ | Market-consistent priors |
| Black-Litterman | Blend CAPM equilibrium with views | When you have specific views |
| Factor model | $\mu_i = \alpha_i + \beta_i^\top f$ | Quant factor strategies |

---

## Covariance Matrix (Σ)

### Historical Sample Covariance
Annualized: $\hat{\Sigma} = 252 \cdot \frac{1}{T-1} \sum_t (r_t - \bar{r})(r_t - \bar{r})^\top$

**Recommended lookback**: 2–3 years of daily data (500–750 observations). With 10 assets, the sample covariance has $10 \times 11 / 2 = 55$ free parameters — estimation noise becomes significant with fewer than ~200 observations.

### Regularization (ε)
| ε | Condition number improvement | When to use |
|---|------------------------------|-------------|
| 1e-5 | Minimal | Very clean data, many observations |
| 1e-4 | Moderate | **Default** — most use cases |
| 1e-3 | Strong | Few observations, noisy data |
| 1e-2 | Heavy shrinkage | Crisis periods, unstable correlations |

Check: after regularization, the minimum eigenvalue should be > 1e-6 (annualized). If not, increase ε.

### Ledoit-Wolf Shrinkage (advanced)
A principled alternative to Tikhonov: $\hat{\Sigma}_{\text{LW}} = (1-\alpha)\hat{\Sigma} + \alpha \mu_{\text{LW}} I$, where $\alpha$ and $\mu_{\text{LW}}$ are chosen by analytical formula. Sklearn implements this as `LedoitWolf().fit(returns)`.

---

## Risk Aversion (λ)

| λ | Portfolio character | Typical use |
|---|---------------------|-------------|
| 0.25 | Aggressive, high return/high vol | Aggressive growth allocation |
| 0.5 | Moderately aggressive | Default for return-seeking |
| 1.0 | Balanced | **Starting point** |
| 2.0 | Moderately conservative | Institutional mandates |
| 5.0 | Conservative | Risk-parity-adjacent |
| 10.0+ | Near-minimum variance | Liability-driven investing |

**Sweep it**: The app lets you sweep λ from 0.1 to 10 and watch the portfolio slide along the efficient frontier.

---

## Position Limits (w_max)

| w_max | Typical context |
|-------|----------------|
| 5–10% | Highly diversified, regulatory constraint |
| 10–20% | **Typical institutional range** |
| 25–33% | Concentrated, high-conviction |
| 100% | Unconstrained (academic baseline) |

**Rule of thumb**: For an N-asset universe, w_max = 3/N gives roughly 3 concentrated positions at the cap — a reasonable starting point.

---

## Sector Caps (sector_max)

| sector_max | Effect |
|-----------|--------|
| 25% | Aggressive diversification across sectors |
| 40% | **Moderate** — prevents sector concentration |
| 60% | Light constraint — only blocks extreme tilts |

For a 10-asset universe, a 40% sector cap with 2-asset sectors (e.g. Growth = XLK + XLY) is usually non-binding unless the optimizer strongly wants both assets.

---

## Turnover Limit (τ)

| τ | Interpretation |
|---|----------------|
| 0.0 | No trading — hold current portfolio |
| 0.10 | 10% of portfolio repositioned |
| 0.20–0.30 | Typical quarterly rebalance budget |
| 0.50 | Half the portfolio repositioned |
| 2.0 | Effectively unconstrained |

**Transaction cost equivalence**: If round-trip cost is $c$ per unit of turnover, a turnover limit $\tau$ is equivalent to requiring that the Sharpe improvement from rebalancing exceeds $c \cdot \tau$.

---

## Common Issues

**Issue**: Optimizer returns highly concentrated (1–2 asset) portfolio
**Fix**: Add position limits (w_max = 0.15–0.20) or increase λ

**Issue**: All weight goes to the lowest-volatility asset
**Fix**: Check that μ estimates are reasonable; increase λ if the optimizer is just minimizing variance

**Issue**: `CLARABEL solver failed`
**Fix**: Increase regularization ε; check that target_return is achievable (between min and max of μ)

**Issue**: Efficient frontier has gaps or kinks
**Fix**: This is expected with the long-only constraint — each kink is where an asset enters or exits the portfolio as the target return increases

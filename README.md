# Portfolio Optimizer: Efficient Frontier to Production Constraints

**Mean-variance optimization with CVXPY — from Markowitz to real-world position limits, sector caps, and turnover constraints**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](https://streamlit.io)
[![CVXPY](https://img.shields.io/badge/CVXPY-1.4%2B-orange)](https://www.cvxpy.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Overview

This project implements a production-grade portfolio optimization system built on CVXPY. Starting from basic Markowitz mean-variance optimization, it progressively adds real-world constraints used at quantitative asset managers.

**Three core optimization problems:**

| Problem | Formulation | Use Case |
|---------|-------------|----------|
| Min Variance | $\min_w w^\top \Sigma w$ | Risk-minimizing allocation |
| Target Return | $\min_w w^\top \Sigma w$ s.t. $\mu^\top w = r^*$ | Efficient frontier point |
| Risk Aversion | $\max_w \mu^\top w - \lambda w^\top \Sigma w$ | Full tradeoff with tunable $\lambda$ |

---

## Mathematical Foundation

### Markowitz Optimization

$$\max_w \quad \mu^\top w - \lambda \cdot w^\top \Sigma w$$

Subject to:
- $\mathbf{1}^\top w = 1$ — budget constraint
- $w \geq 0$ — long-only
- $w_i \leq w_{\max}$ — position limits
- $\sum_{i \in S_k} w_i \leq c_k$ — sector caps
- $\|w - w_0\|_1 \leq \tau$ — turnover limit

### Covariance Regularization (Tikhonov)

$$\Sigma_{\text{reg}} = \Sigma + \varepsilon I$$

Raises all eigenvalues by $\varepsilon$, eliminating near-zero eigenvalues that cause numerical instability. Typical $\varepsilon = 10^{-4}$ costs negligible Sharpe while reducing condition number by orders of magnitude.

### Constraint Cost

The Sharpe ratio cost of a position limit $w_{\max}$ is:

$$\text{Cost} = \frac{\text{SR}_{\text{unconstrained}} - \text{SR}(w_{\max})}{\text{SR}_{\text{unconstrained}}}$$

Empirically, a 10–20% cap costs 5–10% of Sharpe — a reasonable price for robustness to estimation error.

---

## Project Structure

```
portfolio-optimizer/
│
├── app.py                  # Streamlit interactive app
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
│
└── docs/
    ├── math_derivations.md   # KKT conditions, duality, constraint analysis
    └── parameter_guide.md    # Calibrating λ, ε, position limits from real data
```

---

## Quick Start

```bash
git clone https://github.com/<your-username>/portfolio-optimizer.git
cd portfolio-optimizer
pip install -r requirements.txt
streamlit run app.py
```

---

## App Features

- **Live data** via `yfinance` — 10 S&P 500 sector ETFs, configurable date range
- **Animated efficient frontier** — curve builds point by point as optimization sweeps targets
- **Constraint explorer** — sliders for $\lambda$, $w_{\max}$, sector cap, turnover limit
- **Constraint cost analysis** — animated Sharpe vs position limit curve
- **Weight allocation charts** — side-by-side comparison across configurations
- **Turnover rebalancing** — shows how tight turnover limits constrain the path to optimal
- **Covariance regularization** — eigenvalue spectrum before/after regularization
- **Production portfolio** — final recommended allocation with full metrics

---

## Key Results

- Tikhonov regularization with $\varepsilon = 10^{-4}$ reduces condition number from $>10^4$ to $<10^3$
- A 15% position cap costs ~8% of Sharpe ratio on sector ETFs
- Turnover constraint of 30% recovers ~85% of unconstrained Sharpe in one rebalance
- 40% sector cap has minimal Sharpe impact for a 10-asset universe

---

## Extensions

- **Black-Litterman**: Replace historical $\mu$ with BL posterior views
- **Robust optimization**: Ellipsoidal uncertainty sets for estimation error
- **Factor risk model**: Substitute sample $\Sigma$ with Barra-style factor decomposition
- **Transaction costs**: Add linear/quadratic cost terms directly to objective

---

## License

MIT License — see [LICENSE](LICENSE).

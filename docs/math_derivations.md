# Mathematical Derivations — Portfolio Optimizer

---

## 1. Markowitz Mean-Variance Optimization

### Primal Problem

$$\max_w \quad \mu^\top w - \lambda \cdot w^\top \Sigma w$$
$$\text{s.t.} \quad \mathbf{1}^\top w = 1, \quad w \geq 0$$

This is a quadratic program (QP) — convex objective, linear constraints — so any local optimum is global.

### Unconstrained Analytical Solution (no short-sell constraint)

The Lagrangian is:

$$\mathcal{L} = \mu^\top w - \lambda w^\top \Sigma w - \nu(\mathbf{1}^\top w - 1)$$

KKT condition: $\nabla_w \mathcal{L} = \mu - 2\lambda \Sigma w - \nu \mathbf{1} = 0$

$$\Rightarrow \quad w^* = \frac{1}{2\lambda} \Sigma^{-1}(\mu - \nu \mathbf{1})$$

Applying $\mathbf{1}^\top w^* = 1$ solves for $\nu$. The result is the **two-fund separation theorem**: every mean-variance efficient portfolio is a linear combination of the minimum variance portfolio and the tangency portfolio.

---

## 2. Minimum Variance Portfolio

$$\min_w \quad w^\top \Sigma w \qquad \text{s.t.} \quad \mathbf{1}^\top w = 1, \quad w \geq 0$$

With the non-negativity constraint, there is no closed form — this is a QP solved numerically. Without the long-only constraint:

$$w_{\text{MV}} = \frac{\Sigma^{-1} \mathbf{1}}{\mathbf{1}^\top \Sigma^{-1} \mathbf{1}}$$

The minimum variance portfolio allocates inversely proportional to variance — assets with lower variance and higher negative correlations receive more weight.

---

## 3. Efficient Frontier

The efficient frontier is traced by solving the **parametric QP**:

$$\min_w \quad w^\top \Sigma w \qquad \text{s.t.} \quad \mu^\top w = r^*, \quad \mathbf{1}^\top w = 1, \quad w \geq 0$$

for each target return $r^* \in [\mu_{\min}, \mu_{\max}]$.

**Two-fund separation** (without long-only): The entire frontier is spanned by two portfolios — the minimum variance portfolio $w_{\text{MV}}$ and any other efficient portfolio $w_1$:

$$w(r^*) = \alpha w_{\text{MV}} + (1-\alpha) w_1$$

With the long-only constraint, the frontier has kinks where assets enter/leave the portfolio as $r^*$ increases.

---

## 4. Covariance Regularization

### Tikhonov Regularization

$$\Sigma_\varepsilon = \Sigma + \varepsilon I$$

**Effect on eigenvalues**: If $\Sigma$ has eigenvalues $\lambda_1 \geq \cdots \geq \lambda_m > 0$, then $\Sigma_\varepsilon$ has eigenvalues $\lambda_k + \varepsilon$. The condition number improves:

$$\kappa(\Sigma_\varepsilon) = \frac{\lambda_1 + \varepsilon}{\lambda_m + \varepsilon} < \frac{\lambda_1}{\lambda_m} = \kappa(\Sigma)$$

**Interpretation**: Adding $\varepsilon I$ is equivalent to adding independent noise of variance $\varepsilon$ to each asset. It shrinks the sample covariance toward a scaled identity matrix.

**Bias-variance tradeoff**: Small $\varepsilon$ has minimal bias but little stabilization. Large $\varepsilon$ heavily shrinks toward equal-variance. Typical $\varepsilon = 10^{-4}$ on annualized covariances is enough to eliminate near-zero eigenvalues without meaningful distortion.

---

## 5. Position Limit Constraints

Adding $w_i \leq w_{\max}$ for all $i$ introduces $n$ inequality constraints. The KKT conditions become:

$$\mu - 2\lambda \Sigma w - \nu \mathbf{1} - \gamma + \delta = 0$$

where $\gamma_i \geq 0$ is the multiplier for $w_i \geq 0$ and $\delta_i \geq 0$ for $w_i \leq w_{\max}$.

**Shadow price**: $\delta_i$ measures the Sharpe ratio lost per unit increase in $w_{\max}$ for asset $i$. At the optimal, $\delta_i > 0$ means asset $i$ is at its cap — it would receive more weight if the constraint were relaxed.

---

## 6. Turnover Constraint

The $\ell_1$ turnover constraint:

$$\|w - w_0\|_1 = \sum_i |w_i - w_{0,i}| \leq \tau$$

This is convex (absolute value of affine functions) and can be linearized with auxiliary variables $u_i \geq |w_i - w_{0,i}|$:

$$w_i - w_{0,i} \leq u_i, \quad w_{0,i} - w_i \leq u_i, \quad \sum_i u_i \leq \tau$$

**Interpretation**: $\tau = 0$ means no trading (hold current portfolio). $\tau = 2$ means full liquidation and reinvestment. For a 10-asset portfolio rebalancing from equal weights, $\tau = 0.3$ typically recovers 70–85% of the unconstrained Sharpe improvement.

---

## 7. Sector Cap Constraints

For sector $k$ with asset index set $\mathcal{S}_k$:

$$\sum_{i \in \mathcal{S}_k} w_i \leq c_k$$

These are linear inequality constraints — adding them preserves the QP structure and CVXPY handles them natively. The shadow price of sector cap $c_k$ measures the Sharpe cost of the cap in the same units as the objective.

---

## 8. Risk Aversion Parameter λ

$\lambda$ controls the risk-return tradeoff:

| $\lambda$ | Behavior |
|-----------|----------|
| $\lambda \to 0$ | Pure return maximization — concentrated in highest-$\mu$ asset |
| $\lambda = 1$ | Balanced tradeoff — typical starting point |
| $\lambda \to \infty$ | Pure variance minimization → minimum variance portfolio |

**Calibration from target Sharpe**: Given a desired portfolio Sharpe $S^*$, the optimal $\lambda \approx \frac{\bar{\mu}}{2 S^* \bar{\sigma}}$ where $\bar{\mu}$ and $\bar{\sigma}$ are the cross-sectional means of expected returns and volatilities.

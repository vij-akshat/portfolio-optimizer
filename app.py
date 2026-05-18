"""
Portfolio Optimizer — Interactive Streamlit App
Efficient Frontier to Production Constraints with CVXPY
"""

import time
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
C = {
    "primary":   "#2ecc71",
    "secondary": "#3498db",
    "accent":    "#e74c3c",
    "warn":      "#f39c12",
    "purple":    "#9b59b6",
    "neutral":   "#95a5a6",
    "bg":        "#0e1117",
    "surface":   "#1c1c2e",
}

st.markdown("""
<style>
.metric-box {
    background: #1c1c2e; border-left: 4px solid #2ecc71;
    border-radius: 8px; padding: 14px 18px; margin: 6px 0;
}
.metric-label { color: #95a5a6; font-size: 0.78rem; letter-spacing: 0.05em; text-transform: uppercase; }
.metric-value { color: #ffffff; font-size: 1.45rem; font-weight: 700; }
.metric-sub   { color: #2ecc71; font-size: 0.82rem; margin-top: 2px; }
.insight-box {
    background: #12211a; border-left: 3px solid #2ecc71;
    padding: 10px 16px; border-radius: 0 8px 8px 0;
    color: #b8f0cc; font-size: 0.9rem; margin: 12px 0;
}
.section-header {
    font-size: 1.1rem; font-weight: 600; color: #3498db;
    border-bottom: 1px solid #1c2d40; padding-bottom: 4px; margin: 18px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)

def metric_card(label, value, sub="", color="#2ecc71"):
    st.markdown(
        f'<div class="metric-box" style="border-left-color:{color}">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-sub" style="color:{color}">{sub}</div>'
        f'</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# UNIVERSES
# ─────────────────────────────────────────────
UNIVERSES = {
    "S&P 500 Sectors": {
        "tickers": {
            "XLK": "Technology", "XLF": "Financials", "XLV": "Healthcare",
            "XLY": "Consumer Disc", "XLP": "Consumer Staples", "XLE": "Energy",
            "XLI": "Industrials", "XLB": "Materials", "XLU": "Utilities",
            "XLRE": "Real Estate",
        },
        "groups": {
            "Growth":      ["XLK", "XLY"],
            "Defensive":   ["XLP", "XLU", "XLV"],
            "Cyclical":    ["XLF", "XLI", "XLB", "XLE"],
            "Real Assets": ["XLRE", "XLE", "XLB"],
        },
        "description": "10 SPDR sector ETFs covering the full S&P 500",
    },
    "Nasdaq 100 Leaders": {
        "tickers": {
            "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA",
            "AMZN": "Amazon", "GOOGL": "Alphabet", "META": "Meta",
            "TSLA": "Tesla", "AVGO": "Broadcom", "COST": "Costco",
            "NFLX": "Netflix",
        },
        "groups": {
            "Mega-cap Tech": ["AAPL", "MSFT", "NVDA", "GOOGL", "META"],
            "Consumer":      ["AMZN", "TSLA", "COST", "NFLX"],
            "Semis":         ["NVDA", "AVGO"],
        },
        "description": "Top 10 Nasdaq 100 constituents by market cap",
    },
    "Dow Jones 30 (Sample)": {
        "tickers": {
            "JPM": "JPMorgan", "GS": "Goldman", "V": "Visa",
            "JNJ": "J&J", "UNH": "UnitedHealth", "HD": "Home Depot",
            "MCD": "McDonald's", "BA": "Boeing", "CAT": "Caterpillar",
            "MMM": "3M",
        },
        "groups": {
            "Finance":       ["JPM", "GS", "V"],
            "Healthcare":    ["JNJ", "UNH"],
            "Consumer":      ["HD", "MCD"],
            "Industrial":    ["BA", "CAT", "MMM"],
        },
        "description": "10 representative Dow Jones 30 blue chips",
    },
    "Global Markets": {
        "tickers": {
            "SPY":  "US (S&P 500)", "QQQ":  "US (Nasdaq)",
            "EWJ":  "Japan",        "EWZ":  "Brazil",
            "FXI":  "China",        "EWG":  "Germany",
            "EWU":  "UK",           "EWC":  "Canada",
            "EWA":  "Australia",    "INDA": "India",
        },
        "groups": {
            "Americas":    ["SPY", "QQQ", "EWZ", "EWC"],
            "Europe":      ["EWG", "EWU"],
            "Asia-Pacific": ["EWJ", "FXI", "EWA", "INDA"],
        },
        "description": "Major country/region ETFs for global macro exposure",
    },
    "Fixed Income": {
        "tickers": {
            "TLT":  "20Y+ Treasury",  "IEF":  "7-10Y Treasury",
            "SHY":  "1-3Y Treasury",  "LQD":  "Corp Bonds (IG)",
            "HYG":  "High Yield",     "TIP":  "TIPS",
            "MBB":  "Mortgage-backed","EMB":  "EM Bonds",
            "BND":  "Total Bond Mkt", "AGG":  "Agg Bond",
        },
        "groups": {
            "Government": ["TLT", "IEF", "SHY", "TIP"],
            "Credit":     ["LQD", "HYG", "MBB"],
            "Global":     ["EMB", "BND", "AGG"],
        },
        "description": "Bond ETFs across duration and credit quality",
    },
    "Commodities & Real Assets": {
        "tickers": {
            "GLD":  "Gold",       "SLV":  "Silver",
            "USO":  "Oil",        "UNG":  "Natural Gas",
            "PDBC": "Commodities","CORN": "Corn",
            "WEAT": "Wheat",      "DBA":  "Agri Basket",
            "PALL": "Palladium",  "PPLT": "Platinum",
        },
        "groups": {
            "Metals":      ["GLD", "SLV", "PALL", "PPLT"],
            "Energy":      ["USO", "UNG"],
            "Agriculture": ["CORN", "WEAT", "DBA", "PDBC"],
        },
        "description": "Commodity and real asset ETFs",
    },
}

# ─────────────────────────────────────────────
# DATA (cached)
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data(years_back: int, universe_name: str):
    try:
        import yfinance as yf
        assets = UNIVERSES[universe_name]["tickers"]
        end   = datetime.now()
        start = end - timedelta(days=years_back * 365)
        tickers = list(assets.keys())
        raw = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=True)
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"] if "Close" in raw.columns.get_level_values(0) else raw["Adj Close"]
        else:
            prices = raw
        prices.columns = [assets.get(c, c) for c in prices.columns]
        prices = prices.dropna()
        returns = np.log(prices / prices.shift(1)).dropna()
        return prices, returns, None
    except Exception as e:
        return None, None, str(e)


def estimate_params(returns_df, epsilon=1e-4):
    mu    = returns_df.mean().values * 252
    Sigma = returns_df.cov().values * 252
    Sigma_reg = Sigma + epsilon * np.eye(len(mu))
    return mu, Sigma, Sigma_reg


def solve_portfolio(mu, Sigma, risk_aversion=1.0, w_min=0.0, w_max=1.0,
                    sector_indices=None, sector_max=None,
                    w_current=None, turnover_max=None, epsilon=1e-4):
    try:
        import cvxpy as cp
    except ImportError:
        st.error("cvxpy not installed. Run: pip install cvxpy")
        return None

    n = len(mu)
    Sig = Sigma + epsilon * np.eye(n)
    w   = cp.Variable(n)
    obj = cp.Maximize(mu @ w - risk_aversion * cp.quad_form(w, Sig))
    cons = [cp.sum(w) == 1, w >= w_min, w <= w_max]
    if sector_indices and sector_max:
        for idxs in sector_indices.values():
            cons.append(cp.sum(w[idxs]) <= sector_max)
    if w_current is not None and turnover_max is not None:
        cons.append(cp.norm(w - w_current, 1) <= turnover_max)
    prob = cp.Problem(obj, cons)
    try:
        prob.solve(solver=cp.CLARABEL, warm_start=True)
    except Exception:
        prob.solve()
    if prob.status not in ["optimal", "optimal_inaccurate"] or w.value is None:
        weights = np.ones(n) / n
    else:
        weights = np.clip(np.array(w.value).flatten(), 0, 1)
        weights /= weights.sum()
    port_ret = float(mu @ weights)
    port_vol = float(np.sqrt(weights @ Sig @ weights))
    sharpe   = port_ret / port_vol if port_vol > 0 else 0
    turnover = float(np.sum(np.abs(weights - w_current))) if w_current is not None else None
    return {
        "weights": weights, "return": port_ret, "volatility": port_vol,
        "sharpe": sharpe, "turnover": turnover,
        "n_positions": int(np.sum(weights > 0.01)),
    }


def build_frontier(mu, Sigma, n_pts=60, epsilon=1e-4):
    try:
        import cvxpy as cp
    except ImportError:
        return None, None, None
    n   = len(mu)
    Sig = Sigma + epsilon * np.eye(n)
    rets, vols, wts = [], [], []
    for target in np.linspace(mu.min(), mu.max(), n_pts):
        w    = cp.Variable(n)
        prob = cp.Problem(cp.Minimize(cp.quad_form(w, Sig)),
                          [w @ mu == target, cp.sum(w) == 1, w >= 0])
        try:
            prob.solve(solver=cp.CLARABEL)
        except Exception:
            continue
        if prob.status in ["optimal", "optimal_inaccurate"] and w.value is not None:
            wv = np.clip(w.value, 0, 1)
            rets.append(target)
            vols.append(float(np.sqrt(wv @ Sig @ wv)))
            wts.append(wv)
    return np.array(rets), np.array(vols), wts


# ═══════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## Portfolio Optimizer")
    st.markdown("*Markowitz → Production Constraints*")
    st.divider()

    page = st.radio("**Navigate**", [
        "Overview", "Asset Universe", "Regularization",
        "Efficient Frontier", "Constraint Explorer",
        "Constraint Cost", "Turnover Rebalancing", "Final Portfolio"
    ])

    st.divider()
    st.markdown("### Settings")
    universe_name = st.selectbox(
        "Asset Universe",
        list(UNIVERSES.keys()),
        index=0,
        help="Choose which market to optimize"
    )
    st.caption(UNIVERSES[universe_name]["description"])
    years_back = st.slider("Years of history", 1, 5, 3)
    epsilon    = st.select_slider("Regularization ε", [1e-5, 1e-4, 1e-3, 1e-2], value=1e-4,
                                  format_func=lambda x: f"{x:.0e}")
    n_steps    = st.slider("Animation steps", 15, 60, 35)

    st.divider()
    st.markdown("### Resources")
    st.markdown("[Math Derivations](docs/math_derivations.md)")
    st.markdown("[Parameter Guide](docs/parameter_guide.md)")


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
with st.spinner("Fetching sector ETF data…"):
    prices, returns, err = load_data(years_back, universe_name)

if err or returns is None:
    st.error(f"Data fetch failed: {err}")
    st.stop()

tickers    = list(prices.columns)    # these are sector names from ASSETS dict
mu, Sigma, Sigma_reg = estimate_params(returns, epsilon)
n_assets   = len(mu)
vols       = np.sqrt(np.diag(Sigma))

# Sector index mapping (use ticker list from prices which still uses original tickers)
raw_tickers = list(returns.columns)
# Rebuild from original ticker keys
def get_sector_indices(original_tickers, universe_name):
    groups = UNIVERSES[universe_name]["groups"]
    sector_idx = {}
    for sector, tkrs in groups.items():
        idxs = [original_tickers.index(t) for t in tkrs if t in original_tickers]
        if idxs:
            sector_idx[sector] = idxs
    return sector_idx

original_tickers = list(prices.columns)
# Map back to ticker symbols via reverse lookup
assets_map = UNIVERSES[universe_name]["tickers"]
label_map  = {v: v for v in assets_map.values()}  # names are already labels
asset_labels = list(prices.columns)
sector_indices = get_sector_indices(original_tickers, universe_name)


# ═══════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════
if page == "Overview":
    st.markdown("# Portfolio Optimizer")
    st.markdown("**Mean-variance optimization: from Markowitz to production-ready constraints**")

    m1, m2, m3, m4 = st.columns(4)
    with m1: metric_card("Assets", str(n_assets), "S&P 500 sector ETFs")
    with m2: metric_card("Trading Days", f"{len(returns):,}", f"{returns.index[0].date()} → {returns.index[-1].date()}")
    with m3: metric_card("Avg Volatility", f"{vols.mean()*100:.1f}%", "cross-sectional mean")
    with m4: metric_card("Avg Correlation", f"{Sigma[np.triu_indices(n_assets,1)].mean() / (vols[None,:]*vols[:,None])[np.triu_indices(n_assets,1)].mean():.2f}", "pairwise")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### The Optimization Problem")
        st.markdown(r"""
        $$\max_w \quad \mu^\top w - \lambda \cdot w^\top \Sigma w$$

        Subject to:
        - $\mathbf{1}^\top w = 1$ — budget constraint
        - $w \geq 0$ — long-only
        - $w_i \leq w_{\max}$ — position limits
        - $\sum_{i \in S_k} w_i \leq c_k$ — sector caps
        - $\|w - w_0\|_1 \leq \tau$ — turnover limit

        Each constraint is convex → CVXPY solves to global optimum.
        """)
    with col2:
        st.markdown("### What You'll Build")
        st.markdown("""
        | Stage | What you'll see |
        |-------|-----------------|
        | Asset Universe | Returns, volatilities, correlations |
        | Regularization | Eigenvalue spectrum, condition number |
        | Efficient Frontier | Animated risk-return curve |
        | Constraint Explorer | Live sliders, real-time re-optimization |
        | Constraint Cost | Sharpe cost of tightening position limits |
        | Turnover Rebalancing | Path to optimal under trading budget |
        | Final Portfolio | Production-ready allocation |
        """)


# ═══════════════════════════════════════════════════════
# PAGE: ASSET UNIVERSE
# ═══════════════════════════════════════════════════════
elif page == "Asset Universe":
    st.markdown("## Asset Universe — Returns & Correlations")

    tab1, tab2, tab3 = st.tabs(["Asset Statistics", "Correlation Heatmap", "Cumulative Returns"])

    with tab1:
        stats_df = pd.DataFrame({
            "Expected Return (%)": (mu * 100).round(2),
            "Volatility (%)":      (vols * 100).round(2),
            "Sharpe Ratio":        (mu / vols).round(3),
        }, index=asset_labels)
        st.dataframe(stats_df.style.background_gradient(subset=["Sharpe Ratio"], cmap="RdYlGn"),
                     use_container_width=True)

        fig = go.Figure()
        sr  = mu / vols
        cmap = px.colors.sample_colorscale("Viridis", sr / sr.max())
        fig.add_trace(go.Scatter(
            x=vols*100, y=mu*100, mode="markers+text",
            text=asset_labels, textposition="top right",
            marker=dict(color=cmap, size=12, line=dict(color="white", width=1.5)),
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=440, title="Risk-Return by Asset",
            xaxis=dict(title="Volatility (%)", gridcolor="#1e2a38"),
            yaxis=dict(title="Expected Return (%)", gridcolor="#1e2a38"),
            margin=dict(l=50, r=20, t=50, b=50),
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_321_1")


    with tab2:
        corr = Sigma / np.outer(vols, vols)
        mask = np.triu(np.ones_like(corr), k=1).astype(bool)
        z    = np.where(mask, corr, None)
        fig2 = go.Figure(go.Heatmap(
            z=z, x=asset_labels, y=asset_labels,
            colorscale="RdYlGn", zmin=-1, zmax=1,
            text=np.where(mask, corr.round(2), ""),
            texttemplate="%{text}", textfont=dict(size=11),
            colorbar=dict(title="Correlation"),
        ))
        fig2.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=500, title="Asset Return Correlations",
            margin=dict(l=100, r=20, t=50, b=100),
        )
        st.plotly_chart(fig2, use_container_width=True, key="chart_339_2")


    with tab3:
        cum = (1 + returns).cumprod()
        cum.columns = asset_labels
        fig3 = go.Figure()
        palette = px.colors.qualitative.Plotly
        for i, col in enumerate(cum.columns):
            fig3.add_trace(go.Scatter(
                x=cum.index, y=cum[col], mode="lines",
                name=col, line=dict(width=1.8, color=palette[i % len(palette)]),
            ))
        fig3.add_hline(y=1, line=dict(color=C["neutral"], dash="dot", width=1))
        fig3.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=440, title="Cumulative Returns by Sector",
            xaxis=dict(title="Date", gridcolor="#1e2a38"),
            yaxis=dict(title="Cumulative Return", gridcolor="#1e2a38"),
            margin=dict(l=50, r=20, t=50, b=50),
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h"),
        )
        st.plotly_chart(fig3, use_container_width=True, key="chart_360_3")



# ═══════════════════════════════════════════════════════
# PAGE: REGULARIZATION
# ═══════════════════════════════════════════════════════
elif page == "Regularization":
    st.markdown("## Covariance Regularization")
    st.markdown("$$\\Sigma_{\\varepsilon} = \\Sigma + \\varepsilon I$$")

    epsilons = [0, 1e-5, 1e-4, 1e-3, 1e-2]
    rows = []
    for eps in epsilons:
        S = Sigma + eps * np.eye(n_assets) if eps > 0 else Sigma
        eigs = np.linalg.eigvalsh(S)
        rows.append({
            "ε": f"{eps:.0e}" if eps > 0 else "0",
            "Min Eigenvalue": round(eigs.min(), 6),
            "Max Eigenvalue": round(eigs.max(), 4),
            "Condition Number": round(eigs.max() / max(eigs.min(), 1e-12), 1),
        })
    reg_df = pd.DataFrame(rows)
    st.dataframe(reg_df, use_container_width=True)

    # Animated eigenvalue spectrum
    st.markdown('<div class="section-header">Eigenvalue Spectrum Before vs After Regularization</div>',
                unsafe_allow_html=True)
    eigs_before = np.linalg.eigvalsh(Sigma)[::-1]
    eigs_after  = np.linalg.eigvalsh(Sigma_reg)[::-1]

    placeholder = st.empty()
    step = max(1, n_assets // n_steps)
    for i in range(step, n_assets+1, step):
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(range(1, i+1)), y=eigs_before[:i],
            name="Original Σ", marker_color=C["accent"], opacity=0.7,
        ))
        fig.add_trace(go.Bar(
            x=list(range(1, i+1)), y=eigs_after[:i],
            name=f"Regularized (ε={epsilon:.0e})", marker_color=C["primary"], opacity=0.7,
        ))
        fig.update_layout(
            barmode="overlay",
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=380, title="Eigenvalue Spectrum",
            xaxis=dict(title="Component", gridcolor="#1e2a38"),
            yaxis=dict(title="Eigenvalue", gridcolor="#1e2a38"),
            margin=dict(l=50, r=20, t=50, b=40),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        placeholder.plotly_chart(fig, use_container_width=True, key=f"anim_411_{i}")

        time.sleep(0.05)

    st.markdown(
        f'<div class="insight-box">Regularization raises all eigenvalues by ε = {epsilon:.0e}, '
        f'eliminating near-zero values that cause numerical instability and extreme weight swings.</div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# PAGE: EFFICIENT FRONTIER
# ═══════════════════════════════════════════════════════
elif page == "Efficient Frontier":
    st.markdown("## Efficient Frontier")
    st.markdown("Sweeping target returns from min to max to trace the full risk-return tradeoff.")

    with st.spinner("Building efficient frontier…"):
        f_ret, f_vol, f_wts = build_frontier(mu, Sigma, n_pts=60, epsilon=epsilon)

    if f_ret is None or len(f_ret) == 0:
        st.error("Could not build frontier — check that cvxpy is installed.")
        st.stop()

    min_var_idx  = int(np.argmin(f_vol))
    max_sr_idx   = int(np.argmax(f_ret / f_vol))

    m1, m2, m3, m4 = st.columns(4)
    with m1: metric_card("Min Vol Portfolio", f"{f_vol[min_var_idx]*100:.1f}%", f"Return: {f_ret[min_var_idx]*100:.1f}%")
    with m2: metric_card("Max Sharpe", f"{(f_ret/f_vol)[max_sr_idx]:.2f}", f"Vol: {f_vol[max_sr_idx]*100:.1f}%")
    with m3: metric_card("Frontier Points", str(len(f_ret)), "solved QPs")
    with m4: metric_card("Return Range", f"{f_ret.min()*100:.1f}%–{f_ret.max()*100:.1f}%", "")

    # Animated frontier build
    placeholder = st.empty()
    step = max(1, len(f_ret) // n_steps)

    for i in range(step, len(f_ret)+1, step):
        fig = go.Figure()
        # Gradient frontier
        for j in range(max(0, i-2), i):
            if j < len(f_ret)-1:
                frac = j / len(f_ret)
                col  = f"rgba({int(52+150*frac)},{int(152-50*frac)},{int(219-100*frac)},0.9)"
                fig.add_trace(go.Scatter(
                    x=f_vol[j:j+2]*100, y=f_ret[j:j+2]*100,
                    mode="lines", line=dict(color=col, width=3),
                    showlegend=False,
                ))
        # Individual assets
        fig.add_trace(go.Scatter(
            x=vols*100, y=mu*100, mode="markers+text",
            text=asset_labels, textposition="top right",
            marker=dict(color=C["neutral"], size=8, line=dict(color="white", width=1.5)),
            name="Assets", textfont=dict(size=9),
        ))
        if i >= min_var_idx + 1:
            fig.add_trace(go.Scatter(
                x=[f_vol[min_var_idx]*100], y=[f_ret[min_var_idx]*100],
                mode="markers+text", text=["  Min Variance"],
                textposition="middle right",
                marker=dict(color=C["primary"], size=14, line=dict(color="white", width=2)),
                name="Min Variance",
            ))
        if i >= max_sr_idx + 1:
            fig.add_trace(go.Scatter(
                x=[f_vol[max_sr_idx]*100], y=[f_ret[max_sr_idx]*100],
                mode="markers+text", text=["  Max Sharpe"],
                textposition="middle right",
                marker=dict(color=C["accent"], size=14, line=dict(color="white", width=2)),
                name="Max Sharpe",
            ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=520, title="Efficient Frontier — Risk-Return Tradeoff",
            xaxis=dict(title="Volatility (%)", gridcolor="#1e2a38"),
            yaxis=dict(title="Expected Return (%)", gridcolor="#1e2a38"),
            margin=dict(l=50, r=20, t=50, b=50),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        placeholder.plotly_chart(fig, use_container_width=True, key=f"anim_495_{i}")

        time.sleep(0.04)

    st.markdown(
        f'<div class="insight-box">Each point on the frontier is a separate QP solve. '
        f'The curve bends — adding constraints (long-only) shrinks the feasible set and pushes '
        f'the frontier right (higher vol for same return).</div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# PAGE: CONSTRAINT EXPLORER
# ═══════════════════════════════════════════════════════
elif page == "Constraint Explorer":
    st.markdown("## Constraint Explorer — Live Re-optimization")
    st.markdown("Adjust constraints and watch the portfolio update in real time.")

    col_s, col_r = st.columns([1, 2])
    with col_s:
        st.markdown("### Parameters")
        lam      = st.slider("Risk aversion λ", 0.1, 10.0, 1.0, step=0.1)
        w_max    = st.slider("Max position weight (%)", 5, 100, 20) / 100
        w_min    = st.slider("Min position weight (%)", 0, 5, 0) / 100
        use_sec  = st.checkbox("Enable sector caps", value=False)
        sec_max  = st.slider("Sector cap (%)", 20, 100, 40) / 100 if use_sec else None
        use_turn = st.checkbox("Enable turnover limit", value=False)
        turn_max = st.slider("Turnover limit (%)", 5, 200, 30) / 100 if use_turn else None

    with col_r:
        with st.spinner("Optimizing…"):
            result = solve_portfolio(
                mu, Sigma, risk_aversion=lam,
                w_min=w_min, w_max=w_max,
                sector_indices=sector_indices if use_sec else None,
                sector_max=sec_max,
                w_current=np.ones(n_assets)/n_assets if use_turn else None,
                turnover_max=turn_max,
                epsilon=epsilon,
            )

        m1, m2, m3, m4 = st.columns(4)
        with m1: metric_card("Expected Return", f"{result['return']*100:.2f}%")
        with m2: metric_card("Volatility",      f"{result['volatility']*100:.2f}%")
        with m3: metric_card("Sharpe Ratio",    f"{result['sharpe']:.3f}")
        with m4: metric_card("# Positions",     str(result["n_positions"]))

        wts     = result["weights"] * 100
        colors  = px.colors.sample_colorscale("Viridis", wts / wts.max())
        fig = go.Figure(go.Bar(
            x=wts, y=asset_labels, orientation="h",
            marker_color=colors, marker_line_color="white", marker_line_width=0.5,
            text=[f"{w:.1f}%" for w in wts], textposition="outside",
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=400, title="Portfolio Weights",
            xaxis=dict(title="Weight (%)", gridcolor="#1e2a38"),
            yaxis=dict(gridcolor="#1e2a38"),
            margin=dict(l=100, r=60, t=50, b=40),
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_550_5")

        if use_turn and result["turnover"] is not None:
            st.metric("Actual Turnover", f"{result['turnover']*100:.1f}%",
                      delta=f"limit: {turn_max*100:.0f}%")


# ═══════════════════════════════════════════════════════
# PAGE: CONSTRAINT COST
# ═══════════════════════════════════════════════════════
elif page == "Constraint Cost":
    st.markdown("## Constraint Cost Analysis")
    st.markdown("How much Sharpe ratio do position limits cost?")

    max_weights = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 1.0]
    with st.spinner("Solving across position limits…"):
        cost_rows = []
        for wm in max_weights:
            r = solve_portfolio(mu, Sigma, risk_aversion=1.0, w_max=wm, epsilon=epsilon)
            if r:
                cost_rows.append({"Max Weight (%)": wm*100, "Sharpe": r["sharpe"],
                                   "Vol (%)": r["volatility"]*100, "Positions": r["n_positions"]})
    cost_df = pd.DataFrame(cost_rows)
    baseline = cost_df["Sharpe"].iloc[-1]
    cost_df["Sharpe Cost (%)"] = ((baseline - cost_df["Sharpe"]) / baseline * 100).round(2)

    # Animated Sharpe curve
    placeholder = st.empty()
    x_vals = cost_df["Max Weight (%)"].values
    y_vals = cost_df["Sharpe"].values
    step   = max(1, len(x_vals) // n_steps)

    for i in range(step, len(x_vals)+1, step):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals[:i], y=y_vals[:i], mode="lines+markers",
            line=dict(color=C["secondary"], width=2.5),
            marker=dict(size=9, color=C["secondary"], line=dict(color="white", width=1.5)),
            fill="tozeroy", fillcolor="rgba(52,152,219,0.1)",
            name="Sharpe Ratio",
        ))
        fig.add_hline(y=baseline, line=dict(color=C["accent"], dash="dash", width=1.5),
                      annotation_text="Unconstrained", annotation_position="right")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=380, title="Sharpe Ratio vs Position Limit",
            xaxis=dict(title="Max Position Weight (%)", gridcolor="#1e2a38"),
            yaxis=dict(title="Sharpe Ratio", gridcolor="#1e2a38"),
            margin=dict(l=50, r=80, t=50, b=50),
        )
        placeholder.plotly_chart(fig, use_container_width=True, key=f"anim_599_{i}")

        time.sleep(0.04)

    # Sharpe cost bars
    bar_colors = [C["primary"] if c < 5 else C["warn"] if c < 15 else C["accent"]
                  for c in cost_df["Sharpe Cost (%)"]]
    fig2 = go.Figure(go.Bar(
        x=cost_df["Max Weight (%)"].astype(str),
        y=cost_df["Sharpe Cost (%)"],
        marker_color=bar_colors, marker_line_color="white", marker_line_width=0.5,
        text=[f"{c:.1f}%" for c in cost_df["Sharpe Cost (%)"]],
        textposition="outside",
    ))
    fig2.update_layout(
        template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
        height=340, title="Sharpe Cost of Position Limits",
        xaxis=dict(title="Max Position Weight (%)"),
        yaxis=dict(title="Sharpe Cost (%)", gridcolor="#1e2a38"),
        margin=dict(l=50, r=20, t=50, b=50),
    )
    st.plotly_chart(fig2, use_container_width=True, key="chart_619_6")

    st.dataframe(cost_df.set_index("Max Weight (%)"), use_container_width=True)
    st.markdown(
        '<div class="insight-box">A 10–20% cap typically costs 5–10% of unconstrained Sharpe. '
        'This is the price of robustness — tighter limits force diversification and reduce '
        'sensitivity to estimation error in μ.</div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# PAGE: TURNOVER REBALANCING
# ═══════════════════════════════════════════════════════
elif page == "Turnover Rebalancing":
    st.markdown("## Turnover-Constrained Rebalancing")
    st.markdown("Starting from equal-weight, how fast can we reach the optimal portfolio?")

    w_start = np.ones(n_assets) / n_assets
    turn_limits = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1.0, 2.0]

    with st.spinner("Solving turnover sweep…"):
        t_rows = []
        for tl in turn_limits:
            r = solve_portfolio(mu, Sigma, risk_aversion=1.0, w_max=0.25,
                                w_current=w_start, turnover_max=tl, epsilon=epsilon)
            if r:
                t_rows.append({
                    "Max Turnover (%)": tl*100,
                    "Actual Turnover (%)": round(r["turnover"]*100, 1) if r["turnover"] else 0,
                    "Sharpe": round(r["sharpe"], 3),
                    "Return (%)": round(r["return"]*100, 2),
                    "Vol (%)": round(r["volatility"]*100, 2),
                })
    turn_df = pd.DataFrame(t_rows)
    unconstrained_sharpe = turn_df["Sharpe"].iloc[-1]

    placeholder = st.empty()
    x_vals = turn_df["Max Turnover (%)"].values
    y_vals = turn_df["Sharpe"].values
    step   = max(1, len(x_vals) // n_steps)
    for i in range(step, len(x_vals)+1, step):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals[:i], y=y_vals[:i], mode="lines+markers",
            line=dict(color=C["primary"], width=2.5),
            marker=dict(size=9, color=C["primary"], line=dict(color="white", width=1.5)),
            fill="tozeroy", fillcolor="rgba(46,204,113,0.1)",
            name="Sharpe Ratio",
        ))
        fig.add_hline(y=unconstrained_sharpe, line=dict(color=C["accent"], dash="dash", width=1.5),
                      annotation_text="Unconstrained", annotation_position="right")
        eq_sharpe = solve_portfolio(mu, Sigma, risk_aversion=1.0, w_max=0.25,
                                    w_current=w_start, turnover_max=0.0001, epsilon=epsilon)
        if eq_sharpe:
            fig.add_hline(y=eq_sharpe["sharpe"],
                          line=dict(color=C["neutral"], dash="dot", width=1.2),
                          annotation_text="Equal Weight", annotation_position="left")
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=400, title="Sharpe Ratio vs Turnover Budget",
            xaxis=dict(title="Max Turnover (%)", gridcolor="#1e2a38"),
            yaxis=dict(title="Sharpe Ratio", gridcolor="#1e2a38"),
            margin=dict(l=50, r=80, t=50, b=50),
        )
        placeholder.plotly_chart(fig, use_container_width=True, key=f"anim_682_{i}")

        time.sleep(0.04)

    st.dataframe(turn_df.set_index("Max Turnover (%)"), use_container_width=True)
    st.markdown(
        '<div class="insight-box">Most of the Sharpe improvement is captured at 20–30% turnover. '
        'Beyond that, additional trading delivers diminishing returns relative to transaction costs.</div>',
        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# PAGE: FINAL PORTFOLIO
# ═══════════════════════════════════════════════════════
elif page == "Final Portfolio":
    st.markdown("## Final Production Portfolio")
    st.markdown("Moderate risk aversion, position limits, sector caps.")

    col_s, col_r = st.columns([1, 2])
    with col_s:
        st.markdown("### Production Settings")
        lam_f    = st.slider("Risk aversion λ", 0.5, 5.0, 2.0, step=0.5)
        wmin_f   = st.slider("Min weight (%)", 0, 5, 2) / 100
        wmax_f   = st.slider("Max weight (%)", 5, 30, 15) / 100
        smax_f   = st.slider("Sector cap (%)", 20, 60, 40) / 100

    with st.spinner("Building final portfolio…"):
        final = solve_portfolio(
            mu, Sigma, risk_aversion=lam_f,
            w_min=wmin_f, w_max=wmax_f,
            sector_indices=sector_indices, sector_max=smax_f,
            epsilon=epsilon,
        )

    with col_r:
        m1, m2, m3, m4 = st.columns(4)
        with m1: metric_card("Expected Return", f"{final['return']*100:.2f}%", color=C["primary"])
        with m2: metric_card("Volatility",      f"{final['volatility']*100:.2f}%", color=C["secondary"])
        with m3: metric_card("Sharpe Ratio",    f"{final['sharpe']:.3f}", color=C["warn"])
        with m4: metric_card("Positions",       str(final["n_positions"]), color=C["purple"])

    tab1, tab2 = st.tabs(["Allocation", "On Frontier"])

    with tab1:
        wts = final["weights"]
        mask = wts > 0.005
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=[l for l, m in zip(asset_labels, mask) if m],
            values=wts[mask]*100,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Plotly,
                        line=dict(color="white", width=1.5)),
            textinfo="label+percent",
        ))
        fig.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"],
            height=420, title="Final Portfolio Allocation",
            margin=dict(l=20, r=20, t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True, key="chart_741_7")


        final_df = pd.DataFrame({
            "Asset": asset_labels,
            "Weight (%)": (wts*100).round(2),
            "E[Return] (%)": (mu*100).round(2),
            "Vol (%)": (vols*100).round(2),
        }).sort_values("Weight (%)", ascending=False)
        st.dataframe(final_df[final_df["Weight (%)"] > 0.5].set_index("Asset"),
                     use_container_width=True)

    with tab2:
        with st.spinner("Rebuilding frontier for comparison…"):
            f_ret, f_vol, _ = build_frontier(mu, Sigma, n_pts=50, epsilon=epsilon)

        fig2 = go.Figure()
        if f_ret is not None:
            for i in range(len(f_ret)-1):
                frac = i / len(f_ret)
                col  = f"rgba({int(52+150*frac)},{int(152-50*frac)},{int(219-100*frac)},0.7)"
                fig2.add_trace(go.Scatter(
                    x=f_vol[i:i+2]*100, y=f_ret[i:i+2]*100,
                    mode="lines", line=dict(color=col, width=2.5),
                    showlegend=False,
                ))
        fig2.add_trace(go.Scatter(
            x=[final["volatility"]*100], y=[final["return"]*100],
            mode="markers+text", text=["  Final Portfolio"],
            textposition="middle right",
            marker=dict(color=C["accent"], size=16, line=dict(color="white", width=2)),
            name=f"Final (Sharpe: {final['sharpe']:.2f})",
        ))
        fig2.add_trace(go.Scatter(
            x=vols*100, y=mu*100, mode="markers",
            marker=dict(color=C["neutral"], size=8, opacity=0.6),
            name="Individual Assets",
        ))
        fig2.update_layout(
            template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
            height=480, title="Final Portfolio on Efficient Frontier",
            xaxis=dict(title="Volatility (%)", gridcolor="#1e2a38"),
            yaxis=dict(title="Expected Return (%)", gridcolor="#1e2a38"),
            margin=dict(l=50, r=20, t=50, b=50),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True, key="chart_786_8")


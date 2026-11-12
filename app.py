# Returns Lab - Streamlit dashboard for week 1 of the roadmap
# run:  .venv/bin/streamlit run app.py   then open http://localhost:8501

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import pandas as pd
import streamlit as st

import analysis as an
import charts
import returns as rt

st.set_page_config(page_title="Returns Lab", page_icon=":material/monitoring:", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 2.2rem; max-width: 1300px; }
.app-eyebrow { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #2a78d6; }
.app-title { font-size: 2.2rem; font-weight: 700; letter-spacing: -0.02em; margin: 2px 0 6px; color: #0b0b0b; }
.app-sub { font-size: 15px; color: #52514e; max-width: 760px; line-height: 1.5; margin-bottom: 10px; }
.chips span { display: inline-block; font-size: 12px; color: #52514e; border: 1px solid #e7e5e0; background: #fff;
              border-radius: 999px; padding: 3px 10px; margin: 0 6px 6px 0; }
.note { font-size: 13px; color: #52514e; margin: 4px 0 8px; }
.section-title { font-size: 15px; font-weight: 600; color: #0b0b0b; margin: 14px 0 6px; }
div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
</style>
""", unsafe_allow_html=True)

PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


@st.cache_data(show_spinner="Loading price data…")
def load():
    return an.load_all()


raw, prices, removed = load()


def show(fig):
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOT_CONFIG)


def pct(x, d=1):
    return f"{x:+.{d}%}"


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def card(col, label, value, note, color="gray", help=None):
    # metric card with a small caption line under the value (no arrow)
    col.metric(label, value, note, delta_color=color, delta_arrow="off", border=True, help=help)


def pct_col(label=None, d=1, sign=True):
    return st.column_config.NumberColumn(label, format=f"%{'+' if sign else ''}.{d}f%%")


# ---------- header + sidebar ----------

st.markdown(f"""
<div class="app-eyebrow">Quant Finance Journey · Step 1 · Markets &amp; instruments</div>
<div class="app-title">Returns Lab</div>
<div class="app-sub">Ten years of daily prices for ten assets. How simple and log returns behave, why adjusted
prices matter, and what goes wrong in free market data.</div>
<div class="chips">
  <span>Source: Yahoo Finance (yfinance)</span>
  <span>{an.START[:7]} → {an.END[:7]}</span>
  <span>Downloaded {an.last_download()}</span>
  <span>USD &amp; PKR assets</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### About")
    st.markdown("A dashboard for week 1 of my quantitative finance roadmap: simple vs log returns, "
                "adjusted prices and data quality.")
    st.markdown("**Assets**")
    st.dataframe(pd.DataFrame([{"Asset": k, "Ticker": v[0], "Currency": v[2]} for k, v in an.ASSETS.items()]),
                 hide_index=True, width="stretch")
    st.markdown("**Cleaning rules**")
    st.markdown("- PSX holidays (zero volume) removed\n"
                "- USD/PKR quotes more than 1.5% off their 5-day median removed\n"
                "- Returns use `Adj Close` (splits + dividends)")
    st.caption("Educational project, not investment advice. Yahoo data is unofficial and for personal use.")

tabs = st.tabs(["Performance", "Simple vs log returns", "Portfolio maths",
                "Pakistan (PKR)", "Dividends & splits", "Data quality"])


# ---------- 1. performance ----------

with tabs[0]:
    c1, c2, c3 = st.columns([3, 2, 1.2])
    names = c1.multiselect("Assets (USD)", an.USD_ASSETS, default=["SPY", "TLT", "GLD", "BTC"])
    period = c2.segmented_control("Period", list(an.PERIODS), default="10Y", required=True, key="perf_period")
    scale = c3.segmented_control("Scale", ["Log", "Linear"], default="Log", required=True, key="perf_scale")

    if not names:
        st.info("Select at least one asset.", icon=":material/info:")
    else:
        windows = {n: an.window(prices[n], period) for n in names}
        growth = {n: p / p.iloc[0] for n, p in windows.items()}

        # one card per asset, 4 per row, with a small growth chart inside
        for i in range(0, len(names), 4):
            cols = st.columns(4)
            for col, name in zip(cols, names[i:i + 4]):
                s = an.stats(windows[name])
                spark = growth[name].resample("W").last().round(4).tolist()
                col.metric(name, pct(s["total"], 0), f"{pct(s['cagr'])} a year", border=True,
                           chart_data=spark, chart_type="area", help=an.ASSETS[name][1])

        show(charts.growth_chart(growth, log=(scale == "Log")))
        show(charts.drawdown_chart(windows))

        section("Statistics for the selected period")
        st.dataframe(an.stats_table(prices, names, period), hide_index=True, width="stretch", column_config={
            "Total return": pct_col(d=0),
            "Annual return": pct_col(),
            "Annual volatility": pct_col(sign=False),
            "Max drawdown": pct_col(d=0),
            "Worst day": pct_col(),
            "Best day": pct_col(),
        })
        st.markdown('<div class="note">Annualized numbers use each asset\'s own trading days per year '
                    '(Bitcoin trades 365 days, US ETFs about 252). The PSX stock is priced in rupees, '
                    'so it is in the Pakistan tab.</div>', unsafe_allow_html=True)


# ---------- 2. simple vs log returns ----------

with tabs[1]:
    c1, c2, _ = st.columns([2, 2, 2])
    asset = c1.selectbox("Asset", list(an.ASSETS), index=0)
    period = c2.segmented_control("Period", list(an.PERIODS), default="10Y", required=True, key="ret_period")

    p = an.window(prices[asset], period)
    c = rt.check_time_aggregation(p)
    ok = c["log_gap"] < 1e-10

    k = st.columns(5)
    card(k[0], "Total return", pct(c["total_simple"]), "P_T / P_0 − 1")
    card(k[1], "Σ log returns", f"{c['sum_log']:.6f}", f"over {c['n_returns']:,} days")
    card(k[2], "ln(P_T / P_0)", f"{c['log_gross']:.6f}", "log of the gross return")
    card(k[3], "Difference", f"{c['log_gap']:.1e}",
         "✓ identity holds" if ok else "✗ identity fails", "green" if ok else "red")
    card(k[4], "Σ simple returns", pct(c["sum_simple"]), "✗ ignores compounding", "red",
         help="Adding simple returns is NOT the total return")

    st.markdown('<div class="note">Log returns add up over time: ln(P₁/P₀) + ln(P₂/P₁) + … = ln(P_T/P₀), '
                'because the middle terms cancel. Simple returns compound, so adding them gives the wrong '
                'answer.</div>', unsafe_allow_html=True)

    left, right = st.columns([4, 7])
    with left:
        show(charts.simple_vs_log_chart(rt.simple_returns(p), rt.log_returns(p), asset))
    with right:
        section("The check for all 10 assets")
        st.dataframe(an.identity_table(prices, period), hide_index=True, width="stretch",
                     column_config={
                         "Σ log returns": st.column_config.NumberColumn(format="%.6f"),
                         "ln(P_T / P_0)": st.column_config.NumberColumn(format="%.6f"),
                         "Gap": st.column_config.NumberColumn(format="%.1e"),
                         "Passes": st.column_config.CheckboxColumn(),
                         "Σ simple returns (wrong)": pct_col("Σ simple (wrong)"),
                         "Real total return": pct_col("Total return"),
                     })


# ---------- 3. portfolio ----------

with tabs[2]:
    c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
    a = c1.selectbox("Asset A", an.USD_ASSETS, index=an.USD_ASSETS.index("SPY"))
    b = c2.selectbox("Asset B", an.USD_ASSETS, index=an.USD_ASSETS.index("BTC"))
    weight = c3.slider("Weight in asset A", 0, 100, 50, step=5, format="%d%%")
    period = c4.segmented_control("Period", list(an.PERIODS), default="10Y", required=True, key="pf_period")

    if a == b:
        st.warning("Pick two different assets.", icon=":material/warning:")
    else:
        exact, wrong = an.portfolio(prices, a, b, weight / 100, period)
        gap_pp = (exact.iloc[-1] - wrong.iloc[-1]) * 100
        worst_bp = (wrong.pct_change() - exact.pct_change()).min() * 1e4

        k = st.columns(4)
        card(k[0], "Correct total return", pct(exact.iloc[-1] - 1), f"{weight}% {a} / {100 - weight}% {b}")
        card(k[1], "Averaging log returns", pct(wrong.iloc[-1] - 1), "✗ the common mistake", "red")
        card(k[2], "Understated by", f"{gap_pp:,.1f} pp", "percentage points of total return")
        card(k[3], "Worst single day", f"{worst_bp:,.0f} bp", "error on one day (basis points)")

        show(charts.portfolio_chart(exact, wrong))
        st.markdown('<div class="note">Across assets it is the other way round: the portfolio return is the '
                    'weighted average of <b>simple</b> returns. Averaging log returns always understates it '
                    "(Jensen's inequality), and the gap grows with volatility.</div>", unsafe_allow_html=True)


# ---------- 4. pakistan ----------

with tabs[3]:
    c1, _ = st.columns([2, 4])
    period = c1.segmented_control("Period", list(an.PERIODS), default="10Y", required=True, key="pak_period")

    pkr, usd = an.ogdc_in_usd(prices, period)
    fx = an.window(prices["USDPKR"], period)

    k = st.columns(3)
    card(k[0], "OGDC in PKR", pct(pkr.iloc[-1] / pkr.iloc[0] - 1, 0), "total return for a rupee investor")
    card(k[1], "OGDC in USD", pct(usd.iloc[-1] / usd.iloc[0] - 1, 0), "same shares, measured in dollars")
    card(k[2], "USD/PKR", f"{fx.iloc[0]:.0f} → {fx.iloc[-1]:.0f}",
         f"rupees per dollar ({pct(fx.iloc[-1] / fx.iloc[0] - 1, 0)})")

    show(charts.two_currency_chart(pkr, usd))
    show(charts.fx_chart(fx, removed["USDPKR"].loc[fx.index[0]:]))
    st.markdown('<div class="note">OGDC.KA is used as a KSE-100 proxy because Yahoo no longer serves the index. '
                "Yahoo's USD/PKR series mixes two quote sources: the obvious spikes are removed, but its "
                "day-to-day volatility is still overstated.</div>", unsafe_allow_html=True)


# ---------- 5. dividends & splits ----------

with tabs[4]:
    section("Dividends: price return vs total return (full 10 years)")
    st.dataframe(an.dividends_table(raw, prices), hide_index=True, width="stretch", column_config={
        "Price return (Close)": pct_col(),
        "Total return (Adj Close)": pct_col(),
        "From dividends (pp)": st.column_config.NumberColumn(format="%+.1f pp"),
    })

    section("Stock splits")
    stock = st.segmented_control("Stock", ["NVDA", "AAPL"], default="NVDA", required=True, key="split_stock")
    df = raw[stock]
    raw_price, splits = an.unadjusted(df)
    raw_ret, adj_ret = raw_price.pct_change(), df["Adj Close"].pct_change()

    k = st.columns(4)
    for col, (d, ratio) in zip(k, splits.items()):
        card(col, f"{d:%d %b %Y} · {ratio:g}-for-1 split", pct(adj_ret[d], 2),
             f"true return · unadjusted shows {pct(raw_ret[d], 0)}")
    show(charts.split_chart(raw_price, df["Close"], splits, stock))


# ---------- 6. data quality ----------

with tabs[5]:
    section("Checks run before any return is computed")
    quality = an.quality_table(raw, prices)
    st.dataframe(quality, hide_index=True, width="stretch", column_config={
        "Zero volume": st.column_config.NumberColumn(help="Empty for FX, which has no volume"),
    })
    st.download_button("Download quality log (CSV)", quality.to_csv(index=False), "quality_log.csv",
                       "text/csv", icon=":material/download:")

    st.markdown(
        "- **PSX holidays**: Yahoo repeats the last close with zero volume (132 rows for OGDC). "
        "They would add fake 0% days, so they are removed.\n"
        "- **USD/PKR**: about 20% of closes fall outside the day's high–low range, and in Oct 2026 the close "
        "flips between ~268 and ~276.5. 64 isolated spikes are removed.\n"
        "- **Splits and dividends**: returns use `Adj Close`, which is split- and dividend-adjusted.\n"
        "- **Not checked yet**: the Stooq cross-check, which needs a manual CSV download.")

    section("Download manifest")
    manifest = pd.read_csv(an.MANIFEST)
    manifest["sha256"] = manifest["sha256"].str[:12] + "…"
    st.dataframe(manifest[["source", "symbol", "rows", "first_date", "last_date", "retrieved_utc", "sha256"]],
                 hide_index=True, width="stretch")

# Plotly charts for the app. One shared style so every chart looks the same.

import numpy as np
import plotly.graph_objects as go

FONT = "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#ebeae6"
RED = "#d03b3b"

# fixed color per asset (color follows the asset, not its position in the selection)
COLORS = {
    "SPY": "#2a78d6", "EFA": "#eb6834", "EEM": "#1baf7a", "TLT": "#eda100",
    "GLD": "#e87ba4", "AAPL": "#008300", "NVDA": "#6250d6", "BTC": "#e34948",
}
BLUE, ORANGE = "#2a78d6", "#eb6834"


def style(fig, title, yformat=None, height=400, log=False, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=60, r=12, t=64 if legend else 48, b=40),
        title=dict(text=title, x=0, xanchor="left", y=0.98, yanchor="top",
                   font=dict(size=15, color=INK, family=FONT)),
        font=dict(family=FONT, size=12, color=INK2),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, size=12, color=INK)),
        showlegend=legend,
        legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom",
                    font=dict(size=12, color=INK2), itemclick="toggleothers"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, ticks="outside", tickcolor=GRID, automargin=True,
                     showspikes=True, spikemode="across", spikethickness=1, spikecolor=MUTED, spikedash="solid")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickformat=yformat,
                     type="log" if log else "linear", automargin=True)
    return fig


def log_ticks(fig, lo, hi):
    """Ticks at 1-2-5 steps for a log 'growth of 1' axis, all labelled like 2×."""
    vals = [m * 10 ** e for e in range(-2, 5) for m in (1, 2, 5)]
    vals = [v for v in vals if lo * 0.8 <= v <= hi * 1.25]
    fig.update_yaxes(tickvals=vals, ticktext=[f"{v:g}×" for v in vals])


def growth_chart(series, log=True):
    """series: dict name -> growth of 1 (already normalised)."""
    fig = go.Figure()
    for name, g in series.items():
        fig.add_trace(go.Scatter(
            x=g.index, y=g.values, name=name, mode="lines",
            line=dict(color=COLORS.get(name, BLUE), width=2),
            hovertemplate="%{y:.2f}×"))

    if len(series) <= 4:
        # direct labels at the line ends, pushed apart so they don't overlap
        to_axis = np.log10 if log else (lambda v: v)
        lo = min(to_axis(g.min()) for g in series.values())
        hi = max(to_axis(g.max()) for g in series.values())
        gap = (hi - lo) * 0.06
        ends = sorted(series.items(), key=lambda kv: kv[1].iloc[-1])
        prev = None
        for name, g in ends:
            y = to_axis(g.iloc[-1])
            if prev is not None and y < prev + gap:
                y = prev + gap
            prev = y
            fig.add_annotation(x=g.index[-1], y=y, text=f"<b>{name}</b> {g.iloc[-1]:.2f}×", showarrow=False,
                               xanchor="left", xshift=6, font=dict(size=11, color=INK))
    style(fig, "Growth of $1 (total return, dividends reinvested)", log=log)
    if log:
        log_ticks(fig, min(g.min() for g in series.values()), max(g.max() for g in series.values()))
    else:
        fig.update_yaxes(tickformat=".1f", ticksuffix="×")
    fig.update_layout(margin=dict(r=100 if len(series) <= 4 else 12))
    return fig


def drawdown_chart(series):
    fig = go.Figure()
    for name, p in series.items():
        dd = p / p.cummax() - 1
        fig.add_trace(go.Scatter(
            x=dd.index, y=dd.values, name=name, mode="lines",
            line=dict(color=COLORS.get(name, BLUE), width=1.5),
            hovertemplate="%{y:.1%}"))
    style(fig, "Drawdown from previous peak", yformat=".0%", height=300)
    return fig


def simple_vs_log_chart(R, r, name):
    lim = [float(R.min()), float(R.max())]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines", name="log = simple",
                             line=dict(color=MUTED, width=1, dash="dash"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=R.values, y=r.values, mode="markers", name=f"{name} daily returns",
        marker=dict(color=BLUE, size=6, opacity=0.45, line=dict(width=0)),
        customdata=R.index.strftime("%d %b %Y"),
        hovertemplate="%{customdata}<br>simple %{x:.2%}<br>log %{y:.2%}<extra></extra>"))
    style(fig, "Each day: simple return vs log return", yformat=".0%", height=380)
    fig.update_xaxes(tickformat=".0%", title_text="simple return R", showspikes=False)
    fig.update_yaxes(title_text="log return ln(1+R)")
    fig.update_layout(hovermode="closest")
    return fig


def portfolio_chart(exact, wrong):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=exact.index, y=exact.values, name="Correct: weights × simple returns",
                             line=dict(color=BLUE, width=2), hovertemplate="%{y:.2f}×"))
    fig.add_trace(go.Scatter(x=wrong.index, y=wrong.values, name="Wrong: weights × log returns",
                             line=dict(color=ORANGE, width=2, dash="dot"), hovertemplate="%{y:.2f}×"))
    style(fig, "Portfolio growth of $1, rebalanced daily", log=True)
    log_ticks(fig, min(exact.min(), wrong.min()), max(exact.max(), wrong.max()))
    return fig


def two_currency_chart(pkr, usd):
    fig = go.Figure()
    for s, name, color in [(pkr / pkr.iloc[0], "OGDC in PKR", BLUE), (usd / usd.iloc[0], "OGDC in USD", ORANGE)]:
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=name,
                                 line=dict(color=color, width=2), hovertemplate="%{y:.2f}×"))
    fig.add_hline(y=1, line=dict(color=MUTED, width=1))
    style(fig, "OGDC: growth of 1, in rupees and in dollars")
    fig.update_yaxes(tickformat=".1f", ticksuffix="×")
    return fig


def fx_chart(clean, removed):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=clean.index, y=clean.values, name="USD/PKR (cleaned)",
                             line=dict(color=BLUE, width=1.5), hovertemplate="%{y:.2f}"))
    if len(removed):
        fig.add_trace(go.Scatter(x=removed.index, y=removed.values, name="removed bad quote",
                                 mode="markers", marker=dict(color=RED, size=7, symbol="x"),
                                 hovertemplate="%{y:.2f} (removed)"))
    style(fig, "USD/PKR: rupees per dollar, with removed quotes", height=360)
    return fig


def split_chart(raw_price, adj_price, splits, name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=raw_price.index, y=raw_price.values, name="Price that traded (unadjusted)",
                             line=dict(color=ORANGE, width=2), hovertemplate="$%{y:,.2f}"))
    fig.add_trace(go.Scatter(x=adj_price.index, y=adj_price.values, name="Split-adjusted price",
                             line=dict(color=BLUE, width=2), hovertemplate="$%{y:,.2f}"))
    for d, ratio in splits.items():
        fig.add_vline(x=d, line=dict(color=MUTED, width=1, dash="dot"))
        fig.add_annotation(x=d, y=1, yref="paper", text=f"{ratio:g}-for-1 split", showarrow=False,
                           xanchor="left", xshift=4, yanchor="top", font=dict(size=11, color=INK2))
    style(fig, f"{name}: split days look like crashes in unadjusted prices", log=True)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    return fig

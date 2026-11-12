# quant-finance-journey

My work for the 12-month quant finance roadmap (data science -> quant research).

## Progress

| Step | Topic | Output | Status |
|---|---|---|---|
| 1 | Markets & instruments | `notebooks/01_returns.ipynb`, `notes/what_is_a_share.md`, `src/returns.py` + tests | done, stooq comparison still to do |
| 2 | Time value of money | `tvm.py` + tests | |

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Run the tests:

```bash
.venv/bin/python -m pytest -q
```

Open the notebook:

```bash
.venv/bin/jupyter lab notebooks/01_returns.ipynb
```

Run the dashboard (Returns Lab, Streamlit):

```bash
.venv/bin/streamlit run app.py
```

Then open http://localhost:8501. It has six tabs: performance, simple vs log returns, portfolio maths, Pakistan (PKR vs USD), dividends & splits, and data quality.

The first run downloads the data from yahoo into `data/raw/yfinance/`. After that it reads the saved csv files. Every file is listed in `data/MANIFEST.csv` with its sha256 hash.

## Folders

- `app.py` - the Streamlit dashboard (theme in `.streamlit/config.toml`)
- `src/` - `returns.py` (return functions), `data.py` (download + cache + manifest), `analysis.py` and `charts.py` (used by the dashboard)
- `tests/` - pytest
- `notebooks/` - one notebook per week
- `notes/` - short notes
- `data/` - `MANIFEST.csv`, `quality_log.csv` (raw data is not committed)
- `figures/` - saved plots

## Stooq

stooq.com blocks scripted downloads (javascript browser check), so I download these by hand:
open `https://stooq.com/q/d/?s=spy.us`, click "Download data in csv file" at the bottom and save it in `data/raw/stooq/`.
Same for `efa.us eem.us tlt.us gld.us aapl.us nvda.us btcusd usdpkr`. The last part of the notebook compares them with yahoo.

## Data problems I found

- No KSE-100 index on yahoo (`^KSE` is empty), so I'm using OGDC.KA for now.
- PSX holidays show up in yahoo as days with zero volume and the previous close (132 days for OGDC). Dropped them.
- USD/PKR (`PKR=X`) is messy: 20% of the closes are outside the day's high-low range, and the close jumps between two sources. I removed 64 spikes with a rolling median filter, but the volatility is still too high. Need SBP data for that.
- `Close` is split-adjusted only, `Adj Close` also includes dividends. Using `Adj Close` for returns.

Not investment advice, just learning.

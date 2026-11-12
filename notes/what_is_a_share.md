# What is a share?

*Roadmap Step 1 · Week 1 · one-page note. Numbers come from `notebooks/01_returns.ipynb` (Nov 2016 – Oct 2026).*

## Definition

A **share** (or stock) is one equal slice of ownership in a company. If a company has 1,000,000 ordinary shares and you own 10,000, you own 1% of it. That 1% gives you three things:

1. **A residual claim on cash flows and assets.** Shareholders are paid *last*, after employees, suppliers, lenders and the tax authority. Whatever is left (profit) belongs to them. Some is paid out as **dividends**; the rest is retained and reinvested.
2. **Control rights.** Ordinary shares usually carry one vote each: to elect the board, approve mergers and so on.
3. **Limited liability.** The most you can lose is what you paid. If the company fails, creditors cannot come after your personal assets. Your loss is capped at −100% and your gain is unlimited.

**Preference shares** sit between debt and equity: a fixed dividend paid before ordinary shareholders, usually with no vote.

## Where shares come from and how they trade

* **Primary market:** the company *creates* shares and sells them for cash, in an IPO or a later rights issue (common on the PSX). The company receives the money.
* **Secondary market:** investors trade existing shares with each other on an exchange. The company receives nothing, but the price tells it what investors think it is worth and what new capital would cost.
* **Plumbing in Pakistan:** shares trade on the **Pakistan Stock Exchange** (PSX, formed in 2016 from the Karachi, Lahore and Islamabad exchanges). Trades are cleared and settled by **NCCPL**, and the shares are held electronically at the **CDC** (Central Depository Company). The **SECP** regulates the market. The US equivalents are NYSE/Nasdaq, DTCC and the SEC.

## What a share is worth

The price of a share is the market's estimate of the present value of all the cash it will ever pay its owner:

  P₀ = D₁/(1+k) + D₂/(1+k)² + … , where k is the return investors require for the risk.

**Market capitalisation** = price × shares outstanding = what the market says the whole equity is worth.

Two facts from the notebook make this concrete:

* **Splits do not create value.** In June 2024 NVIDIA split each share into 10. The quoted price fell about 90% overnight, but every holder had 10× as many shares. The true return that day was **+0.75%**, not −90%. A split cuts the cake into more slices; the cake stays the same size.
* **Dividends are part of the return.** The **total return** on a share is (P₁ − P₀ + D₁) / P₀. Over the 10 years, OGDC's price rose 114%, but with dividends reinvested an owner made **+343%** (in PKR). Yahoo's `Adj Close` already includes dividends; `Close` does not.

## Why shares are risky

Because shareholders are paid last, equity absorbs the company's good and bad luck first. It is the riskiest claim on a firm. SPY (the S&P 500) had a −34% drawdown in this sample, and single stocks can go to zero. For a Pakistani investor there is a second layer: **currency**. OGDC returned +343% in rupees but only **+68% in US dollars**, because the rupee fell from about 105 to about 275 per dollar over the same period.

## Share vs bond vs ETF vs index (the 2-minute version)

| | What you own | What you get | Main risk |
|---|---|---|---|
| **Share** | Part of one company | Residual profits (dividends + price growth), votes | Company does badly; you are paid last |
| **Bond** | A loan to a company or government | Fixed coupons + principal back at maturity | Default; rising interest rates lower its price |
| **ETF** | A share of a fund that holds a basket (e.g. SPY holds ~500 US stocks) | The basket's return minus a small fee | Whatever the basket holds |
| **Index** | Nothing. It is a **number** (e.g. KSE-100, S&P 500) that tracks a basket | You cannot buy it directly; you buy an ETF or fund that tracks it | Not applicable: it is a measurement, not an asset |

**One line:** a share is a limited-liability, last-in-line claim on a company's future profits, and its price is the market's present value of those profits.

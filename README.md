owner = Pini Goldenberg

# Nexa Treasury Case - Technical Appendix

This repo has the code behind the Nexa Treasury case study.

The case asks three questions about 2 March to 10 April 2026:

| | Question | Notebook |
| --- | --- | --- |
| A | Where is our cash, and does it reconcile to what we expected? | `task_a1_a2_a3_cash_position_n_reconciliation.ipynb` |
| B | How much FX exposure do we have, and what should we hedge? | `task_b1_b2_fx_expo_n_hedging.ipynb` |
| C | How healthy are our collections, and how do we answer the AR emails? | `task_c1_c2_c3_collections_n_ar_process.ipynb` |

## What is in the folders

| Path | What it is |
| --- | --- |
| `source_files/` | The raw input data from the case (bank report, expected collections, FX rates, subscription forecast, AR emails). Not modified. |
| `analytics_output/` | CSV files written by the notebooks. The dashboard reads these. |
| `db_visual_streamlit.py` | The dashboard (Streamlit). |
| `datasets_spec/` | The data specification that came with the case. |

## How to run it

**1. Install what you need** (Python 3.9 or newer):

```bash
pip install pandas "numpy<2" streamlit plotly jupyter
```

**2. Run the notebooks in this order** (open each one in Jupyter or VS Code and choose *Run All*):

1. Notebook A
2. Notebook B
3. Notebook C

Order matters only for C, which reads a file that A writes (`reconciliation_detail.csv`). Each notebook saves its results to `analytics_output/` in its last cell.

**3. Start the dashboard:**

```bash
streamlit run db_visual_streamlit.py
```

Then open the link Streamlit prints (usually http://localhost:8501). Use the menu on the left to switch between the overview and tasks A, B and C.


## Where to find the reasoning

Each notebook has short text cells that explain the method, the assumptions and what was fixed in the data. Start there if you want to understand a number. The main decisions are:

* **Cash (A):** balances use the *value date* and the daily mid rate for each date.
* **Reconciliation (A):** each bank receipt is matched to one expected item. Small gaps (under 0.5%) count as fees. Anything else is flagged with an owner and a next step.
* **FX (B):** exposure is collections minus refunds minus local costs, using the 10 April spot. Hedge sizes follow the policy ranges in the case.
* **AR (C):** the aging covers open customer invoices only, after taking out what has already been paid. Email decisions follow the credit policy and were checked against the bank data.

## Outputs at a glance

| File in `analytics_output/` | Written by | What it shows |
| --- | --- | --- |
| `cash_positions_summary.csv` | A | Cash by account and currency, local and USD, for 31 Mar and 10 Apr |
| `reconciliation_status_counts.csv`, `reconciliation_detail.csv` | A | Matched, timing difference or exception for every receipt |
| `detailed_exceptions_with_owners.csv` | A | Each exception with owner and next step |
| `timing_differences_summary.csv`, `exceptions_summary.csv` | A | Totals by entity, bank and currency |
| `forecast_net_fx_exposure_summary.csv`, `fx_monthly_exposure.csv` | B | FX exposure by currency and by month |
| `fx_rates_forward_analysis.csv`, `fx_hedging_recommendation.csv` | B | Forward rates and the hedging recommendation |
| `ar_aging_detailed.csv`, `ar_aging_by_bucket_currency.csv` | C | Open invoices and the aging |
| `ar_segment_performance.csv`, `ar_process_kpis.csv` | C | Collections health by segment and key process metrics |
| `ar_email_decision_matrix.csv` | C | Recommended response to each of the six emails |

## If something goes wrong

* **NumPy or pandas import errors:** install `numpy<2`, as in the command above.
* **Dashboard says a file is missing:** run the notebooks first (A, then B, then C).
* **Notebook cannot find a file:** open the notebook from this folder, so the relative paths work.

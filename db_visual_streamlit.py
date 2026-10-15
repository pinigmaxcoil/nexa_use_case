import numpy as np
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool_

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Page Configuration & Theme Styling
st.set_page_config(
    page_title="Nexa Treasury & AR Analytics",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #0f1117;
        color: #ffffff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e222b;
        border-radius: 6px;
        color: #ffffff;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0080ff !important;
        color: #ffffff !important;
    }
    div.metric-card {
        background-color: #1e222b;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2d333b;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Data Loading
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'analytics_output')

# All notebook output files; a missing file is simply not shown
FILES = {
    'cash': 'cash_positions_summary.csv',
    'recon': 'reconciliation_status_counts.csv',
    'timing': 'timing_differences_summary.csv',
    'exceptions': 'exceptions_summary.csv',
    'detailed_exc': 'detailed_exceptions_with_owners.csv',
    'fx_exp': 'forecast_net_fx_exposure_summary.csv',
    'fx_rates': 'fx_rates_forward_analysis.csv',
    'fx_reco': 'fx_hedging_recommendation.csv',
    'fx_monthly': 'fx_monthly_exposure.csv',
    'ar_aging': 'ar_aging_detailed.csv',
    'ar_segment': 'ar_segment_performance.csv',
    'ar_kpis': 'ar_process_kpis.csv',
}

# File modification times are part of the cache key, so re-running a notebook refreshes the data immediately
def files_signature():
    return tuple(
        os.path.getmtime(os.path.join(OUTPUT_DIR, name)) if os.path.exists(os.path.join(OUTPUT_DIR, name)) else 0
        for name in FILES.values()
    )

@st.cache_data
def load_data(signature):
    data = {}
    for key, name in FILES.items():
        path = os.path.join(OUTPUT_DIR, name)
        data[key] = pd.read_csv(path) if os.path.exists(path) else None
    return data

data = load_data(files_signature())
missing_files = [name for key, name in FILES.items() if data[key] is None]
if missing_files:
    st.warning(f"Missing output files in {OUTPUT_DIR}: {', '.join(missing_files)}. Run the notebooks first.")

cash_df, recon_df, timing_df = data['cash'], data['recon'], data['timing']
exceptions_df, detailed_exc_df = data['exceptions'], data['detailed_exc']
fx_exp_df, fx_rates_df, fx_reco_df, fx_monthly_df = data['fx_exp'], data['fx_rates'], data['fx_reco'], data['fx_monthly']
ar_aging_df, ar_segment_df, ar_kpis_df = data['ar_aging'], data['ar_segment'], data['ar_kpis']

# Consistent colors for the reconciliation statuses across all charts
STATUS_LABELS = {'matched': 'Matched', 'timing_difference': 'Timing difference', 'exception_or_followup': 'Exception / follow-up'}
STATUS_COLORS = {'Matched': '#2ecc71', 'Timing difference': '#f39c12', 'Exception / follow-up': '#e74c3c'}

def date_label(d):
    return pd.to_datetime(d).strftime('%d %b %Y')

# 3. Sidebar Navigation
st.sidebar.title("Nexa")
st.sidebar.caption("Treasury & AR Analytics")
st.sidebar.markdown("---")

story_mode = st.sidebar.radio(
    "Navigation:",
    ["Overview", "Task A: Cash & Reconciliation", "Task B: FX Exposure & Hedging", "Task C: AR Aging & Collections"]
)

# 4. Main Content Switcher
if story_mode == "Overview":
    st.title("Nexa Treasury & Collections Dashboard")
    st.caption("Cash position, FX exposure and accounts receivable at a glance.")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    if cash_df is not None:
        dates = sorted(cash_df['target_date'].unique())
        total_latest = cash_df[cash_df['target_date'] == dates[-1]]['balance_usd'].sum()
        total_prev = cash_df[cash_df['target_date'] == dates[0]]['balance_usd'].sum()
        col1.metric(f"Total Cash ({date_label(dates[-1])})", f"${total_latest / 1e6:,.1f}M",
                    f"{(total_latest - total_prev) / 1e6:+,.1f}M vs {date_label(dates[0])}")
    if recon_df is not None:
        matched = recon_df[recon_df['status'] == 'matched']['count'].sum()
        col2.metric("Receipts Reconciled", f"{matched / recon_df['count'].sum() * 100:.0f}%",
                    f"{recon_df[recon_df['status'] == 'exception_or_followup']['count'].sum()} exceptions", delta_color="off")
    if fx_reco_df is not None:
        material = fx_reco_df[fx_reco_df['is_material']]
        col3.metric("Proposed New Hedges", f"${material['additional_hedge_usd_000s'].sum() / 1e3:,.0f}M",
                    f"{len(material)} material currencies", delta_color="off")
    if ar_aging_df is not None:
        open_ar = ar_aging_df[ar_aging_df['open_amount'] > 0]
        overdue_share = open_ar[open_ar['days_overdue'] > 0]['open_amount_usd'].sum() / open_ar['open_amount_usd'].sum() * 100
        col4.metric("Open AR", f"${open_ar['open_amount_usd'].sum() / 1e6:,.2f}M",
                    f"{overdue_share:.0f}% overdue", delta_color="off")

    st.markdown("---")
    st.markdown(
        "Use the sidebar to explore **Cash & Reconciliation**, **FX Exposure & Hedging**, "
        "and **AR Aging & Collections**."
    )

elif story_mode == "Task A: Cash & Reconciliation":
    st.title("📊 Task A: Cash Positions & Bank Reconciliation")
    st.markdown("Where is our cash, and does it reconcile to what we expected to receive?")

    if cash_df is not None:
        dates = sorted(cash_df['target_date'].unique())
        st.subheader("💰 Cash Position by Account and Currency")
        st.caption("Basis: value date (cleared funds), converted to USD at the latest daily mid spot rate on or before each date.")

        metric_cols = st.columns(len(dates))
        for col, d in zip(metric_cols, dates):
            col.metric(f"Total cash {date_label(d)}", f"${cash_df[cash_df['target_date'] == d]['balance_usd'].sum() / 1e6:,.1f}M")

        selected_date = st.radio("Chart date", dates, index=len(dates) - 1, format_func=date_label, horizontal=True)
        by_currency = cash_df[cash_df['target_date'] == selected_date].groupby('currency', as_index=False)['balance_usd'].sum()
        fig_cash = px.bar(
            by_currency.sort_values('balance_usd', ascending=False),
            x='currency', y='balance_usd', color='currency', text_auto='.3s',
            title=f"Cash by currency in USD (as of {date_label(selected_date)})",
            labels={'balance_usd': 'USD', 'currency': 'Currency'},
            template="plotly_dark"
        )
        fig_cash.update_layout(showlegend=False)
        st.plotly_chart(fig_cash, use_container_width=True)

        # One table: local and USD balances for both dates, per account and currency
        key_cols = ['account_number', 'entity', 'bank', 'currency']
        cash_table = cash_df[key_cols].drop_duplicates()
        for d in dates:
            part = cash_df[cash_df['target_date'] == d][key_cols + ['running_balance', 'balance_usd']].rename(
                columns={'running_balance': f"{date_label(d)} (local)", 'balance_usd': f"{date_label(d)} (USD)"})
            cash_table = cash_table.merge(part, on=key_cols, how='left')
        number_cols = [c for c in cash_table.columns if c not in key_cols]
        st.dataframe(cash_table.style.format({c: '{:,.0f}' for c in number_cols}), use_container_width=True, hide_index=True)

    if recon_df is not None:
        st.subheader("🔍 Reconciliation: Actual Receipts vs Expected Collections")
        recon_plot = recon_df.assign(status=recon_df['status'].map(STATUS_LABELS))
        status_cols = st.columns(len(recon_plot))
        for col, (_, r) in zip(status_cols, recon_plot.iterrows()):
            col.metric(r['status'], int(r['count']))

        col1, col2 = st.columns(2)
        with col1:
            fig_recon = px.pie(
                recon_plot, names='status', values='count', hole=0.4, color='status',
                color_discrete_map=STATUS_COLORS,
                title="Receipts by reconciliation status", template="plotly_dark"
            )
            st.plotly_chart(fig_recon, use_container_width=True)
        with col2:
            if detailed_exc_df is not None:
                by_reason = detailed_exc_df.groupby('exception_reason', as_index=False).size().rename(columns={'size': 'count'})
                fig_reason = px.bar(
                    by_reason.sort_values('count'), x='count', y='exception_reason', orientation='h',
                    title="Exceptions by type", labels={'exception_reason': '', 'count': 'Items'},
                    template="plotly_dark"
                )
                st.plotly_chart(fig_reason, use_container_width=True)

    if detailed_exc_df is not None:
        st.subheader("⚠️ Exceptions: Owner and Next Step")
        exc_view = detailed_exc_df[['exception_reason', 'entity', 'currency', 'amount', 'unmatched_amount', 'expected_id',
                                    'bank_reference', 'assigned_owner', 'next_step']]
        st.dataframe(
            exc_view.style.format({'amount': '{:,.2f}', 'unmatched_amount': '{:,.2f}'}),
            use_container_width=True, hide_index=True
        )

    if timing_df is not None:
        with st.expander("⏱️ Timing differences by entity (value date more than 3 days from expected)"):
            st.dataframe(timing_df, use_container_width=True, hide_index=True)

elif story_mode == "Task B: FX Exposure & Hedging":
    st.title("🌐 Task B: Net FX Exposure & Hedging Strategy")
    st.markdown("Forecast net exposure for April to September 2026 and the proposed hedging action per currency.")

    if fx_exp_df is not None:
        st.subheader("📈 Net Exposure by Currency (USD Equivalents)")
        exposure_plot = fx_exp_df.sort_values('total_gross_exposure_usd_000s', ascending=False)[
            ['currency', 'total_gross_exposure_usd_000s', 'total_net_exposure_usd_000s']].melt(
            id_vars='currency', var_name='type', value_name='usd_000s')
        exposure_plot['type'] = exposure_plot['type'].map({
            'total_gross_exposure_usd_000s': 'Before existing hedges',
            'total_net_exposure_usd_000s': 'After existing hedges'})
        exposure_plot['usd_m'] = exposure_plot['usd_000s'] / 1000
        fig_fx = px.bar(
            exposure_plot, x='currency', y='usd_m', color='type', barmode='group',
            title="Total net FX exposure Apr-Sep 2026 (USD millions; negative = net buyer of the currency)",
            labels={'usd_m': 'USD millions', 'currency': 'Currency', 'type': ''},
            template="plotly_dark"
        )
        st.plotly_chart(fig_fx, use_container_width=True)

        exposure_table = fx_exp_df.sort_values('total_gross_exposure_usd_000s', ascending=False)[[
            'currency', 'total_gross_exposure_lc_000s', 'existing_hedges_lc_000s', 'total_net_exposure_lc_000s',
            'total_gross_exposure_usd_000s', 'existing_hedges_usd_000s', 'total_net_exposure_usd_000s',
            'avg_monthly_exposure_usd_000s', 'is_material']].rename(columns={
            'total_gross_exposure_lc_000s': 'Exposure (LC 000s)', 'existing_hedges_lc_000s': 'Existing hedges (LC 000s)',
            'total_net_exposure_lc_000s': 'Open exposure (LC 000s)', 'total_gross_exposure_usd_000s': 'Exposure (USD 000s)',
            'existing_hedges_usd_000s': 'Existing hedges (USD 000s)', 'total_net_exposure_usd_000s': 'Open exposure (USD 000s)',
            'avg_monthly_exposure_usd_000s': 'Avg monthly (USD 000s)', 'is_material': 'Material (>= USD 1M / month)'})
        number_cols = [c for c in exposure_table.columns if c not in ('currency', 'Material (>= USD 1M / month)')]
        st.dataframe(exposure_table.style.format({c: '{:,.0f}' for c in number_cols}), use_container_width=True, hide_index=True)

    if fx_monthly_df is not None and fx_exp_df is not None:
        material_ccy = fx_exp_df[fx_exp_df['is_material']]['currency'].tolist()
        monthly_plot = fx_monthly_df[fx_monthly_df['currency'].isin(material_ccy)].assign(
            usd_m=lambda d: d['net_exposure_gross_usd_000s'] / 1000)
        fig_monthly = px.bar(
            monthly_plot, x='month', y='usd_m', color='currency',
            title="Monthly net exposure of material currencies (USD millions)",
            labels={'usd_m': 'USD millions', 'month': 'Month'}, template="plotly_dark"
        )
        st.plotly_chart(fig_monthly, use_container_width=True)

    if fx_reco_df is not None:
        st.subheader("🛡️ Hedging Recommendation by Currency")
        st.caption("Policy: currencies below USD 1.0M average monthly exposure are not hedged. Target cover is 50-80% for months 1-3 "
                   "and 25-50% for months 4-6, including hedges already in place. Options are not used.")
        reco_view = fx_reco_df[['currency', 'direction', 'avg_monthly_exposure_usd_000s', 'existing_cover_pct_m1_3',
                                'target_pct_m1_3', 'target_pct_m4_6', 'additional_hedge_usd_000s', 'fwd_benefit_3m_pct',
                                'fwd_benefit_6m_pct', 'est_fwd_benefit_usd_000s', 'instrument', 'rationale']].rename(columns={
            'direction': 'Action', 'avg_monthly_exposure_usd_000s': 'Avg monthly (USD 000s)',
            'existing_cover_pct_m1_3': 'Existing cover M1-3 (%)', 'target_pct_m1_3': 'Target M1-3 (%)',
            'target_pct_m4_6': 'Target M4-6 (%)', 'additional_hedge_usd_000s': 'New hedge (USD 000s)',
            'fwd_benefit_3m_pct': 'Fwd vs spot 3m (%)', 'fwd_benefit_6m_pct': 'Fwd vs spot 6m (%)',
            'est_fwd_benefit_usd_000s': 'Est. fwd cost/benefit (USD 000s)', 'instrument': 'Instrument', 'rationale': 'Rationale'})
        pct_fmt = {'Existing cover M1-3 (%)': '{:.0f}', 'Target M1-3 (%)': '{:.1f}', 'Target M4-6 (%)': '{:.1f}',
                   'Fwd vs spot 3m (%)': '{:+.2f}', 'Fwd vs spot 6m (%)': '{:+.2f}'}
        usd_fmt = {c: '{:,.0f}' for c in ['Avg monthly (USD 000s)', 'New hedge (USD 000s)', 'Est. fwd cost/benefit (USD 000s)']}
        st.dataframe(reco_view.style.format({**pct_fmt, **usd_fmt}), use_container_width=True, hide_index=True)

        fwd_plot = fx_reco_df[fx_reco_df['is_material']].melt(
            id_vars='currency', value_vars=['fwd_benefit_3m_pct', 'fwd_benefit_6m_pct'], var_name='horizon', value_name='pct')
        fwd_plot['horizon'] = fwd_plot['horizon'].map({'fwd_benefit_3m_pct': '3 months', 'fwd_benefit_6m_pct': '6 months'})
        fig_fwd = px.bar(
            fwd_plot, x='currency', y='pct', color='horizon', barmode='group',
            title="Forward vs spot for the hedging side (positive = benefit, negative = cost, %)",
            labels={'pct': '%', 'currency': 'Currency', 'horizon': ''}, template="plotly_dark"
        )
        st.plotly_chart(fig_fwd, use_container_width=True)

        with st.expander("What would change this recommendation?"):
            st.markdown(
                "- A forecast change of more than ~10% in collections or local costs for a material currency.\n"
                "- Forward points that turn a benefit into a cost (or the opposite).\n"
                "- A sharp spot move or a change in hedging policy.\n"
                "- BRL: approval or refusal of an NDF by the Director of Treasury.\n"
                "- ILS: a change in the payroll plan."
            )

    if fx_rates_df is not None:
        with st.expander("💱 FX rates and forward points (10 Apr 2026)"):
            st.dataframe(fx_rates_df[['currency', 'quote_convention', 'spot_mid', 'fwd_rate_3m', 'fwd_rate_6m',
                                      'fwd_cost_benefit_3m_pct', 'fwd_cost_benefit_6m_pct']],
                         use_container_width=True, hide_index=True)

elif story_mode == "Task C: AR Aging & Collections":
    st.title("📑 Task C: AR Aging & Collections")
    st.markdown("How healthy are our collections? Open receivables, aging and process efficiency as of 10 April 2026.")

    if ar_aging_df is not None:
        open_ar = ar_aging_df[ar_aging_df['open_amount'] > 0]
        overdue_ar = open_ar[open_ar['days_overdue'] > 0]

        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Open AR", f"${open_ar['open_amount_usd'].sum() / 1e6:,.2f}M", f"{len(open_ar)} invoices", delta_color="off")
        kpi_cols[1].metric("Overdue", f"${overdue_ar['open_amount_usd'].sum() / 1e6:,.2f}M",
                           f"{overdue_ar['open_amount_usd'].sum() / open_ar['open_amount_usd'].sum() * 100:.0f}% of open AR", delta_color="off")
        kpi_cols[2].metric("90+ days overdue", f"${open_ar[open_ar['aging_bucket'] == '05. 90+ Days']['open_amount_usd'].sum() / 1e3:,.0f}K")
        if ar_kpis_df is not None:
            unapplied = ar_kpis_df[(ar_kpis_df['metric'] == 'Unapplied receipts') & (ar_kpis_df['unit'] == 'USD')]['value']
            kpi_cols[3].metric("Unapplied cash", f"${unapplied.sum() / 1e3:,.0f}K")

        st.subheader("📊 AR Aging as of 10 April 2026 (USD)")
        col1, col2 = st.columns(2)
        with col1:
            by_bucket = open_ar.groupby('aging_bucket', as_index=False)['open_amount_usd'].sum()
            fig_bucket = px.bar(
                by_bucket, x='aging_bucket', y='open_amount_usd', text_auto='.3s',
                title="Open AR by aging bucket", labels={'aging_bucket': '', 'open_amount_usd': 'USD'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_bucket, use_container_width=True)
        with col2:
            by_segment = open_ar.groupby(['aging_bucket', 'segment'], as_index=False)['open_amount_usd'].sum()
            fig_segment = px.bar(
                by_segment, x='aging_bucket', y='open_amount_usd', color='segment', barmode='stack',
                title="Aging by segment", labels={'aging_bucket': '', 'open_amount_usd': 'USD', 'segment': ''},
                template="plotly_dark"
            )
            st.plotly_chart(fig_segment, use_container_width=True)

        by_currency = open_ar.pivot_table(index='currency', columns='aging_bucket', values='open_amount_usd',
                                          aggfunc='sum', fill_value=0)
        by_currency['Total'] = by_currency.sum(axis=1)
        st.markdown("**Aging by currency (USD)**")
        st.dataframe(by_currency.sort_values('Total', ascending=False).style.format('{:,.0f}'), use_container_width=True)

        st.markdown("**Largest overdue items**")
        top_overdue = overdue_ar.sort_values('open_amount_usd', ascending=False).head(10)[[
            'collection_id', 'customer_or_psp', 'segment', 'currency', 'open_amount', 'open_amount_usd',
            'days_overdue', 'sales_owner']]
        st.dataframe(top_overdue.style.format({'open_amount': '{:,.0f}', 'open_amount_usd': '{:,.0f}'}),
                     use_container_width=True, hide_index=True)

    if ar_segment_df is not None or ar_kpis_df is not None:
        st.subheader("⚙️ Process Efficiency")
        col1, col2 = st.columns(2)
        if ar_segment_df is not None:
            with col1:
                st.markdown("**Performance by segment**")
                st.dataframe(ar_segment_df.style.format(
                    {c: '{:,.1f}' for c in ar_segment_df.columns if c != 'segment'}), use_container_width=True, hide_index=True)
        if ar_kpis_df is not None:
            with col2:
                st.markdown("**Key process metrics**")
                st.dataframe(ar_kpis_df.style.format({'value': '{:,.1f}'}), use_container_width=True, hide_index=True)

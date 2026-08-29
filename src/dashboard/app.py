from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

STATE = Path(__file__).resolve().parent / "public_data" / "f2r_public_state.json"


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * float(x):.{digits}f}%"


def load_state() -> dict:
    if not STATE.is_file():
        st.error("No approved F2R public state is available.")
        st.stop()
    return json.loads(STATE.read_text(encoding="utf-8"))


def dark_chart(chart: alt.Chart, height: int) -> alt.Chart:
    return (
        chart.properties(height=height)
        .configure(background="#091018")
        .configure_view(strokeOpacity=0)
        .configure_axis(
            gridColor="#21303a",
            domainColor="#21303a",
            tickColor="#21303a",
            labelColor="#82909c",
            titleColor="#82909c",
            labelFontSize=11,
            titleFontSize=11,
        )
        .configure_legend(labelColor="#9aa7b2", titleColor="#9aa7b2", labelFontSize=11, orient="top")
    )


def render_table(df: pd.DataFrame, history: bool = False, scroll: bool = False) -> None:
    classes = ["f2r-table-wrap"]
    if history:
        classes.append("history")
    if scroll:
        classes.append("scroll")
    table_html = df.to_html(index=False, border=0, classes="f2r-table", escape=True)
    st.markdown(f'<div class="{" ".join(classes)}">{table_html}</div>', unsafe_allow_html=True)


def holding_grid(holdings: list[dict], preview: bool = False) -> None:
    cols = st.columns(4)
    for col, holding in zip(cols, holdings):
        with col:
            role = "preview" if preview else "official"
            label = "preview" if preview else "target"
            st.markdown(
                f'''<div class="holding {role}">
                    <div class="rank">RANK {int(holding["rank"])}</div>
                    <div class="asset">{holding["asset"]}</div>
                    <div class="weight">{pct(holding["target_weight"], 0)} {label}</div>
                </div>''',
                unsafe_allow_html=True,
            )


doc = load_state()
system = doc["system"]
live = doc["live_state"]
official = live["official"]
preview = live["preview"]
transition = live["transition"]
perf = doc["historical_research_performance"]
history = doc["historical_targets"]
evidence = doc["evidence_boundary"]

st.set_page_config(page_title="F2R · Forecast-to-Rank Allocation", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown(r'''
<style>
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
.stApp{background:#091018;color:#eef3f6}.block-container{max-width:1500px;padding-top:1rem;padding-bottom:3.5rem}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}h1,h2,h3{letter-spacing:-.035em}
.shell{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid #1d2933}.brand{display:flex;align-items:center;gap:.8rem}.mark{width:42px;height:42px;border-radius:11px;background:#eef3f6;color:#091018;display:flex;align-items:center;justify-content:center;font-size:.82rem;font-weight:900}.name{font-size:1.08rem;font-weight:800}.desc{font-size:.69rem;letter-spacing:.09em;color:#71808d;text-transform:uppercase;margin-top:.1rem}.mode{border:1px solid #315f3e;background:#102319;color:#9fe3b1;border-radius:999px;padding:.43rem .72rem;font-size:.68rem;font-weight:800;letter-spacing:.09em}.mode-wrap{text-align:right}.refresh{font-size:.58rem;color:#667681;margin-top:.32rem}
.hero{padding:1.15rem 0 .55rem}.eyebrow,.sk{font-size:.63rem;letter-spacing:.14em;color:#71818e;text-transform:uppercase;font-weight:800}.hero-title{font-size:clamp(2.1rem,3.6vw,3.75rem);font-weight:790;letter-spacing:-.052em;line-height:1.02;margin-top:.34rem}.hero-copy{font-size:.97rem;line-height:1.63;color:#98a5b0;max-width:930px;margin-top:.7rem}
.health,.metrics,.boundary{display:grid;gap:.65rem}.health{grid-template-columns:repeat(4,minmax(0,1fr));margin:.85rem 0 1.15rem}.metrics{grid-template-columns:repeat(6,minmax(0,1fr));margin:.8rem 0 1rem}.boundary{grid-template-columns:repeat(4,minmax(0,1fr));margin:.8rem 0}.cell,.metric,.bcell{background:#0f1821;border:1px solid #22313d;border-radius:10px;padding:.85rem .92rem}.hl,.ml,.bl{font-size:.58rem;letter-spacing:.1em;color:#6d7b87;text-transform:uppercase;font-weight:800}.hv,.bv{font-size:.98rem;color:#eef3f6;font-weight:750;margin-top:.28rem}.hs,.ms,.bs{font-size:.64rem;color:#697784;margin-top:.2rem;line-height:1.45}.mv{font-size:1.35rem;color:#eef3f6;font-weight:800;margin-top:.35rem}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:2rem 0 .8rem}.stitle{font-size:1.52rem;font-weight:790;letter-spacing:-.035em}.snote{font-size:.68rem;color:#6d7d89}.decision{background:#0f1821;border:1px solid #22313d;border-radius:12px;padding:1rem}.decision.official{border-top:3px solid #43b4d9}.decision.preview{border-top:3px solid #d0a03a}.decision-head{display:flex;justify-content:space-between;align-items:center;margin:.35rem 0 .8rem}.decision-title{font-size:1.13rem;font-weight:800}.decision-date{font-size:.66rem;color:#71818d}.holding{background:#09131b;border:1px solid #20303b;border-radius:9px;padding:.78rem}.holding.official{border-top:2px solid #43b4d9}.holding.preview{border-top:2px solid #d0a03a}.rank{font-size:.54rem;color:#687985;letter-spacing:.1em;font-weight:800}.asset{font-size:1.25rem;font-weight:850;margin:.42rem 0}.weight{font-size:.63rem;color:#70818e}.authority{font-size:.66rem;color:#758692;margin-top:.72rem}.transition{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:.65rem;margin-top:.75rem}.enter{border-color:#285d40}.leave{border-color:#6b3f39}
.arch{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem}.step{background:#0e1720;border:1px solid #22313d;border-radius:10px;padding:1rem}.step-n{font-size:.55rem;color:#71818d;letter-spacing:.11em;font-weight:800}.step-t{font-size:.9rem;font-weight:800;margin:.45rem 0}.step-d{font-size:.66rem;color:#73838f;line-height:1.5}
.f2r-table-wrap{overflow-x:auto;border:1px solid #22313d;border-radius:10px;background:#0e1720;margin-top:.55rem}table.f2r-table{width:100%;border-collapse:collapse;font-size:.74rem;color:#dfe6ea}table.f2r-table th{background:#111c25;color:#83929d;font-size:.58rem;letter-spacing:.075em;text-transform:uppercase;padding:.7rem;border-bottom:1px solid #22313d;text-align:center;white-space:nowrap}table.f2r-table td{padding:.65rem .7rem;border-bottom:1px solid #1b2933;text-align:center;white-space:nowrap}table.f2r-table tr:last-child td{border-bottom:none}.f2r-table-wrap.history table{table-layout:fixed}.f2r-table-wrap.history.scroll{max-height:560px;overflow:auto}.f2r-table-wrap.history.scroll thead th{position:sticky;top:0;z-index:2}
.note{border:1px solid #22313d;background:#0d1720;border-radius:10px;padding:.9rem;color:#82919c;font-size:.71rem;line-height:1.55}.public-note{border-left:3px solid #376e89;background:#0b1821;border-radius:7px;padding:.9rem 1rem;color:#84949f;font-size:.72rem;line-height:1.55}
[data-baseweb="tab-list"]{gap:1.35rem;border-bottom:1px solid #172630}button[data-baseweb="tab"]{padding:.75rem 0;color:#677783}button[data-baseweb="tab"][aria-selected="true"]{color:#f15b59;border-bottom:2px solid #f15b59}
@media(max-width:1000px){.block-container{padding-left:1rem;padding-right:1rem}.health,.metrics,.boundary{grid-template-columns:repeat(2,1fr)}.arch,.transition{grid-template-columns:1fr 1fr}}
</style>
''', unsafe_allow_html=True)

preview_period = preview["signal_period"] if preview["available"] else "Unavailable"
preview_cutoff = preview.get("market_cutoff_date") or "—"
plural = "s" if transition["change_count"] != 1 else ""

st.markdown(f'''<div class="shell"><div class="brand"><div class="mark">F2R</div><div><div class="name">Forecast-to-Rank Allocation</div><div class="desc">Portfolio Strategy System</div></div></div><div class="mode-wrap"><div class="mode">PUBLIC LIVE</div><div class="refresh">State issued {doc["issued_at_display"]}</div></div></div>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><div class="eyebrow">Decision cockpit</div><div class="hero-title">Forecast-ranked allocation, live.</div><div class="hero-copy">Asset-level machine-learning forecasts are converted into relative cross-asset ranks and a disciplined monthly portfolio decision. The authoritative target and provisional next-state estimate are kept explicitly separate.</div></div>', unsafe_allow_html=True)
st.markdown(f'''<div class="health"><div class="cell"><div class="hl">Official signal</div><div class="hv">{official["signal_period"]}</div><div class="hs">Authoritative target</div></div><div class="cell"><div class="hl">Preview signal</div><div class="hv">{preview_period}</div><div class="hs">Provisional next state</div></div><div class="cell"><div class="hl">Preview cutoff</div><div class="hv">{preview_cutoff}</div><div class="hs">Latest admissible close</div></div><div class="cell"><div class="hl">Preview change</div><div class="hv">{transition["change_count"]} swap{plural}</div><div class="hs">{transition["summary"]}</div></div></div>''', unsafe_allow_html=True)

tabs = st.tabs(["Live Decision", "Performance", "Portfolio History", "System & Evidence"])

with tabs[0]:
    st.markdown('<div class="section-head"><div><div class="sk">Current decision</div><div class="stitle">Current allocation and next-state preview</div></div><div class="snote">Blue = authoritative · amber = provisional</div></div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="decision official"><div class="decision-head"><div class="decision-title">Official Decision</div><div class="decision-date">{official["signal_period"]}</div></div>', unsafe_allow_html=True)
        holding_grid(official["holdings"])
        st.markdown(f'<div class="authority">{official["state_note"]}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="decision preview"><div class="decision-head"><div class="decision-title">Intramonth Preview</div><div class="decision-date">{preview_period}</div></div>', unsafe_allow_html=True)
        if preview["available"]:
            holding_grid(preview["holdings"], preview=True)
            st.markdown(f'<div class="authority">{preview["state_note"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="note">Preview is unavailable in the approved public state. No stale target is carried forward.</div></div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="transition"><div class="cell"><div class="hl">Retained</div><div class="hv">{", ".join(transition["retained"]) or "—"}</div></div><div class="cell enter"><div class="hl">Entering</div><div class="hv">{", ".join(transition["entering"]) or "—"}</div></div><div class="cell leave"><div class="hl">Leaving</div><div class="hv">{", ".join(transition["leaving"]) or "—"}</div></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div><div class="sk">Decision architecture</div><div class="stitle">From forecast to portfolio</div></div><div class="snote">Relative ordering, not raw forecast magnitude</div></div>', unsafe_allow_html=True)
    st.markdown('''<div class="arch"><div class="step"><div class="step-n">01 · FORECAST</div><div class="step-t">Asset-level ML forecasts</div><div class="step-d">Estimate forward returns for each eligible asset under the frozen live specification.</div></div><div class="step"><div class="step-n">02 · RANK</div><div class="step-t">Cross-asset ordering</div><div class="step-d">Convert forecasts into within-universe relative ranks.</div></div><div class="step"><div class="step-n">03 · ENSEMBLE</div><div class="step-t">Rank aggregation</div><div class="step-d">Combine model-specific rankings into one opportunity ordering.</div></div><div class="step"><div class="step-n">04 · ALLOCATE</div><div class="step-t">Top-4 target</div><div class="step-d">Translate the final ordering into an equal-weight monthly target.</div></div></div>''', unsafe_allow_html=True)

with tabs[1]:
    m = perf["metrics"]
    st.markdown('<div class="section-head"><div><div class="sk">Historical research evidence</div><div class="stitle">Performance & risk</div></div><div class="snote">Research backtest · not forward-live performance</div></div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="metrics"><div class="metric"><div class="ml">CAGR</div><div class="mv">{pct(m["cagr"])}</div><div class="ms">{perf["coverage"]}</div></div><div class="metric"><div class="ml">Ann. volatility</div><div class="mv">{pct(m["ann_vol"])}</div><div class="ms">Annualized</div></div><div class="metric"><div class="ml">Excess Sharpe</div><div class="mv">{m["excess_sharpe"]:.2f}</div><div class="ms">vs. BIL</div></div><div class="metric"><div class="ml">Max drawdown</div><div class="mv">{pct(m["max_drawdown"])}</div><div class="ms">Research history</div></div><div class="metric"><div class="ml">Avg turnover</div><div class="mv">{pct(m["avg_turnover"])}</div><div class="ms">Monthly</div></div><div class="metric"><div class="ml">Positive months</div><div class="mv">{pct(m["positive_months"])}</div><div class="ms">Hit rate</div></div></div>''', unsafe_allow_html=True)
    growth = pd.DataFrame(perf["growth_series"])
    growth["month_dt"] = pd.to_datetime(growth["month"] + "-01")
    growth_chart = alt.Chart(growth).mark_line(strokeWidth=2).encode(x=alt.X("month_dt:T", title=None, axis=alt.Axis(format="%Y", tickCount=9, labelAngle=0)), y=alt.Y("growth:Q", title="Growth of $1"), color=alt.Color("series:N", title=None), tooltip=[alt.Tooltip("month:N", title="Month"), "series:N", alt.Tooltip("growth:Q", format=".2f")])
    st.altair_chart(dark_chart(growth_chart, 350), use_container_width=True)
    dd = pd.DataFrame(perf["drawdown_series"])
    dd["month_dt"] = pd.to_datetime(dd["month"] + "-01")
    dd_chart = alt.Chart(dd).mark_area(opacity=.75).encode(x=alt.X("month_dt:T", title=None, axis=alt.Axis(format="%Y", tickCount=9, labelAngle=0)), y=alt.Y("drawdown:Q", title="F2R drawdown", axis=alt.Axis(format="%")), tooltip=[alt.Tooltip("month:N", title="Month"), alt.Tooltip("drawdown:Q", format=".1%")])
    st.altair_chart(dark_chart(dd_chart, 230), use_container_width=True)
    st.markdown('<div class="section-head"><div><div class="sk">Research comparison</div><div class="stitle">Information-set evidence</div></div><div class="snote">Comparators do not redefine the live F2R identity</div></div>', unsafe_allow_html=True)
    comparison = pd.DataFrame(perf["information_set_comparison"])
    comparison["CAGR"] = comparison["cagr"].map(pct); comparison["Ann. Vol"] = comparison["ann_vol"].map(pct); comparison["Excess Sharpe"] = comparison["excess_sharpe"].map(lambda x: f"{x:.2f}"); comparison["Max DD"] = comparison["max_drawdown"].map(pct)
    render_table(comparison[["Series", "CAGR", "Ann. Vol", "Excess Sharpe", "Max DD"]])

with tabs[2]:
    hm = history["metrics"]
    st.markdown('<div class="section-head"><div><div class="sk">Allocation history</div><div class="stitle">Certified historical target path</div></div><div class="snote">Research signal-month targets · not execution records</div></div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="metrics"><div class="metric"><div class="ml">Coverage</div><div class="mv">{hm["months"]} mo</div><div class="ms">{history["coverage"]}</div></div><div class="metric"><div class="ml">Target records</div><div class="mv">{hm["target_rows"]}</div><div class="ms">Four per month</div></div><div class="metric"><div class="ml">Avg changes</div><div class="mv">{hm["avg_changes"]:.2f}</div><div class="ms">Entering assets</div></div><div class="metric"><div class="ml">No-change months</div><div class="mv">{hm["no_change_months"]}</div><div class="ms">Same selected set</div></div><div class="metric"><div class="ml">Most selected</div><div class="mv">{hm["most_selected_asset"]}</div><div class="ms">{hm["most_selected_months"]} months</div></div><div class="metric"><div class="ml">Target weight</div><div class="mv">25%</div><div class="ms">Equal weight</div></div></div>''', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1])
    with left:
        freq = pd.DataFrame(history["selection_frequency"])
        freq_chart = alt.Chart(freq).mark_bar().encode(x=alt.X("asset:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("selection_rate:Q", title="Share of months selected", axis=alt.Axis(format="%")), tooltip=["asset:N", alt.Tooltip("selected_months:Q", format="d"), alt.Tooltip("selection_rate:Q", format=".1%")])
        st.altair_chart(dark_chart(freq_chart, 260), use_container_width=True)
    with right:
        changes = pd.DataFrame(history["monthly_changes"]); changes["month_dt"] = pd.to_datetime(changes["month"] + "-01")
        change_chart = alt.Chart(changes).mark_bar().encode(x=alt.X("month_dt:T", title=None, axis=alt.Axis(format="%Y", tickCount=9, labelAngle=0)), y=alt.Y("changes:Q", title="Entering assets", scale=alt.Scale(domain=[0, 4])), tooltip=[alt.Tooltip("month:N"), alt.Tooltip("changes:Q", format="d")])
        st.altair_chart(dark_chart(change_chart, 260), use_container_width=True)
    recent = pd.DataFrame(history["recent_12"]).rename(columns={"month":"Signal Month","rank1":"Rank 1","rank2":"Rank 2","rank3":"Rank 3","rank4":"Rank 4","changes":"Changes vs Prior"})
    recent = recent[["Signal Month","Rank 1","Rank 2","Rank 3","Rank 4","Changes vs Prior"]]
    st.markdown('<div class="section-head"><div><div class="sk">Recent target path</div><div class="stitle">Latest 12 certified signal months</div></div><div class="snote">Newest first</div></div>', unsafe_allow_html=True)
    render_table(recent, history=True)
    with st.expander("Full 112-month certified target history"):
        order = st.selectbox("Signal month order", ["Newest first", "Oldest first"], index=0)
        full = pd.DataFrame(history["full_history"]).sort_values("month", ascending=(order == "Oldest first")).rename(columns={"month":"Signal Month","rank1":"Rank 1","rank2":"Rank 2","rank3":"Rank 3","rank4":"Rank 4","changes":"Changes vs Prior"})
        full = full[["Signal Month","Rank 1","Rank 2","Rank 3","Rank 4","Changes vs Prior"]]
        render_table(full, history=True, scroll=True)

with tabs[3]:
    st.markdown('<div class="section-head"><div><div class="sk">System identity</div><div class="stitle">System identity and operating boundaries</div></div><div class="snote">Public operating contract</div></div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="boundary"><div class="bcell"><div class="bl">Live strategy</div><div class="bv">Price-information F2R core</div><div class="bs">Relative machine-learning forecasts are converted into cross-asset ranks and a Top-4 monthly target.</div></div><div class="bcell"><div class="bl">Official authority</div><div class="bv">Monthly actionable target</div><div class="bs">Execution follows the first common trading-day close after month-end.</div></div><div class="bcell"><div class="bl">Preview authority</div><div class="bv">Provisional only</div><div class="bs">Preview may change before month-end and has no execution or performance authority.</div></div><div class="bcell"><div class="bl">Historical performance</div><div class="bv">Research backtest</div><div class="bs">{perf["coverage"]}. It is not relabeled as forward-live performance.</div></div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="public-note">The research record compares alternative information sets as evidence about information value. Those comparisons do not redefine the live F2R strategy.</div>', unsafe_allow_html=True)
    spec = pd.DataFrame([["Universe", ", ".join(system["universe"])], ["Decision cycle", system["decision_cycle"]], ["Portfolio rule", system["portfolio_rule"]], ["Execution", system["execution_contract"]], ["Research evidence", evidence["historical_performance_label"]], ["Forward-live record", evidence["forward_live_label"]]], columns=["Field", "Public specification"])
    st.markdown('<div class="section-head"><div><div class="sk">Operating contract</div><div class="stitle">Operating specification</div></div></div>', unsafe_allow_html=True)
    render_table(spec)
    st.markdown('<div class="note">This interface is generated from an approved public snapshot and is intentionally limited to the current decision state, certified historical target history, and research evidence needed to interpret F2R.</div>', unsafe_allow_html=True)

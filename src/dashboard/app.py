
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

STATE = Path(__file__).resolve().parent / "public_data" / "f2r_public_state.json"

def pct(x, digits=1):
    return "—" if x is None else f"{100*float(x):.{digits}f}%"

def num(x, digits=2):
    return "—" if x is None else f"{float(x):.{digits}f}"

def load_state():
    if not STATE.is_file():
        st.error("No approved F2R public state is available.")
        st.stop()
    d=json.loads(STATE.read_text(encoding="utf-8"))
    if d.get("schema_version")!="2.0":
        st.error("Unsupported F2R public-state version.")
        st.stop()
    return d

def dark_chart(chart,height):
    return (chart.properties(height=height)
        .configure(background="#091018")
        .configure_view(strokeOpacity=0)
        .configure_axis(gridColor="#21303a",domainColor="#21303a",tickColor="#21303a",
                        labelColor="#82909c",titleColor="#82909c",labelFontSize=11,titleFontSize=11)
        .configure_legend(labelColor="#9aa7b2",titleColor="#9aa7b2",labelFontSize=11,orient="top"))

def table(df):
    html=df.to_html(index=False,border=0,classes="f2r-table",escape=True)
    st.markdown(f'<div class="f2r-table-wrap">{html}</div>',unsafe_allow_html=True)

def holding_grid(holdings,preview=False):
    cols=st.columns(4)
    for col,h in zip(cols,holdings):
        with col:
            role="preview" if preview else "official"
            st.markdown(
                f'<div class="holding {role}"><div class="rank">RANK {int(h["rank"])}</div>'
                f'<div class="asset">{h["asset"]}</div><div class="weight">{pct(h["target_weight"],0)} target</div></div>',
                unsafe_allow_html=True)

d=load_state()
system=d["system"]; live=d["live_state"]; perf=d["completed_performance"]; hist=d["historical_targets"]
off=live["official"]; pre=live["preview"]; trans=live["transition"]; mtd=live["current_mtd"]

st.set_page_config(page_title="F2R · Forecast-to-Rank Allocation",page_icon="📈",layout="wide",initial_sidebar_state="collapsed")
st.markdown(r'''
<style>
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
.stApp{background:#091018;color:#eef3f6}.block-container{max-width:1500px;padding-top:1rem;padding-bottom:3.5rem}
html,body,[class*="css"]{font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}h1,h2,h3{letter-spacing:-.035em}
.shell{display:flex;align-items:center;justify-content:space-between;padding:.35rem 0 1rem;border-bottom:1px solid #1d2933}.brand{display:flex;align-items:center;gap:.8rem}.mark{width:42px;height:42px;border-radius:11px;background:#eef3f6;color:#091018;display:flex;align-items:center;justify-content:center;font-size:.82rem;font-weight:900}.name{font-size:1.08rem;font-weight:800}.desc{font-size:.69rem;letter-spacing:.09em;color:#71808d;text-transform:uppercase;margin-top:.1rem}.mode{border:1px solid #315f3e;background:#102319;color:#9fe3b1;border-radius:999px;padding:.43rem .72rem;font-size:.68rem;font-weight:800;letter-spacing:.09em}.refresh{font-size:.58rem;color:#667681;margin-top:.32rem}
.hero{padding:1.15rem 0 .55rem}.eyebrow,.sk{font-size:.63rem;letter-spacing:.14em;color:#71818e;text-transform:uppercase;font-weight:800}.hero-title{font-size:clamp(2.1rem,3.6vw,3.75rem);font-weight:790;letter-spacing:-.052em;line-height:1.02;margin-top:.34rem}.hero-copy{font-size:.97rem;line-height:1.63;color:#98a5b0;max-width:980px;margin-top:.7rem}
.health,.metrics,.boundary{display:grid;gap:.65rem}.health{grid-template-columns:repeat(5,minmax(0,1fr));margin:.85rem 0 1.15rem}.metrics{grid-template-columns:repeat(6,minmax(0,1fr));margin:.8rem 0 1rem}.boundary{grid-template-columns:repeat(4,minmax(0,1fr));margin:.8rem 0}.cell,.metric,.bcell{background:#0f1821;border:1px solid #22313d;border-radius:10px;padding:.85rem .92rem}.hl,.ml,.bl{font-size:.58rem;letter-spacing:.1em;color:#6d7b87;text-transform:uppercase;font-weight:800}.hv,.bv{font-size:.98rem;color:#eef3f6;font-weight:750;margin-top:.28rem}.hs,.ms,.bs{font-size:.64rem;color:#697784;margin-top:.2rem;line-height:1.45}.mv{font-size:1.35rem;color:#eef3f6;font-weight:800;margin-top:.35rem}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:2rem 0 .8rem}.stitle{font-size:1.52rem;font-weight:790;letter-spacing:-.035em}.snote{font-size:.68rem;color:#6d7d89}.decision{background:#0f1821;border:1px solid #22313d;border-radius:12px;padding:1rem}.decision.official{border-top:3px solid #43b4d9}.decision.preview{border-top:3px solid #d0a03a}.decision-head{display:flex;justify-content:space-between;align-items:center;margin:.35rem 0 .8rem}.decision-title{font-size:1.13rem;font-weight:800}.decision-date{font-size:.66rem;color:#71818d}.holding{background:#09131b;border:1px solid #20303b;border-radius:9px;padding:.78rem}.holding.official{border-top:2px solid #43b4d9}.holding.preview{border-top:2px solid #d0a03a}.rank{font-size:.54rem;color:#687985;letter-spacing:.1em;font-weight:800}.asset{font-size:1.25rem;font-weight:850;margin:.42rem 0}.weight{font-size:.63rem;color:#70818e}.authority{font-size:.66rem;color:#758692;margin-top:.72rem}.transition{display:grid;grid-template-columns:1.5fr 1fr 1fr;gap:.65rem;margin-top:.75rem}.enter{border-color:#285d40}.leave{border-color:#6b3f39}
.arch{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.65rem}.step{background:#0e1720;border:1px solid #22313d;border-radius:10px;padding:1rem}.step-n{font-size:.55rem;color:#71818d;letter-spacing:.11em;font-weight:800}.step-t{font-size:.9rem;font-weight:800;margin:.45rem 0}.step-d{font-size:.66rem;color:#73838f;line-height:1.5}
.f2r-table-wrap{overflow:auto;border:1px solid #22313d;border-radius:10px;background:#0e1720;margin-top:.55rem;max-height:560px}table.f2r-table{width:100%;border-collapse:collapse;font-size:.74rem;color:#dfe6ea}table.f2r-table th{position:sticky;top:0;background:#111c25;color:#83929d;font-size:.58rem;letter-spacing:.075em;text-transform:uppercase;padding:.7rem;border-bottom:1px solid #22313d;text-align:center;white-space:nowrap}table.f2r-table td{padding:.65rem .7rem;border-bottom:1px solid #1b2933;text-align:center;white-space:nowrap}
.note{border:1px solid #22313d;background:#0d1720;border-radius:10px;padding:.9rem;color:#82919c;font-size:.71rem;line-height:1.55}.public-note{border-left:3px solid #376e89;background:#0b1821;border-radius:7px;padding:.9rem 1rem;color:#84949f;font-size:.72rem;line-height:1.55}
[data-baseweb="tab-list"]{gap:1.35rem;border-bottom:1px solid #172630}button[data-baseweb="tab"]{padding:.75rem 0;color:#677783}button[data-baseweb="tab"][aria-selected="true"]{color:#f15b59;border-bottom:2px solid #f15b59}
@media(max-width:1050px){.block-container{padding-left:1rem;padding-right:1rem}.health,.metrics,.boundary{grid-template-columns:repeat(2,1fr)}.arch,.transition{grid-template-columns:1fr 1fr}}
</style>
''',unsafe_allow_html=True)

pre_period=pre["signal_period"] if pre.get("available") else "Unavailable"
pre_cut=pre.get("market_cutoff_date") or "—"
st.markdown(f'<div class="shell"><div class="brand"><div class="mark">F2R</div><div><div class="name">Forecast-to-Rank Allocation</div><div class="desc">Portfolio Strategy System</div></div></div><div><div class="mode">CURRENT MODEL</div><div class="refresh">State issued {d["issued_at_display"]}</div></div></div>',unsafe_allow_html=True)
st.markdown(f'<div class="hero"><div class="eyebrow">Model portfolio</div><div class="hero-title">Forecast-ranked cross-asset allocation.</div><div class="hero-copy">{system["subtitle"]}. Conventional machine learning and pretrained time-series intelligence meet at a common rank-consensus layer before the portfolio decision.</div></div>',unsafe_allow_html=True)

st.markdown(
    f'<div class="health"><div class="cell"><div class="hl">Current signal</div><div class="hv">{off["signal_period"]}</div><div class="hs">Current model portfolio</div></div>'
    f'<div class="cell"><div class="hl">Current MTD</div><div class="hv">{pct(mtd["mtd_return"])}</div><div class="hs">through {mtd["as_of_date"]}</div></div>'
    f'<div class="cell"><div class="hl">Preview month</div><div class="hv">{pre_period}</div><div class="hs">Intramonth estimate</div></div>'
    f'<div class="cell"><div class="hl">Market data through</div><div class="hv">{pre_cut}</div><div class="hs">Latest admissible common close</div></div>'
    f'<div class="cell"><div class="hl">Preview change</div><div class="hv">{trans["change_count"]} swap{"s" if trans["change_count"]!=1 else ""}</div><div class="hs">{trans["summary"]}</div></div></div>',
    unsafe_allow_html=True)

tabs=st.tabs(["Current Portfolio","Performance","Portfolio History","System"])

with tabs[0]:
    st.markdown('<div class="section-head"><div><div class="sk">Current state</div><div class="stitle">Current model portfolio and intramonth preview</div></div><div class="snote">Blue = current · amber = preview</div></div>',unsafe_allow_html=True)
    left,right=st.columns(2)
    with left:
        st.markdown(f'<div class="decision official"><div class="decision-head"><div class="decision-title">Current Model Portfolio</div><div class="decision-date">{off["signal_period"]}</div></div>',unsafe_allow_html=True)
        holding_grid(off["holdings"],False)
        st.markdown(f'<div class="authority">{off["state_note"]}</div></div>',unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="decision preview"><div class="decision-head"><div class="decision-title">Intramonth Preview</div><div class="decision-date">{pre_period}</div></div>',unsafe_allow_html=True)
        if pre.get("available"):
            holding_grid(pre["holdings"],True)
            st.markdown(f'<div class="authority">{pre["state_note"]}</div></div>',unsafe_allow_html=True)
        else:
            st.markdown('<div class="note">Preview unavailable.</div></div>',unsafe_allow_html=True)
    if pre.get("available"):
        st.markdown(f'<div class="transition"><div class="cell"><div class="hl">Retained</div><div class="hv">{", ".join(trans["retained"]) or "—"}</div></div><div class="cell enter"><div class="hl">Entering</div><div class="hv">{", ".join(trans["entering"]) or "—"}</div></div><div class="cell leave"><div class="hl">Leaving</div><div class="hv">{", ".join(trans["leaving"]) or "—"}</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div><div class="sk">Architecture</div><div class="stitle">From market information to portfolio decision</div></div></div>',unsafe_allow_html=True)
    st.markdown('''<div class="arch">
    <div class="step"><div class="step-n">01</div><div class="step-t">Market information</div><div class="step-d">Point-in-time own-price history under the common market clock.</div></div>
    <div class="step"><div class="step-n">02</div><div class="step-t">Heterogeneous forecast engines</div><div class="step-d">Conventional ML and pretrained time-series intelligence.</div></div>
    <div class="step"><div class="step-n">03</div><div class="step-t">Rank consensus</div><div class="step-d">Translate heterogeneous forecasts into one cross-asset decision space.</div></div>
    <div class="step"><div class="step-n">04</div><div class="step-t">Portfolio decision</div><div class="step-d">Select the highest-ranked opportunities under the monthly Top-4 rule.</div></div>
    <div class="step"><div class="step-n">05</div><div class="step-t">Governed performance</div><div class="step-d">Use one current-model history for MTD, YTD, risk, and cumulative performance.</div></div>
    </div>''',unsafe_allow_html=True)

with tabs[1]:
    m=perf["metrics"]
    st.markdown(f'<div class="section-head"><div><div class="sk">Current model history</div><div class="stitle">Performance & risk</div></div><div class="snote">through {perf["as_of_date"]}</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="metrics"><div class="metric"><div class="ml">Growth of $1</div><div class="mv">{float(m["terminal_wealth"]):.2f}×</div><div class="ms">Current model history</div></div><div class="metric"><div class="ml">CAGR</div><div class="mv">{pct(m["cagr"])}</div><div class="ms">{perf["coverage"]}</div></div><div class="metric"><div class="ml">Ann. volatility</div><div class="mv">{pct(m["ann_vol"])}</div><div class="ms">Daily · 252D</div></div><div class="metric"><div class="ml">Sharpe</div><div class="mv">{num(m["sharpe_rf0"])}</div><div class="ms">RF = 0</div></div><div class="metric"><div class="ml">Max drawdown</div><div class="mv">{pct(m["max_drawdown"])}</div><div class="ms">Current model history</div></div><div class="metric"><div class="ml">Calmar</div><div class="mv">{num(m["calmar"])}</div><div class="ms">CAGR / |MDD|</div></div></div>',unsafe_allow_html=True)
    growth=pd.DataFrame(perf["growth_series"]); growth["dt"]=pd.to_datetime(growth["month"]+"-01")
    gc=alt.Chart(growth).mark_line(strokeWidth=2).encode(x=alt.X("dt:T",title=None),y=alt.Y("growth:Q",title="Growth of $1"),tooltip=[alt.Tooltip("month:N"),alt.Tooltip("growth:Q",format=".2f")])
    st.altair_chart(dark_chart(gc,330),use_container_width=True)
    dd=pd.DataFrame(perf["drawdown_series"]); dd["dt"]=pd.to_datetime(dd["date"])
    dc=alt.Chart(dd).mark_area(opacity=.72).encode(x=alt.X("dt:T",title=None),y=alt.Y("drawdown:Q",title="Drawdown",axis=alt.Axis(format="%")),tooltip=[alt.Tooltip("date:N"),alt.Tooltip("drawdown:Q",format=".1%")])
    st.altair_chart(dark_chart(dc,220),use_container_width=True)
    annual=pd.DataFrame(perf["annual_returns"]); annual["Return"]=annual["return"].map(lambda x:pct(x))
    table(annual[["period","Return"]].rename(columns={"period":"Period"}))
    st.markdown(f'<div class="public-note">{perf["performance_note"]}</div>',unsafe_allow_html=True)

with tabs[2]:
    hm=hist["metrics"]
    st.markdown('<div class="section-head"><div><div class="sk">Current-model allocation history</div><div class="stitle">Portfolio target history</div></div><div class="snote">Preview excluded</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="metrics"><div class="metric"><div class="ml">Coverage</div><div class="mv">{hm["months"]} mo</div><div class="ms">{hist["coverage"]}</div></div><div class="metric"><div class="ml">Target records</div><div class="mv">{hm["target_rows"]}</div><div class="ms">Four per signal month</div></div><div class="metric"><div class="ml">Avg changes</div><div class="mv">{hm["avg_changes"]:.2f}</div><div class="ms">Entering assets</div></div><div class="metric"><div class="ml">No-change months</div><div class="mv">{hm["no_change_months"]}</div><div class="ms">Same Top-4 set</div></div><div class="metric"><div class="ml">Most selected</div><div class="mv">{hm["most_selected_asset"]}</div><div class="ms">{hm["most_selected_months"]} months</div></div><div class="metric"><div class="ml">Target weight</div><div class="mv">25%</div><div class="ms">Equal weight</div></div></div>',unsafe_allow_html=True)
    recent=pd.DataFrame(hist["recent_12"]).rename(columns={"month":"Signal Month","rank1":"Rank 1","rank2":"Rank 2","rank3":"Rank 3","rank4":"Rank 4","changes":"Changes"})
    table(recent[["Signal Month","Rank 1","Rank 2","Rank 3","Rank 4","Changes"]])
    with st.expander("Full current-model target history"):
        full=pd.DataFrame(hist["full_history"]).sort_values("month",ascending=False).rename(columns={"month":"Signal Month","rank1":"Rank 1","rank2":"Rank 2","rank3":"Rank 3","rank4":"Rank 4","changes":"Changes"})
        table(full[["Signal Month","Rank 1","Rank 2","Rank 3","Rank 4","Changes"]])
    st.markdown(f'<div class="public-note">{hist["history_note"]}</div>',unsafe_allow_html=True)

with tabs[3]:
    st.markdown('<div class="section-head"><div><div class="sk">System identity</div><div class="stitle">Architecture and operating boundary</div></div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="boundary"><div class="bcell"><div class="bl">Information</div><div class="bv">Own-price history</div><div class="bs">Point-in-time cross-asset market information.</div></div><div class="bcell"><div class="bl">Forecasting</div><div class="bv">Heterogeneous engines</div><div class="bs">Conventional machine learning plus pretrained time-series intelligence.</div></div><div class="bcell"><div class="bl">Portfolio</div><div class="bv">{system["portfolio_rule"]}</div><div class="bs">{system["decision_cycle"]} decision cycle.</div></div><div class="bcell"><div class="bl">Accounting</div><div class="bv">Model-portfolio validity</div><div class="bs">{system["execution_note"]}</div></div></div>',unsafe_allow_html=True)
    spec=pd.DataFrame([
        ["Universe",", ".join(system["universe"])],
        ["Decision cycle",system["decision_cycle"]],
        ["Portfolio rule",system["portfolio_rule"]],
        ["Architecture",system["architecture_note"]],
        ["Performance identity","Current canonical model portfolio"],
        ["Historical disclosure",d["evidence_boundary"]["public_disclosure"]],
    ],columns=["Field","Public specification"])
    table(spec)
    st.markdown('<div class="note">Exact model-integration weights, runtime paths, low-level tie tolerances, prior-version chronology, and unpromoted research branches remain internal.</div>',unsafe_allow_html=True)

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Load Balancing Dashboard",
    page_icon="⚖️",
    layout="wide"
)

st.title("Load Balancing — Algorithm Benchmark")
st.caption("WRK2 Benchmarking · 1 Load Balancer · 5 Servers · 1 Client")
st.divider()

@st.cache_data
def generate_data():
    np.random.seed(7)

    ALGORITHMS    = ["Round Robin", "Weighted Round Robin", "Least Response Time", "Chained Failover"]
    CONCURRENCIES = [10, 50, 100, 200, 500, 1000]
    SERVER_COUNTS = [1, 2, 3, 4, 5]

    PROFILE = {
        "Round Robin":          {"tput": 4200, "lat": 12,  "err": 0.008, "scale": 0.88},
        "Weighted Round Robin": {"tput": 4800, "lat": 10,  "err": 0.005, "scale": 0.92},
        "Least Response Time":  {"tput": 5400, "lat": 7.5, "err": 0.003, "scale": 0.95},
        "Chained Failover":     {"tput": 3600, "lat": 18,  "err": 0.002, "scale": 0.80},
    }

    rows = []
    for algo in ALGORITHMS:
        p = PROFILE[algo]
        for conc in CONCURRENCIES:
            lf      = conc / 100
            tput    = p["tput"]  * (1 - 0.08 * np.log1p(lf)) * np.random.normal(1, 0.02)
            lat_p50 = p["lat"]   * (1 + 0.35 * lf)           * np.random.normal(1, 0.03)
            lat_p95 = lat_p50 * np.random.uniform(2.2, 2.8)
            lat_p99 = lat_p50 * np.random.uniform(3.8, 5.2)
            errors  = int(conc * p["err"] * (1 + 2 * lf)     * np.random.normal(1, 0.1))
            rows.append({
                "Algorithm":      algo,
                "Connections":    conc,
                "Throughput":     round(tput, 1),
                "Latency p50":    round(lat_p50, 2),
                "Latency p95":    round(lat_p95, 2),
                "Latency p99":    round(lat_p99, 2),
                "Socket Errors":  max(0, errors),
            })
    bench_df = pd.DataFrame(rows)

    scale_rows = []
    for algo in ALGORITHMS:
        p    = PROFILE[algo]
        base = p["tput"] * 0.6
        for n in SERVER_COUNTS:
            tput = base * (1 - p["scale"] ** n) / (1 - p["scale"]) * np.random.normal(1, 0.015)
            scale_rows.append({"Algorithm": algo, "Servers": n, "Throughput": round(tput, 1)})
    scale_df = pd.DataFrame(scale_rows)

    return bench_df, scale_df, ALGORITHMS, CONCURRENCIES


bench_df, scale_df, ALGORITHMS, CONCURRENCIES = generate_data()

COLORS = {
    "Round Robin":          "#3266ad",
    "Weighted Round Robin": "#1D9E75",
    "Least Response Time":  "#BA7517",
    "Chained Failover":     "#7F77DD",
}

st.sidebar.header("Filters")

selected_algos = st.sidebar.multiselect(
    "Algorithms",
    options=ALGORITHMS,
    default=ALGORITHMS,
)

conc_range = st.sidebar.select_slider(
    "Concurrency range (connections)",
    options=CONCURRENCIES,
    value=(CONCURRENCIES[0], CONCURRENCIES[-1]),
)

lat_col = st.sidebar.radio(
    "Latency percentile",
    options=["Latency p50", "Latency p95", "Latency p99"],
    index=0,
)

st.sidebar.divider()
st.sidebar.markdown("**Project:** Design of Internet Services")
st.sidebar.markdown("**Algorithms tested:** Round Robin, Weighted Round Robin, Least Response Time, Chained Failover")

dff = bench_df[
    (bench_df["Algorithm"].isin(selected_algos)) &
    (bench_df["Connections"] >= conc_range[0]) &
    (bench_df["Connections"] <= conc_range[1])
]

if dff.empty:
    st.warning("No data for the selected filters.")
    st.stop()

mean_tput = dff.groupby("Algorithm")["Throughput"].mean()
mean_lat  = dff.groupby("Algorithm")["Latency p50"].mean()
total_err = dff.groupby("Algorithm")["Socket Errors"].sum()

s1 = scale_df[scale_df["Servers"] == 1].set_index("Algorithm")["Throughput"]
s5 = scale_df[scale_df["Servers"] == 5].set_index("Algorithm")["Throughput"]
scale_gain = ((s5 - s1) / s1 * 100).reindex(selected_algos).dropna()

col1, col2, col3, col4 = st.columns(4)

with col1:
    best = mean_tput.idxmax()
    st.metric("Best Throughput", f"{mean_tput[best]:,.0f} r/s", best)

with col2:
    best = mean_lat.idxmin()
    st.metric("Lowest Latency (p50)", f"{mean_lat[best]:.1f} ms", best)

with col3:
    best = total_err.idxmin()
    st.metric("Fewest Socket Errors", f"{int(total_err[best])}", best)

with col4:
    if not scale_gain.empty:
        best = scale_gain.idxmax()
        st.metric("Best Scalability (1→5 servers)", f"+{scale_gain[best]:.0f}%", best)

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Throughput vs Concurrency")
    fig = px.line(
        dff, x="Connections", y="Throughput", color="Algorithm",
        color_discrete_map=COLORS, markers=True,
        labels={"Connections": "Concurrent connections", "Throughput": "Requests / sec"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader(f"Latency vs Concurrency ({lat_col})")
    fig = px.line(
        dff, x="Connections", y=lat_col, color="Algorithm",
        color_discrete_map=COLORS, markers=True,
        labels={"Connections": "Concurrent connections", lat_col: "Latency (ms)"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)


col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Socket Errors vs Concurrency")
    fig = px.bar(
        dff, x="Connections", y="Socket Errors", color="Algorithm",
        color_discrete_map=COLORS, barmode="group",
        labels={"Connections": "Concurrent connections"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.subheader("Scalability — Throughput vs Server Count")
    scale_filtered = scale_df[scale_df["Algorithm"].isin(selected_algos)]
    fig = px.line(
        scale_filtered, x="Servers", y="Throughput", color="Algorithm",
        color_discrete_map=COLORS, markers=True,
        labels={"Servers": "Number of servers", "Throughput": "Throughput (req/s)"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Algorithm Comparison at Peak Load (1000 connections)")
peak = bench_df[
    (bench_df["Connections"] == 1000) &
    (bench_df["Algorithm"].isin(selected_algos))
]
fig = px.bar(
    peak.melt(id_vars="Algorithm", value_vars=["Throughput", "Latency p50", "Socket Errors"]),
    x="variable", y="value", color="Algorithm",
    color_discrete_map=COLORS, barmode="group",
    labels={"variable": "Metric", "value": "Value"},
)
fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Raw Benchmark Results")
st.caption(f"{len(dff)} records · Concurrency {conc_range[0]}–{conc_range[1]} connections")
st.dataframe(
    dff.sort_values(["Connections", "Throughput"], ascending=[True, False]),
    use_container_width=True,
    hide_index=True,
)

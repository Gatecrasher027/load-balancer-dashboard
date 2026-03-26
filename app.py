import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Load Balancing Dashboard", layout="wide")

st.title("⚙️ Load Balancing Algorithms Dashboard")

# Sidebar inputs
st.sidebar.header("Simulation Controls")
num_requests = st.sidebar.slider("Number of Requests", 100, 10000, 1000)
num_servers = st.sidebar.slider("Number of Servers", 1, 10, 5)

algorithms = ["Round Robin", "Weighted RR", "Least Response Time", "Chained Failover"]

# Simulated metrics
np.random.seed(42)
data = []

for algo in algorithms:
    latency = np.random.uniform(50, 200) / num_servers
    throughput = np.random.uniform(200, 500) * num_servers
    error_rate = np.random.uniform(0, 5)

    data.append([algo, latency, throughput, error_rate])

df = pd.DataFrame(data, columns=["Algorithm", "Latency (ms)", "Throughput", "Error Rate (%)"])

# Layout
col1, col2 = st.columns(2)

# Bar Chart: Throughput
with col1:
    st.subheader("📊 Throughput Comparison")
    st.bar_chart(df.set_index("Algorithm")["Throughput"])

# Bar Chart: Latency
with col2:
    st.subheader("📊 Latency Comparison")
    st.bar_chart(df.set_index("Algorithm")["Latency (ms)"])

# Line Chart: Requests vs Latency
st.subheader("📈 Latency vs Requests")

requests = np.linspace(100, num_requests, 50)
latency_curve = requests / (num_servers * 50)

fig, ax = plt.subplots()
ax.plot(requests, latency_curve)
ax.set_xlabel("Requests")
ax.set_ylabel("Latency")
ax.set_title("Latency Growth")

st.pyplot(fig)

# Table
st.subheader("📋 Detailed Metrics")
st.dataframe(df)

# Insight box
best_algo = df.loc[df["Latency (ms)"].idxmin()]["Algorithm"]

st.success(f"🏆 Best Algorithm (Lowest Latency): {best_algo}")

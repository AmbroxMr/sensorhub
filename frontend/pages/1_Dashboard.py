import time

import pandas as pd
import streamlit as st

from client import get_readings, get_stats

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")

# ── Controles ───────────────────────────────────────────────────────────────────

col_toggle, col_btn = st.columns([3, 1])
with col_toggle:
    auto_refresh = st.toggle("Auto-refresco cada 5 segundos", value=False)
with col_btn:
    if st.button("🔄 Refrescar", use_container_width=True):
        st.rerun()

# ── Métricas por dispositivo ────────────────────────────────────────────────────

st.subheader("Estado actual")

try:
    stats = get_stats()
except Exception as e:
    st.error(f"Error al cargar estadísticas: {e}")
    st.stop()

if not stats:
    st.info("Sin datos. Lanza el simulador primero.")
    st.stop()

cols = st.columns(len(stats))
for col, device in zip(cols, stats):
    with col:
        with st.container(border=True):
            st.markdown(f"**{device['device_id']}**")
            st.metric("Temperatura media", f"{device['avg_temperature']:.1f} °C")
            st.metric("Humedad media", f"{device['avg_humidity']:.1f} %")
            st.metric("CO₂ medio", f"{device['avg_co2']:.0f} ppm")
            st.metric("CO₂ máximo", f"{device['max_co2']:.0f} ppm")
            st.caption(f"{int(device['count'])} lecturas registradas")

# ── Gráficas temporales ─────────────────────────────────────────────────────────

st.divider()
st.subheader("Evolución temporal")

try:
    raw = get_readings(limit=500)
except Exception as e:
    st.error(f"Error al cargar lecturas: {e}")
    st.stop()

if not raw:
    st.info("Sin lecturas disponibles.")
else:
    df = pd.DataFrame(raw)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    devices = df["device_id"].unique().tolist()
    selected = st.multiselect("Filtrar dispositivos", devices, default=devices)
    df = df[df["device_id"].isin(selected)]

    tab_temp, tab_hum, tab_co2 = st.tabs(["🌡️ Temperatura (°C)", "💧 Humedad (%)", "🌫️ CO₂ (ppm)"])

    with tab_temp:
        pivot = df.pivot_table(index="timestamp", columns="device_id", values="temperature")
        st.line_chart(pivot, y_label="°C")

    with tab_hum:
        pivot = df.pivot_table(index="timestamp", columns="device_id", values="humidity")
        st.line_chart(pivot, y_label="%")

    with tab_co2:
        pivot = df.pivot_table(index="timestamp", columns="device_id", values="co2")
        st.line_chart(pivot, y_label="ppm")

# ── Auto-refresco ───────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(5)
    st.rerun()

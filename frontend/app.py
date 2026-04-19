import streamlit as st

from client import get_health, get_stats

st.set_page_config(
    page_title="SensorHub",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ SensorHub")
st.caption("Panel de monitoreo ambiental IoT")

# ── Estado de la API ────────────────────────────────────────────────────────────

st.subheader("Estado del sistema")

try:
    health = get_health()
    st.success("API conectada y operativa")
except Exception:
    st.error("No se puede conectar con la API. Comprueba que el servidor está en marcha.")
    st.stop()

# ── Resumen de dispositivos ─────────────────────────────────────────────────────

st.divider()
st.subheader("Dispositivos activos")

try:
    stats = get_stats()
except Exception as e:
    st.warning(f"No se pudieron cargar las estadísticas: {e}")
    stats = []

if not stats:
    st.info("Aún no hay lecturas en la base de datos. Lanza el simulador para generar datos.")
    st.code("uv run python simulator.py", language="bash")
else:
    cols = st.columns(len(stats))
    for col, device in zip(cols, stats):
        with col:
            st.metric(label="Dispositivo", value=device["device_id"])
            st.metric(label="Lecturas", value=int(device["count"]))
            st.metric(label="Temperatura media", value=f"{device['avg_temperature']:.1f} °C")
            st.metric(label="Humedad media", value=f"{device['avg_humidity']:.1f} %")
            st.metric(label="CO₂ medio", value=f"{device['avg_co2']:.0f} ppm")

# ── Navegación ─────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
    """
    **Páginas disponibles en el menú lateral:**

    | Página | Descripción |
    |--------|-------------|
    | 📊 Dashboard | Gráficas de evolución temporal por dispositivo |
    | 🔍 Explorador | Tabla de lecturas con filtros y descarga CSV |
    | 📋 Reportes | Generación y descarga de reportes horarios |
    """
)

import pandas as pd
import streamlit as st

from client import export_csv, get_readings, get_stats

st.set_page_config(page_title="Explorador", page_icon="🔍", layout="wide")

st.title("🔍 Explorador de datos")

# ── Filtros ─────────────────────────────────────────────────────────────────────

st.subheader("Filtros")
col_device, col_limit = st.columns(2)

with col_device:
    try:
        stats = get_stats()
        device_options = ["Todos"] + [s["device_id"] for s in stats]
    except Exception:
        device_options = ["Todos"]
    selected_device = st.selectbox("Dispositivo", device_options)

with col_limit:
    limit = st.slider("Máximo de registros", min_value=10, max_value=500, value=100, step=10)

device_id = None if selected_device == "Todos" else selected_device

# ── Tabla de lecturas ───────────────────────────────────────────────────────────

try:
    raw = get_readings(device_id=device_id, limit=limit)
except Exception as e:
    st.error(f"Error al cargar lecturas: {e}")
    st.stop()

if not raw:
    st.info("No hay lecturas para los filtros seleccionados.")
    st.stop()

df = pd.DataFrame(raw)
df["timestamp"] = pd.to_datetime(df["timestamp"], format='ISO8601')
df = df.sort_values("timestamp", ascending=False)

display_cols = ["timestamp", "device_id", "location", "temperature", "humidity", "co2"]
display_cols = [c for c in display_cols if c in df.columns]

st.subheader(f"Lecturas — {len(df)} registros")
st.dataframe(
    df[display_cols],
    use_container_width=True,
    column_config={
        "timestamp": st.column_config.DatetimeColumn(
            "Timestamp", format="YYYY-MM-DD HH:mm:ss"
        ),
        "device_id": st.column_config.TextColumn("Dispositivo"),
        "location": st.column_config.TextColumn("Ubicación"),
        "temperature": st.column_config.NumberColumn("Temperatura (°C)", format="%.1f °C"),
        "humidity": st.column_config.NumberColumn("Humedad (%)", format="%.1f %%"),
        "co2": st.column_config.NumberColumn("CO₂ (ppm)", format="%.0f ppm"),
    },
)

# ── Descarga ────────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Descargar datos")

col_filtered, col_full = st.columns(2)

with col_filtered:
    csv_filtrado = df[display_cols].to_csv(index=False).encode()
    st.download_button(
        label="⬇️ Descargar selección actual (CSV)",
        data=csv_filtrado,
        file_name="lecturas_filtradas.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_full:
    try:
        csv_completo = export_csv()
        st.download_button(
            label="⬇️ Descargar todas las lecturas (CSV)",
            data=csv_completo,
            file_name="lecturas_completas.csv",
            mime="text/csv",
            use_container_width=True,
        )
    except Exception as e:
        st.warning(f"No se pudo obtener el CSV completo: {e}")

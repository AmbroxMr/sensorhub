from datetime import datetime

import streamlit as st

from client import generate_report, get_report, list_reports

st.set_page_config(page_title="Reportes", page_icon="📋", layout="wide")

st.title("📋 Reportes horarios")
st.caption("Los reportes se generan agrupando lecturas por dispositivo y ubicación en una ventana de una hora.")

# ── Generar reporte ─────────────────────────────────────────────────────────────

st.subheader("Generar nuevo reporte")

with st.form("form_generar"):
    usar_hora_custom = st.checkbox("Especificar una hora distinta a la actual")

    hour_str = None
    if usar_hora_custom:
        col_fecha, col_hora = st.columns(2)
        with col_fecha:
            fecha = st.date_input("Fecha", value=datetime.now().date())
        with col_hora:
            hora = st.selectbox("Hora", [f"{h:02d}:00" for h in range(24)], index=datetime.now().hour)
        hour_str = f"{fecha}T{hora}:00"
    else:
        ahora = datetime.now()
        st.caption(f"Se usará la hora actual: **{ahora.strftime('%Y-%m-%d %H:00')}**")

    submitted = st.form_submit_button("🚀 Generar reporte", type="primary", use_container_width=True)

if submitted:
    with st.spinner("Generando reporte..."):
        try:
            result = generate_report(hour=hour_str)
            st.success(f"Reporte generado correctamente: `{result['object_key']}`")
        except Exception as e:
            st.error(f"Error al generar el reporte: {e}")

# ── Listar reportes ─────────────────────────────────────────────────────────────

st.divider()

col_titulo, col_btn = st.columns([4, 1])
with col_titulo:
    st.subheader("Reportes disponibles en MinIO")
with col_btn:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

try:
    reports = list_reports()
except Exception as e:
    st.error(f"Error al listar reportes: {e}")
    st.stop()

if not reports:
    st.info("Todavía no hay reportes generados.")
else:
    for report in reports:
        with st.container(border=True):
            col_nombre, col_fecha, col_btn = st.columns([4, 3, 1])

            with col_nombre:
                st.markdown(f"**{report['name']}**")

            with col_fecha:
                if report.get("last_modified"):
                    st.caption(f"Modificado: {report['last_modified'][:19]}")
                if report.get("size"):
                    st.caption(f"Tamaño: {report['size']} bytes")

            with col_btn:
                try:
                    csv_bytes = get_report(report["name"])
                    filename = report["name"].split("/")[-1]
                    st.download_button(
                        label="⬇️ CSV",
                        data=csv_bytes,
                        file_name=filename,
                        mime="text/csv",
                        key=f"dl_{report['name']}",
                        use_container_width=True,
                    )
                except Exception:
                    st.error("Error al obtener el fichero")

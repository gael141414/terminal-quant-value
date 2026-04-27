import streamlit as st
import pandas as pd
import os
from datetime import datetime

def ejecutar_visor_smallcaps():
    st.markdown("### ⛏️ Minero de Small Caps (Joyas Ocultas)")
    
    ruta_csv = "data/small_caps_oro.csv"
    
    if os.path.exists(ruta_csv):
        try:
            # 1. Intentar leer el archivo
            df = pd.read_csv(ruta_csv)
            
            # 2. Comprobar si el archivo tiene datos reales
            if df.empty:
                st.warning("🔎 El minero ha escaneado el mercado, pero actualmente ninguna empresa cumple con tus filtros estrictos de selección.")
                st.info("Esto es normal en mercados laterales o bajistas. El robot volverá a intentarlo en la próxima ejecución.")
                return

            # --- SI HAY DATOS, MOSTRAR LA INTERFAZ ---
            fecha_mod = os.path.getmtime(ruta_csv)
            fecha_legible = datetime.fromtimestamp(fecha_mod).strftime('%d/%m/%Y %H:%M')
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🚀 Startups Filtradas", len(df))
            c2.metric("📊 Top Crecimiento", df.iloc[0]['Ticker'])
            c3.metric("📅 Actualizado el", fecha_legible)
            
            st.markdown("#### 🏆 Tabla de Ganadoras")
            st.dataframe(df, use_container_width=True, hide_index=True)
            # ... resto de tu configuración de columnas ...

        except pd.errors.EmptyDataError:
            # Este es el error que te salía. Ahora lo capturamos.
            st.warning("🛰️ **Conexión establecida, pero sin datos.**")
            st.write("El robot minero se ejecutó correctamente, pero el mercado no ofreció oportunidades que superaran los filtros de calidad hoy.")
            st.caption("Próxima revisión automática programada para el domingo.")
            
    else:
        st.error("🚨 Base de datos no encontrada.")

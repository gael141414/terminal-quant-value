import streamlit as st
import pandas as pd
import os
from datetime import datetime

def ejecutar_visor_smallcaps():
    st.markdown("### ⛏️ Minero de Small Caps (Joyas Ocultas)")
    st.markdown("Este módulo visualiza el 'oro' encontrado por el proceso automático de GitHub Actions tras filtrar cientos de empresas del S&P 600.")
    
    ruta_csv = "data/small_caps_oro.csv"
    
    if os.path.exists(ruta_csv):
        # Obtener la fecha de última modificación del archivo
        fecha_mod = os.path.getmtime(ruta_csv)
        fecha_legible = datetime.fromtimestamp(fecha_mod).strftime('%d/%m/%Y %H:%M')
        
        df = pd.read_csv(ruta_csv)
        
        # KPI Superiores
        c1, c2, c3 = st.columns(3)
        c1.metric("🚀 Startups Filtradas", len(df))
        c2.metric("📊 Top Crecimiento", df.iloc[0]['Ticker'] if not df.empty else "-")
        c3.metric("📅 Actualizado el", fecha_legible)
        
        st.markdown("---")
        
        if not df.empty:
            st.markdown("#### 🏆 Tabla de Ganadoras (Lista Élite)")
            st.caption("Filtros institucionales: Crecimiento > 15% | Margen > 40% | Deuda < 50% | Insiders > 5%")
            
            # Mostramos el dataframe con configuración de columnas mejorada
            st.dataframe(
                df,
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "Crecimiento Ventas (%)": st.column_config.ProgressColumn("Crecimiento (%)", min_value=0, max_value=100, format="%.2f%%"),
                    "Margen Bruto (%)": st.column_config.NumberColumn("Margen (%)", format="%.2f%%"),
                    "Market Cap (M$)": st.column_config.NumberColumn("Cap. Mercado (M$)", format="$%.1fM"),
                    "Deuda/Capital": st.column_config.NumberColumn("D/E Ratio", format="%.2f"),
                    "Insiders (%)": st.column_config.NumberColumn("Insiders", format="%.2f%%")
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.warning("El minero terminó su trabajo pero ninguna empresa cumplió los filtros estrictos esta vez.")
        
        st.info("💡 **Consejo Quant:** Estas empresas han pasado el filtro cuantitativo. Ahora te toca a ti validar su modelo de negocio con el Oráculo o el Análisis Fundamental.")
        
    else:
        st.error("🚨 Base de datos no encontrada.")
        st.info("🤖 **Estado del Robot:** Si acabas de activar el Workflow en GitHub, espera unos 15 minutos a que el archivo 'small_caps_oro.csv' aparezca en tu repositorio.")

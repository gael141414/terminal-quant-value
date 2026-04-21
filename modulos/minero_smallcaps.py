import streamlit as st
import pandas as pd
import os

def ejecutar_visor_smallcaps():
    st.markdown("### ⛏️ Minero de Small Caps (Joyas Ocultas)")
    st.markdown("Este módulo lee los resultados del último rastreo profundo (Batch Processing). Muestra empresas de baja capitalización que están creciendo a doble dígito, con altos márgenes, baja deuda y dueños muy involucrados.")
    
    ruta_csv = "data/small_caps_oro.csv"
    
    if os.path.exists(ruta_csv):
        df = pd.read_csv(ruta_csv)
        
        # KPI Superiores
        c1, c2, c3 = st.columns(3)
        c1.metric("🚀 Startups Filtradas", len(df))
        c2.metric("📊 Ticker con Mayor Crecimiento", df.iloc[0]['Ticker'] if not df.empty else "-")
        c3.metric("📅 Última actualización", "Datos del último minado")
        
        st.markdown("#### 🏆 Tabla de Ganadoras (Lista Élite)")
        st.caption("Filtros aplicados: Crecimiento > 15% | Margen Bruto > 40% | Deuda controlada | Insiders > 5%")
        
        # Mostramos el dataframe con formato nativo de Streamlit
        st.dataframe(
            df,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Crecimiento Ventas (%)": st.column_config.ProgressColumn("Crecimiento (%)", min_value=0, max_value=100, format="%f%%"),
                "Margen Bruto (%)": st.column_config.NumberColumn("Margen (%)", format="%f%%"),
                "Market Cap (M$)": st.column_config.NumberColumn("Cap. Mercado (M$)", format="$%f")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Información de uso
        st.info("💡 **Consejo Quant:** Coge un ticker de esta lista, ponlo en la barra lateral izquierda y pásalo por la 'Auditoría Forense' y el 'Análisis Fundamental' para confirmar si de verdad es una joya antes de invertir.")
        
    else:
        st.error("🚨 Base de datos no encontrada.")
        st.warning("Aún no has ejecutado el minero nocturno. Abre tu terminal de comandos, ejecuta `python utilidades/minero_nocturno.py` y espera a que termine. Cuando lo haga, esta pantalla se llenará de oportunidades.")

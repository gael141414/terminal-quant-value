import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components

# Importamos las herramientas de gráficos y utilidades
from charts import plot_flujo_opciones, plot_visor_trend_following
from modulos.utils import obtener_datos_directiva, obtener_transacciones_insiders

# -------------------------------------------------------------------
# 1. WIDGET NATIVO DE TRADINGVIEW
# -------------------------------------------------------------------
def renderizar_grafico_tradingview(ticker):
    codigo_html = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tv_chart_container" style="height:600px;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true, "symbol": "{ticker}", "interval": "D", "timezone": "Etc/UTC",
      "theme": "dark", "style": "1", "locale": "es", "enable_publishing": false,
      "backgroundColor": "#0b0e14", "gridColor": "#1f293d", "hide_top_toolbar": false,
      "hide_legend": false, "save_image": false, "container_id": "tv_chart_container",
      "toolbar_bg": "#131722", "studies": ["Volume@tv-basicstudies"]
      }});
      </script>
    </div>
    """
    components.html(codigo_html, height=600)

# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DEL MÓDULO
# -------------------------------------------------------------------
def ejecutar_tecnico_y_opciones(ticker_input):
    """Muestra el gráfico interactivo, visores quant y datos de derivados."""
    st.markdown(f"### 📈 Terminal de Análisis Técnico y Flujos: {ticker_input}")
    
    # 1. Gráfico General (TradingView)
    st.caption("Visor interactivo global. Utiliza las herramientas de la izquierda para trazar soportes y resistencias manuales.")
    renderizar_grafico_tradingview(ticker_input)
    
    # ==========================================================
    # 2. CAJA DE CAMBIOS: VISORES CUANTITATIVOS (NUEVO)
    # ==========================================================
    st.markdown("---")
    st.markdown("### 🤖 Motores Algorítmicos de Trading")
    st.markdown("Selecciona un visor estratégico. Cada algoritmo está diseñado para cazar un comportamiento específico del mercado mediante confluencia matemática.")
    
    visor_seleccionado = st.radio(
        "🎯 Selecciona el Motor Algorítmico:",
        [
            "🌊 Visor 1: Trend Following (EMAs + MACD + RSI)",
            "💥 Visor 2: Breakout & Volatilidad (Próximamente)",
            "🧲 Visor 3: Reversión a la Media (Próximamente)",
            "🏯 Visor 4: Ichimoku Cloud (Próximamente)"
        ],
        horizontal=True
    )
    
    # Lógica del Visor 1
    if "Visor 1" in visor_seleccionado:
        st.markdown("#### 🌊 Sistema de Seguimiento de Tendencias")
        st.caption("Filtra el ruido diario. Busca subir a olas institucionales confirmando que hay tendencia (EMAs), aceleración (MACD) y margen de subida (RSI < 70).")
        
        with st.spinner("Compilando algoritmo Trend Following..."):
            fig, df = plot_visor_trend_following(ticker_input, period="1y")
            
            if fig is not None and df is not None:
                st.plotly_chart(fig, use_container_width=True)
                
                # --- LECTOR DE SEÑALES INTELIGENTE ---
                st.markdown("##### 🤖 Veredicto Algorítmico del Visor")
                ultimo = df.iloc[-1]
                ayer = df.iloc[-2]
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.markdown("**1. Filtro de Tendencia**")
                    if ultimo['EMA_50'] > ultimo['EMA_200']:
                        st.success("🟢 **Alcista:** EMA 50 > EMA 200.")
                        tendencia_ok = True
                    else:
                        st.error("🔴 **Bajista:** EMA 50 < EMA 200.")
                        tendencia_ok = False
                
                with c2:
                    st.markdown("**2. Gatillo de Momentum**")
                    cruce_alcista = ultimo['MACD'] > ultimo['Señal'] and ayer['MACD'] <= ayer['Señal']
                    if cruce_alcista:
                        st.success("🚀 **Señal:** Cruce alcista hoy/ayer.")
                        gatillo_ok = True
                    elif ultimo['MACD'] > ultimo['Señal']:
                        st.info("🟢 MACD en fase compradora.")
                        gatillo_ok = True
                    else:
                        st.warning("🔴 MACD en fase correctora.")
                        gatillo_ok = False
                        
                with c3:
                    st.markdown("**3. Riesgo de Sobrecompra**")
                    if ultimo['RSI'] > 70:
                        st.error(f"🔴 **Peligro ({ultimo['RSI']:.0f}):** Sobrecomprada.")
                        rsi_ok = False
                    elif ultimo['RSI'] < 30:
                        st.success(f"🟢 **Oportunidad ({ultimo['RSI']:.0f}):** Sobrevendida.")
                        rsi_ok = True
                    else:
                        st.info(f"⚖️ **Neutral ({ultimo['RSI']:.0f}):** En rango sano.")
                        rsi_ok = True

                st.markdown("---")
                if tendencia_ok and gatillo_ok and rsi_ok:
                    st.success("✅ **CONFLUENCIA TOTAL: SEÑAL DE COMPRA FUERTE.** Tendencia alcista, momentum positivo y RSI sano.")
                elif tendencia_ok and gatillo_ok and not rsi_ok:
                    st.warning("⚠️ **PRECAUCIÓN: LLEGAS TARDE.** Tendencia y momentum alcistas, pero RSI en extrema sobrecompra.")
                else:
                    st.info("⏳ **SIN CONFLUENCIA:** Los indicadores se contradicen. Mantente al margen.")
            else:
                st.warning("No hay suficientes datos históricos para ejecutar este visor.")

    elif "Visor 2" in visor_seleccionado:
        st.info("🚧 Visor de Breakout (Bandas Bollinger + Keltner) en construcción...")
    elif "Visor 3" in visor_seleccionado:
        st.info("🚧 Visor de Reversión (VWAP + StochRSI) en construcción...")
    elif "Visor 4" in visor_seleccionado:
        st.info("🚧 Visor Ichimoku Cloud en construcción...")

    # ==========================================================
    # 3. MERCADO DE OPCIONES Y DERIVADOS (TU CÓDIGO ORIGINAL)
    # ==========================================================
    st.markdown("---")
    st.markdown("#### 🕵️ El Rastro del Dinero: Mercado de Derivados (Opciones)")
    st.caption("Los inversores institucionales compran opciones (Calls para apostar al alza, Puts para protegerse). Analizamos el sentimiento de Wall Street.")

    with st.spinner("Descargando la cadena de derivados de Wall Street..."):
        fig_opciones, diag_opciones = plot_flujo_opciones(ticker_input)
        
        if fig_opciones:
            st.plotly_chart(fig_opciones, use_container_width=True)
            if "CODICIA" in diag_opciones:
                st.success(diag_opciones)
            elif "MIEDO" in diag_opciones:
                st.error(diag_opciones)
            else:
                st.info(diag_opciones)
        else:
            st.warning(diag_opciones if diag_opciones else "Datos de opciones no disponibles.")

    # ==========================================================
    # 4. ANÁLISIS DE LA DIRECTIVA (TU CÓDIGO ORIGINAL)
    # ==========================================================
    st.markdown("---")
    st.markdown("#### 👔 Análisis de la Directiva y Sentimiento del Mercado")
    st.caption("Verificamos si los directivos tienen 'Skin in the Game' y sus movimientos recientes de compra/venta (Formulario 4).")
    
    insiders, inst, short = obtener_datos_directiva(ticker_input)
    col_dir1, col_dir2, col_dir3 = st.columns(3)
    
    if insiders is not None:
        estado_insiders = "Excelente" if insiders > 5 else "Bajo"
        col_dir1.metric("Propiedad Insiders", f"{insiders:.2f}%", estado_insiders, delta_color="normal" if insiders > 5 else "off")
        estado_inst = "Alta convicción" if inst > 60 else "Poco respaldo"
        col_dir2.metric("Propiedad Institucional", f"{inst:.2f}%", estado_inst, delta_color="off")
        estado_short = "Ataque Bajista" if short > 5 else "Sano"
        color_short = "inverse" if short > 5 else "normal"
        col_dir3.metric("Short Ratio", f"{short:.2f}", estado_short, delta_color=color_short)
    else:
        st.info("Datos de accionariado no disponibles.")

    df_insiders = obtener_transacciones_insiders(ticker_input)
    if df_insiders is not None and not df_insiders.empty:
        def color_transaction(val):
            if isinstance(val, str):
                if 'Buy' in val or 'Purchase' in val: return 'color: #2ca02c; font-weight: bold'
                elif 'Sale' in val or 'Sell' in val: return 'color: #d62728'
            return ''
        st.dataframe(df_insiders.style.map(color_transaction, subset=['Transaction']), use_container_width=True)
    else:
        st.info("No se han registrado transacciones recientes de insiders.")

    # ==========================================================
    # 5. RANKING DE MERCADO (TU CÓDIGO ORIGINAL MOVIDO AL FINAL)
    # ==========================================================
    st.markdown("---")
    st.markdown("### 🏆 Las Mejores Empresas del Mercado (Buffett Ranking)")
    st.caption("Esta lista se genera automáticamente analizando cientos de empresas mediante el script `screener.py` en segundo plano.")
    
    try:
        df_ranking = pd.read_csv("ranking_mercado.csv")
        podio1, podio2, podio3 = st.columns(3)
        if len(df_ranking) >= 3:
            top1, top2, top3 = df_ranking.iloc[0], df_ranking.iloc[1], df_ranking.iloc[2]
            podio1.metric(f"🥇 1º - {top1['Ticker']}", f"Score: {top1['Buffett Score']}/100", f"ROE: {top1['ROE %']}%")
            podio2.metric(f"🥈 2º - {top2['Ticker']}", f"Score: {top2['Buffett Score']}/100", f"ROE: {top2['ROE %']}%")
            podio3.metric(f"🥉 3º - {top3['Ticker']}", f"Score: {top3['Buffett Score']}/100", f"ROE: {top3['ROE %']}%")
        
        st.dataframe(
            df_ranking.style.background_gradient(subset=['Buffett Score'], cmap='Greens')
                            .background_gradient(subset=['ROE %'], cmap='Blues').format(precision=2),
            use_container_width=True, height=400
        )
    except FileNotFoundError:
        st.warning("⚠️ Todavía no hay datos del mercado. Ejecuta `python screener.py` en tu terminal para generarlos.")

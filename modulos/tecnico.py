import streamlit as st
import yfinance as yf
import pandas as pd
import streamlit.components.v1 as components
from charts import plot_flujo_opciones, plot_grafico_tecnico_pro

# Traemos la función de TradingView que creamos en la Fase 1
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
      "toolbar_bg": "#131722", "studies": ["Volume@tv-basicstudies", "MASimple@tv-basicstudies"]
      }});
      </script>
    </div>
    """
    components.html(codigo_html, height=600)

def ejecutar_tecnico_y_opciones(ticker_input):
    """Muestra el gráfico interactivo de TradingView y datos de opciones/volatilidad."""
    st.markdown(f"### 📈 Análisis Técnico Pro: {ticker_input}")
    
    # Inyectamos el gráfico de TradingView
    renderizar_grafico_tradingview(ticker_input)
    
    # ======== TAB 5 ========
    st.markdown("### 🏆 Las Mejores Empresas del Mercado (Buffett Ranking)")
    st.caption("Esta lista se genera automáticamente analizando cientos de empresas mediante el script `screener.py` en segundo plano.")
    
    try:
        # Leemos la base de datos que generó el bot
        df_ranking = pd.read_csv("ranking_mercado.csv")
        
        # Mostramos el podio visual (Top 3)
        st.markdown("#### 🥇 El Podio Actual")
        podio1, podio2, podio3 = st.columns(3)
        
        if len(df_ranking) >= 3:
            top1 = df_ranking.iloc[0]
            top2 = df_ranking.iloc[1]
            top3 = df_ranking.iloc[2]
            
            podio1.metric(f"🥇 1º - {top1['Ticker']}", f"Score: {top1['Buffett Score']}/100", f"ROE: {top1['ROE %']}%")
            podio2.metric(f"🥈 2º - {top2['Ticker']}", f"Score: {top2['Buffett Score']}/100", f"ROE: {top2['ROE %']}%")
            podio3.metric(f"🥉 3º - {top3['Ticker']}", f"Score: {top3['Buffett Score']}/100", f"ROE: {top3['ROE %']}%")
        
        st.markdown("---")
        st.markdown("#### 📋 Ranking Completo (Top Oportunidades)")
        
        # Damos formato bonito a la tabla
        st.dataframe(
            df_ranking.style.background_gradient(subset=['Buffett Score'], cmap='Greens')
                            .background_gradient(subset=['ROE %'], cmap='Blues')
                            .format(precision=2),
            use_container_width=True,
            height=400
        )
        
        st.info("💡 **Tip:** Para actualizar esta lista con las 500 empresas del S&P 500, edita el archivo `screener.py`, añade todos los tickers, y ejecútalo en tu terminal con `python screener.py`.")
        
    except FileNotFoundError:
        st.warning("⚠️ Todavía no hay datos del mercado. Abre tu terminal de comandos y ejecuta `python screener.py` para analizar el mercado y generar la base de datos.")

    st.markdown("---")
    st.markdown("#### 🕵️ El Rastro del Dinero: Mercado de Derivados (Opciones)")
    st.caption("Los inversores minoristas compran acciones. Los inversores institucionales compran opciones (Calls para apostar al alza, Puts para apostar a la baja o protegerse). Este gráfico suma todos los contratos abiertos para el próximo trimestre.")

    with st.spinner("Descargando la cadena de derivados de Wall Street..."):
        fig_opciones, diag_opciones = plot_flujo_opciones(ticker_input)
        
        if fig_opciones:
            c_opt1, c_opt2 = st.columns([1.5, 1])
            
            with c_opt1:
                st.markdown("#### 📈 Terminal Técnico (TradingView Pro)")
                render_tradingview_widget(ticker_input)
                
            with c_opt2:
                st.markdown("#### 🕵️ El Rastro del Dinero (Opciones)")
                st.plotly_chart(fig_opciones, use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                if "CODICIA" in diag_opciones:
                    st.success(diag_opciones)
                elif "MIEDO" in diag_opciones:
                    st.error(diag_opciones)
                else:
                    st.info(diag_opciones)
                    
                st.markdown("""
                **💡 Leyenda del Analista:**
                *   **Calls > Puts:** Mercado fuertemente alcista.
                *   **Puts > Calls (P/C > 1):** Mercado asustado.
                *   *Nota contrarian:* Si el P/C es absurdamente alto (ej. > 1.5), a veces indica un "pánico injustificado" y marca el suelo perfecto para comprar.
                """)
        else:
            st.warning(diag_opciones)

    # ======== MIEDO Y CODICIA ========


    # ======== TAB 4 ========
    st.markdown("#### 👔 Análisis de la Directiva y Sentimiento del Mercado")
    st.caption("A Buffett le gusta invertir en empresas donde los directivos son dueños de gran parte de las acciones (Skin in the Game).")
    
    insiders, inst, short = obtener_datos_directiva(ticker_input)
    
    col_dir1, col_dir2, col_dir3 = st.columns(3)
    
    if insiders is not None:
        estado_insiders = "Excelente" if insiders > 5 else "Bajo"
        col_dir1.metric("Propiedad de Insiders (Directivos)", f"{insiders:.2f}%", estado_insiders, delta_color="normal" if insiders > 5 else "off")
        
        estado_inst = "Alta convicción" if inst > 60 else "Poco respaldo"
        col_dir2.metric("Propiedad Institucional (Fondos)", f"{inst:.2f}%", estado_inst, delta_color="off")
        
        estado_short = "Ataque Bajista" if short > 5 else "Sano"
        color_short = "inverse" if short > 5 else "normal"
        col_dir3.metric("Short Ratio (Días para cubrir cortos)", f"{short:.2f}", estado_short, delta_color=color_short)
    else:
        st.info("No se pudieron obtener los datos de accionariado de Yahoo Finance.")

    st.markdown("---")

    st.markdown("#### 🕵️ Movimientos Recientes de Directivos (Formulario 4)")
    st.caption("Peter Lynch decía: 'Los insiders pueden vender por muchas razones (comprar una casa, diversificar), pero **solo compran por una razón: creen que el precio va a subir**'.")
    
    df_insiders = obtener_transacciones_insiders(ticker_input)
    if df_insiders is not None:
        # Aplicar colores: Verde para compras (Buy/Purchase), Rojo para ventas (Sale/Sell)
        def color_transaction(val):
            if isinstance(val, str):
                if 'Buy' in val or 'Purchase' in val:
                    return 'color: #2ca02c; font-weight: bold'
                elif 'Sale' in val or 'Sell' in val:
                    return 'color: #d62728'
            return ''
        
        st.dataframe(df_insiders.style.map(color_transaction, subset=['Transaction']), use_container_width=True)
    else:
        st.info("No se han registrado transacciones recientes de insiders en la SEC o los datos no están disponibles.")

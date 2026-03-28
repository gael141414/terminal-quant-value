import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Importamos gráficos que pudieras tener de comparativas
from charts import plot_termometro_macro, plot_radar_comparativo 

def ejecutar_radar_macro(ticker_input, ticker_competidor="", df_sectores):
    """Analiza el entorno macroeconómico, comparativas sectoriales y head-to-head."""
    st.markdown(f"### 🌍 Radar Macro y Competidores: {ticker_input}")
    
    # ======== RADAR ROTACIÓN SECTORIAL ========
    with st.expander("🌍 Radar Macro: ¿Dónde está fluyendo el dinero? (Rotación Sectorial)", expanded=False):
        st.markdown("Los grandes fondos de inversión rotan su capital constantemente. Aquí puedes ver qué sectores están calentándose y cuáles se están quedando atrás.")
        
        with st.spinner("Mapeando el mercado global..."):
            df_sectores = analizar_rotacion_sectores()
            
            if df_sectores is not None and not df_sectores.empty:
                # Separamos en 2 columnas: la tabla y el gráfico
                col_sec1, col_sec2 = st.columns([1, 1.5])
                
                with col_sec1:
                    st.dataframe(
                        df_sectores.set_index("Sector").style.background_gradient(subset=['1 Mes (%)', '3 Meses (%)'], cmap='RdYlGn'),
                        height=350,
                        use_container_width=True
                    )
                
                with col_sec2:
                    fig_sectores = plot_rotacion_sectorial(df_sectores)
                    st.plotly_chart(fig_sectores, use_container_width=True)
                    
                # Damos un insight rápido
                mejor_sector = df_sectores.loc[df_sectores['1 Mes (%)'].idxmax()]['Sector']
                peor_sector = df_sectores.loc[df_sectores['1 Mes (%)'].idxmin()]['Sector']
                st.info(f"💡 **Insight Macro:** En los últimos 30 días, el capital institucional está rotando agresivamente hacia **{mejor_sector}**, mientras abandona **{peor_sector}**.")

    # ======== TAB 9 ========
    st.markdown("### 🎲 Probabilidad y Estacionalidad (Los últimos 20 años)")
    st.caption("Los fondos Quant no adivinan, cuentan cartas. Este mapa de calor analiza la historia completa de la acción para decirte en qué meses tienes las probabilidades matemáticas a tu favor.")
    
    with st.spinner(f"Procesando miles de velas históricas de {ticker_input}..."):
        fig_estacional, diagnostico_estacional = plot_estacionalidad_quant(ticker_input)
        
        if fig_estacional:
            st.plotly_chart(fig_estacional, use_container_width=True)
            st.info(diagnostico_estacional)
            
            st.markdown("---")
            st.markdown("""
            **💡 ¿Cómo usar esta ventaja injusta?**
            *   **Barras Verdes (>60%):** En estos meses, jugar a la baja (cortos) es un suicidio estadístico.
            *   **Barras Rojas (<40%):** Meses de purga. Es el momento perfecto para guardar liquidez y cazar chollos a final de mes.
            *   *Ejemplo clásico:* Muchas tecnológicas (como Apple) sufren en Septiembre y vuelan en Octubre/Noviembre tras presentar resultados.
            """)
        else:
            st.warning(diagnostico_estacional)

    # ======== TAB 6 ========
    st.markdown("### ⚖️ Laboratorio Quant: Optimización de Cartera")
    st.caption("Introduce al menos 3 tickers separados por comas. El algoritmo simulará 2,000 combinaciones para encontrar los pesos exactos que maximizan tu rentabilidad y minimizan la volatilidad (Modelo Markowitz).")
    
    # Input del usuario para los tickers de la cartera
    tickers_cartera = st.text_input("Tickers de tu Cartera (Ej: AAPL, KO, JNJ, V, XOM):", value="AAPL, MSFT, KO, JNJ, V")
    
    if st.button("🚀 Optimizar Pesos (Correr Monte Carlo)"):
        lista_tickers = [t.strip().upper() for t in tickers_cartera.split(",")]
        
        if len(lista_tickers) < 2:
            st.warning("Necesitas al menos 2 empresas para optimizar una cartera.")
        else:
            with st.spinner("Simulando miles de escenarios de mercado..."):
                fig_mark, pesos_rec = plot_frontera_eficiente(lista_tickers)
                
                if fig_mark and pesos_rec:
                    c_opt1, c_opt2 = st.columns([2, 1])
                    
                    with c_opt1:
                        st.plotly_chart(fig_mark, use_container_width=True)
                        
                    with c_opt2:
                        st.markdown("#### 🎯 Asignación Óptima")
                        st.success("Para conseguir el mejor Ratio Sharpe (Riesgo/Beneficio), el modelo matemático recomienda dividir tu capital exactamente así:")
                        
                        # Crear barras visuales para los pesos
                        for tick, peso in pesos_rec.items():
                            if peso > 1.0: # Solo mostrar si tiene más de un 1%
                                st.write(f"**{tick}:** {peso}%")
                                st.progress(peso / 100)

    # ======== TAB 7 ========
    st.markdown("### 🌍 Visión Macro Institucional")
    st.caption("Analizando el flujo del 'Smart Money'. Los grandes fondos no miran las noticias, miran cómo se mueve el capital entre activos refugio y activos de riesgo.")
    
    with st.spinner("Descargando métricas globales e índices adelantados..."):
        fig_macro, diagnostico_macro = plot_termometro_macro()
        
        if fig_macro:
            # 1. Termómetro Principal
            st.plotly_chart(fig_macro, use_container_width=True)
            
            # Extracción del Diccionario de Datos
            datos_macro = analizar_macro_avanzado()
            
            st.markdown("---")
            
            st.markdown("#### 🧭 Dinámicas de Mercado (Smart Money Ratios)")
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            # Curva de Tipos
            spread = datos_macro['spread_curva']
            est_curva = "Invertida 🚨" if spread < 0 else "Normal 🟢"
            col_r1.metric("Curva Tipos (10Y-3M)", f"{spread:+.2f} pts", est_curva, delta_color="inverse" if spread < 0 else "normal")
            
            # Ratio Riesgo (Consumo)
            r_riesgo = datos_macro['ratio_riesgo']
            est_riesgo = "Apetito (Risk-On) 🐂" if r_riesgo > 2.2 else "Miedo (Risk-Off) 🐻"
            col_r2.metric("Apetito al Riesgo (XLY/XLP)", f"{r_riesgo:.2f}x", est_riesgo, delta_color="normal" if r_riesgo > 2.2 else "inverse")
            
            # Dr. Cobre vs Oro
            r_cu_au = datos_macro['ratio_cobre_oro']
            est_cu = "Expansión 🏭" if r_cu_au > 0.18 else "Contracción 📉"
            col_r3.metric("Dr. Copper (Cobre/Oro)", f"{r_cu_au:.3f}", est_cu, delta_color="normal" if r_cu_au > 0.18 else "inverse")
            
            # Amplitud de Mercado
            amplitud = datos_macro['amplitud_mercado']
            est_amp = "Mercado Sano 🌲" if amplitud > 0.30 else "Peligro: Concentrado ⚠️"
            col_r4.metric("Amplitud Mercado (RSP/SPY)", f"{amplitud:.2f}x", est_amp, delta_color="normal" if amplitud > 0.30 else "inverse")

            st.markdown("---")
            
            st.markdown("#### 🛢️ Inflación y Costes de Capital")
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            
            col_i1.metric("Oro (Refugio)", f"${datos_macro['oro']:,.2f}" if datos_macro['oro'] else "N/A")
            col_i2.metric("Cobre (Industria)", f"${datos_macro['cobre']:,.2f}" if datos_macro['cobre'] else "N/A")
            col_i3.metric("Petróleo WTI (Energía)", f"${datos_macro['petroleo']:,.2f}" if datos_macro['petroleo'] else "N/A")
            col_i4.metric("Índice Dólar DXY (Divisa)", f"{datos_macro['dxy']:,.2f}" if datos_macro['dxy'] else "N/A")
            
            st.markdown("---")
            
            st.markdown("#### 🤖 Procesamiento de Noticias (Wall Street Newsfeed)")
            
            c_mac1, c_mac2 = st.columns([1, 2.5])
            
            pol = datos_macro['polaridad']
            with c_mac1:
                if pol > 0.05:
                    st.success("##### 🐂 Tono IA: ALCISTA")
                    st.caption("El procesamiento de lenguaje natural detecta un fuerte optimismo en los titulares de hoy.")
                elif pol < -0.05:
                    st.error("##### 🐻 Tono IA: BAJISTA")
                    st.caption("El procesamiento de lenguaje natural detecta pesimismo, cautela o pánico en la prensa.")
                else:
                    st.info("##### ⚖️ Tono IA: NEUTRAL")
                    st.caption("Las noticias reflejan un mercado sin dirección clara a la espera de datos clave.")
                    
            with c_mac2:
                noticias = datos_macro['noticias']
                if noticias:
                    for noti in noticias:
                        st.markdown(f"**{noti['Sentimiento']}** | [{noti['Titular']}]({noti['Link']})")
                else:
                    st.warning("⚠️ El servidor de noticias de Yahoo está bloqueando la conexión RSS temporalmente.")

        else:
            st.error(f"🚨 Fallo técnico detectado:\n\n{diagnostico_macro}")

    # ======== ORÁCULO TÁCTICO IA ========
    st.markdown("---")
    st.markdown("### 🔮 Oráculo Táctico: Playbook de Inversión IA")
    st.markdown("La Inteligencia Artificial analiza el ciclo económico actual (Curva de tipos, flujos de capital, VIX) y te sugiere cómo balancear tu cartera hoy.")

    if st.button("🧠 Generar Playbook Estratégico", use_container_width=True):
        with st.spinner("La IA está cruzando los datos macroeconómicos e institucionales..."):
            try:
                # 1. Recopilamos el contexto de tu terminal
                spread = datos_macro.get('spread_curva', 0) if 'datos_macro' in locals() else 0
                r_riesgo = datos_macro.get('ratio_riesgo', 0) if 'datos_macro' in locals() else 0
                r_cu_au = datos_macro.get('ratio_cobre_oro', 0) if 'datos_macro' in locals() else 0
                
                mejor_sec = df_sectores.loc[df_sectores['1 Mes (%)'].idxmax()]['Sector'] if 'df_sectores' in locals() and not df_sectores.empty else "Desconocido"
                peor_sec = df_sectores.loc[df_sectores['1 Mes (%)'].idxmin()]['Sector'] if 'df_sectores' in locals() and not df_sectores.empty else "Desconocido"

                # 2. Diseñamos el Prompt Cuantitativo
                prompt_oraculo = f"""
                Eres el Estratega Jefe Macro (Chief Investment Officer) de un Hedge Fund Cuantitativo.
                Tu trabajo es decirle a los clientes exactamente qué hacer con su dinero en este momento preciso basándote ESTRICTAMENTE en estos datos de mercado actuales:
                
                - Curva de Tipos (10Y-3M): {spread:+.2f} pts (Si es negativo, alerta extrema de recesión/riesgo).
                - Apetito al Riesgo (Consumo Discrecional vs Básico): {r_riesgo:.2f}x (Si es < 2.0, el mercado está a la defensiva).
                - Cobre vs Oro (Termómetro industrial): {r_cu_au:.3f} (Si sube, hay expansión. Si baja, hay miedo y se refugian en oro).
                - Momentum Sectorial: El dinero está entrando en {mejor_sec} y huyendo de {peor_sec}.

                Escribe un "Playbook Táctico" (Manual de Acción) dividido en estas 3 secciones:
                1. 🌡️ **Diagnóstico del Ciclo:** ¿En qué fase estamos? (Expansión, Desaceleración, Miedo, Euforia). Usa los datos para justificarlo.
                2. 🎯 **Asignación de Activos (Asset Allocation):** ¿Es momento de estar líquidos (Cash), comprar Bonos (Renta Fija), acumular Oro, o ir largos en Acciones? 
                3. ⚔️ **Estrategia Táctica:** ¿Recomiendas comprar acciones con descuento ahora mismo, usar derivados (opciones Put para cubrirse), o subirse al momentum de {mejor_sec}?

                Tono: Profesional, directo, sin rodeos, como si hablaras con un gestor de patrimonio.
                """

                # 3. Llamamos al cerebro de Gemini
                modelo_oraculo = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        modelo_oraculo = m.name
                        if "flash" in m.name.lower(): break 
                
                if modelo_oraculo:
                    model = genai.GenerativeModel(modelo_oraculo)
                    response = model.generate_content(prompt_oraculo)
                    
                    st.success("✅ Playbook generado con éxito basándose en datos de mercado en tiempo real.")
                    with st.expander("📖 LEER PLAYBOOK TÁCTICO DE LA IA", expanded=True):
                        st.markdown(response.text)
                else:
                    st.error("Error de conexión con la API de la IA.")
            except Exception as e:
                st.error(f"Faltan datos macroeconómicos para generar el oráculo. Espera a que carguen los gráficos superiores. Detalle: {e}")

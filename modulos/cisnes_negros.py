import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

def ejecutar_simulador_crisis(ticker_input):
    st.markdown(f"### 🦢 Simulador de Cisnes Negros: {ticker_input}")
    st.markdown("¿Tienes estómago para aguantar esta acción? Sometemos a la empresa a las peores crisis de la historia reciente para medir su **Resiliencia Extrema** y su pérdida máxima histórica (Max Drawdown).")

    if st.button("🚨 Ejecutar Stress Test Institucional", type="primary", use_container_width=True):
        with st.spinner(f"Simulando colapsos de mercado para {ticker_input}..."):
            try:
                # Descargamos historia máxima
                df = yf.download(ticker_input, period="max")['Close']
                
                if df.empty or len(df) < 252:
                    st.warning("No hay suficiente historia para esta empresa (posiblemente salió a bolsa hace poco). El test requiere datos históricos profundos.")
                    return

                # Definimos los peores momentos de la historia reciente
                crisis = {
                    "📉 Gran Crisis Financiera (2007-2009)": ("2007-10-09", "2009-03-09"),
                    "🦠 Crash del COVID-19 (2020)": ("2020-02-19", "2020-03-23"),
                    "🔥 Shock de Inflación / Tipos (2022)": ("2022-01-03", "2022-10-12")
                }

                resultados = []

                for nombre, (inicio, fin) in crisis.items():
                    # Filtramos por las fechas de la crisis
                    df_crisis = df.loc[inicio:fin]
                    
                    if not df_crisis.empty and len(df_crisis) > 5:
                        p_max = df_crisis.max()
                        p_min = df_crisis.min()
                        drawdown = ((p_min - p_max) / p_max) * 100
                        
                        resultados.append({
                            "Crisis": nombre,
                            "Caída Máxima (%)": drawdown
                        })
                    else:
                        resultados.append({
                            "Crisis": nombre,
                            "Caída Máxima (%)": 0 # Significa que la empresa no existía en esa época
                        })

                # Procesar resultados
                df_res = pd.DataFrame(resultados)
                
                # Gráfico
                st.markdown("#### 🩸 Sangrado Máximo por Crisis (Drawdown)")
                
                # Filtramos las crisis donde sí existía (caída < 0)
                df_res_filtrado = df_res[df_res["Caída Máxima (%)"] < 0].copy()
                
                if not df_res_filtrado.empty:
                    fig = px.bar(
                        df_res_filtrado, x="Caída Máxima (%)", y="Crisis", 
                        orientation='h', text_auto='.2f', 
                        color="Caída Máxima (%)", color_continuous_scale='Reds_r'
                    )
                    fig.update_layout(
                        height=350, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="Pérdida de Capital (%)", yaxis_title=""
                    )
                    fig.update_traces(textposition="outside", texttemplate="%{x:.2f}%")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Diagnóstico
                    peor_caida = df_res_filtrado["Caída Máxima (%)"].min()
                    st.info(f"💡 **Veredicto de Riesgo:** Si el mundo se acaba mañana, debes estar psicológicamente preparado para ver tu inversión en **{ticker_input}** caer un **{abs(peor_caida):.2f}%** en pocos meses, porque ya lo hizo en el pasado.")
                else:
                    st.info("La empresa es demasiado joven para haber pasado por estas crisis.")

            except Exception as e:
                st.error(f"Error calculando cisnes negros: {e}")

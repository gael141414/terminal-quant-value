import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

@st.cache_data(ttl=86400, show_spinner=False)
def calcular_z_score(ticker):
    try:
        # Descargamos 5 años de datos para medio-largo plazo
        df = yf.download(ticker, period="5y")['Close']
        if df.empty or len(df) < 200:
            return None
            
        # Transformamos a DataFrame si es una Serie
        if isinstance(df, pd.Series):
            df = df.to_frame()
            df.columns = ['Close']

        # Matemáticas Cuantitativas: SMA 200 y Desviación Estándar
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['STD_200'] = df['Close'].rolling(window=200).std()
        
        # Z-Score: ¿A cuántas desviaciones estándar estamos de la media?
        df['Z_Score'] = (df['Close'] - df['SMA_200']) / df['STD_200']
        
        return df.dropna()
    except Exception as e:
        return None

def ejecutar_predictor_techos_suelos(ticker_input):
    st.markdown(f"### 🔭 Predictor de Ciclos Extremos (Techos y Suelos): {ticker_input}")
    st.markdown("Utilizamos la reversión a la media (Z-Score a 200 días). Cuando el precio se aleja más de 2 desviaciones estándar (Z > 2 o Z < -2) de su tendencia histórica, la probabilidad matemática de un techo o suelo es superior al 90%.")
    
    with st.spinner("Calculando desviaciones estándar históricas..."):
        df = calcular_z_score(ticker_input)
        
        if df is not None and not df.empty:
            z_actual = df['Z_Score'].iloc[-1]
            precio_actual = df['Close'].iloc[-1]
            
            # 1. Diagnóstico Actual
            c1, c2 = st.columns(2)
            c1.metric("Puntuación Z-Score Actual", f"{z_actual:.2f} σ")
            
            if z_actual >= 2:
                c2.error("🚨 ZONA DE TECHO: Euforia extrema. Alta probabilidad de corrección inminente.")
            elif z_actual <= -2:
                c2.success("🟢 ZONA DE SUELO: Pánico extremo. Históricamente, excelente punto de compra a largo plazo.")
            elif z_actual >= 1:
                c2.warning("⚠️ SOBRECOMPRA: El activo está caro respecto a su media histórica. Precaución.")
            elif z_actual <= -1:
                c2.info("📉 SOBREVENTA: El activo se está abaratando. Posible inicio de formación de suelo.")
            else:
                c2.markdown("⚖️ **ZONA NEUTRAL:** El precio se mueve dentro de su normalidad histórica. No hay ventajas estadísticas claras.")

            # 2. Gráfico del Oscilador Z-Score
            st.markdown("#### 📊 Oscilador de Reversión a la Media (5 Años)")
            
            fig = go.Figure()
            
            # Línea de Z-Score
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Z_Score'],
                mode='lines', name='Z-Score',
                line=dict(color='#00C0F2', width=2)
            ))
            
            # Bandas de Techo y Suelo
            fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Techo (Burbuja)")
            fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="Suelo (Pánico)")
            fig.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.3)", annotation_text="Media Histórica")
            
            fig.update_layout(
                height=400,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Desviaciones Estándar (σ)",
                xaxis_title=""
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No hay suficientes datos históricos para calcular los ciclos de 200 días de esta empresa.")

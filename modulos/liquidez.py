import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_liquidez():
    try:
        import pandas_datareader.data as web
        
        end = datetime.date.today()
        start = end - datetime.timedelta(days=365*5) # Últimos 5 años
        
        # 1. Descargar datos oficiales de la FED (FRED)
        # WALCL: Activos totales (Balance) [Viene en Millones]
        # WTREGEN: Cuenta del Tesoro (TGA) [Viene en Millones]
        # RRPONTSYD: Repos Inversos (Dinero aparcado) [Viene en Billones]
        fed_data = web.DataReader(['WALCL', 'WTREGEN', 'RRPONTSYD'], 'fred', start, end)
        
        # Interpolar huecos (fines de semana)
        fed_data = fed_data.interpolate(method='time').bfill()
        
        # Estandarizar todo a Billones de dólares (Billions USD)
        fed_data['WALCL_B'] = fed_data['WALCL'] / 1000
        fed_data['WTREGEN_B'] = fed_data['WTREGEN'] / 1000
        fed_data['RRP_B'] = fed_data['RRPONTSYD']
        
        # FÓRMULA MÁGICA DE LIQUIDEZ NETA
        fed_data['Liquidez_Neta'] = fed_data['WALCL_B'] - fed_data['WTREGEN_B'] - fed_data['RRP_B']
        
        # 2. Descargar el S&P 500 para comparar
        sp500 = yf.download('^GSPC', start=start, end=end)['Close']
        
        # Fusionar datos
        df = pd.DataFrame({
            'Liquidez Neta (Billones $)': fed_data['Liquidez_Neta'],
            'S&P 500': sp500
        }).dropna()
        
        return df
    except ImportError:
        st.error("🚨 Falta la librería 'pandas-datareader'. Instálala con: pip install pandas-datareader")
        return None
    except Exception as e:
        st.error(f"Error conectando con la Reserva Federal: {e}")
        return None

def ejecutar_monitor_liquidez():
    st.markdown("### 🚰 Monitor de Liquidez Global (The FED Tracker)")
    st.markdown("El verdadero motor del mercado no son los beneficios empresariales, es la **Liquidez Neta**. Si la línea azul (Liquidez) sube, compra acciones. Si baja, el mercado caerá tarde o temprano. *Don't fight the FED.*")

    with st.spinner("Conectando con los servidores de la Reserva Federal (FRED)..."):
        df = obtener_datos_liquidez()
        
        if df is not None and not df.empty:
            # --- KPI ACTUALES ---
            liquidez_actual = df['Liquidez Neta (Billones $)'].iloc[-1]
            liquidez_mes_pasado = df['Liquidez Neta (Billones $)'].iloc[-21] # Aprox 1 mes hábil
            cambio_mensual = liquidez_actual - liquidez_mes_pasado
            
            c1, c2, c3 = st.columns(3)
            c1.metric("💧 Liquidez Neta Actual", f"${liquidez_actual:,.0f} B")
            c2.metric("📊 Inyección/Drenaje (30 Días)", f"${cambio_mensual:+,.0f} B", "Inyectando 🟢" if cambio_mensual > 0 else "Drenando 🔴", delta_color="normal")
            
            if cambio_mensual > 50:
                c3.success("🟢 Viento a Favor (Mercado Alcista sostenido)")
            elif cambio_mensual < -50:
                c3.error("🔴 Viento en Contra (Riesgo severo de corrección)")
            else:
                c3.warning("⚖️ Liquidez Neutral (Mercado lateral)")

            # --- GRÁFICO SUPERPUESTO (DOBLE EJE Y) ---
            st.markdown("#### 📈 Correlación Histórica (Liquidez vs S&P 500)")
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Línea de Liquidez (Azul Brillante)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Liquidez Neta (Billones $)'], 
                name="Liquidez Neta de la FED", 
                line=dict(color='#00C0F2', width=3)
            ), secondary_y=False)
            
            # Línea del S&P 500 (Gris/Blanco)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['S&P 500'], 
                name="S&P 500", 
                line=dict(color='rgba(255,255,255,0.4)', width=2, dash='dot')
            ), secondary_y=True)
            
            fig.update_layout(
                height=500,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="Liquidez (Billones $)", color="#00C0F2", secondary_y=False)
            fig.update_yaxes(title_text="S&P 500 (Puntos)", color="white", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("📖 ¿Cómo se calcula esta brujería matemática?"):
                st.markdown("""
                **Liquidez Neta = Balance Total - TGA - RRP**
                1. **Balance de la FED:** El dinero que imprimen (Suma liquidez).
                2. **TGA (Cuenta del Tesoro):** El dinero que el gobierno recauda en impuestos y guarda sin gastar (Resta liquidez).
                3. **RRP (Repos Inversos):** Dinero que los bancos aparcan en la FED cada noche porque no saben qué hacer con él (Resta liquidez).
                """)

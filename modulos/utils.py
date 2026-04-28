import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components
from textblob import TextBlob
import pandas as pd
from downloader import obtener_estados_financieros

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_transacciones_insiders(ticker):
    """Descarga las últimas compras/ventas de los directivos (Form 4)"""
    try:
        ticker_yf = yf.Ticker(ticker)
        transacciones = ticker_yf.insider_transactions
        
        if transacciones is not None and not transacciones.empty:
            cols_deseadas = ['Start Date', 'Insider', 'Position', 'Transaction', 'Value', 'Shares']
            cols_presentes = [c for c in cols_deseadas if c in transacciones.columns]
            
            df_limpio = transacciones[cols_presentes].copy()
            if 'Start Date' in df_limpio.columns:
                df_limpio['Start Date'] = pd.to_datetime(df_limpio['Start Date']).dt.strftime('%Y-%m-%d')
                
            return df_limpio.head(15)
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def analizar_sentimiento_noticias(ticker):
    """Extrae las últimas noticias y usa NLP para medir el sentimiento"""
    try:
        noticias = yf.Ticker(ticker).news
        if not noticias: return None, 0

        resultados = []
        polaridad_total = 0
        
        for noticia in noticias[:5]:
            titulo = noticia.get('title', '')
            editor = noticia.get('publisher', '')
            enlace = noticia.get('link', '')
            
            analisis = TextBlob(titulo)
            polaridad = analisis.sentiment.polarity 
            
            estado = "Neutral ⚖️"
            if polaridad > 0.15: estado = "Alcista 🟢"
            elif polaridad < -0.15: estado = "Bajista 🔴"
            
            polaridad_total += polaridad
            resultados.append({"Titular": titulo, "Fuente": editor, "Sentimiento": estado, "Polaridad": polaridad, "Link": enlace})
            
        polaridad_media = polaridad_total / len(resultados) if resultados else 0
        return resultados, polaridad_media
    except Exception:
        return None, 0

def renderizar_grafico_tradingview(ticker):
    """Inyecta el widget avanzado y nativo de TradingView interactivo"""
    ticker_tv = ticker.replace("-", ".") 
    codigo_html = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tv_chart_container" style="height:600px;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true, "symbol": "{ticker_tv}", "interval": "D", "timezone": "Etc/UTC",
      "theme": "dark", "style": "1", "locale": "es", "enable_publishing": false,
      "backgroundColor": "#0b0e14", "gridColor": "#1f293d", "hide_top_toolbar": false,
      "hide_legend": false, "save_image": false, "container_id": "tv_chart_container",
      "toolbar_bg": "#131722", "studies": ["Volume@tv-basicstudies", "MASimple@tv-basicstudies"]
      }});
      </script>
    </div>
    """
    components.html(codigo_html, height=600)

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_valoracion_sectorial(ticker):
    """Aplica la regla de valoración relativa según el sector"""
    try:
        info = yf.Ticker(ticker).info
        sector = info.get('sector', 'Desconocido')
        multiplos = {
            'P/E (Price/Earnings)': info.get('trailingPE', 0),
            'P/B (Price/Book)': info.get('priceToBook', 0),
            'EV / EBITDA': info.get('enterpriseToEbitda', 0),
            'EV / Ventas': info.get('enterpriseToRevenue', 0)
        }
        for k, v in multiplos.items():
            if v is None: multiplos[k] = 0
            
        metrica_clave = 'P/E (Price/Earnings)'
        racionalidad = "Para empresas maduras, las ganancias netas estables son el mejor indicador de valor."
        umbral_barato = 15.0
        
        if sector in ['Technology', 'Communication Services']:
            metrica_clave, umbral_barato, racionalidad = 'EV / Ventas', 5.0, "En tecnología se valora el crecimiento y captura de mercado."
        elif sector in ['Financial Services', 'Real Estate']:
            metrica_clave, umbral_barato, racionalidad = 'P/B (Price/Book)', 1.2, "Un ratio menor a 1 indica compras con descuento."
        elif sector in ['Industrials', 'Basic Materials', 'Energy', 'Utilities']:
            metrica_clave, umbral_barato, racionalidad = 'EV / EBITDA', 10.0, "Elimina ruido de amortizaciones de maquinaria."
            
        valor_metrica = multiplos.get(metrica_clave, 0)
        return sector, metrica_clave, valor_metrica, racionalidad, multiplos, umbral_barato
    except Exception as e:
        return None, None, 0, str(e), {}, 0

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_datos_directiva(ticker):
    """Extrae qué porcentaje de la empresa tienen los directivos y fondos"""
    try:
        info = yf.Ticker(ticker).info
        return info.get('heldPercentInsiders', 0) * 100, info.get('heldPercentInstitutions', 0) * 100, info.get('shortRatio', 0)
    except:
        return 0, 0, 0

def escanear_vulnerabilidades(res_is, res_bs, res_cf):
    """Escanea los estados financieros en busca de Red Flags críticas."""
    alertas = []
    
    def get_last(df, col):
        if df is not None and col in df.columns:
            s = df[col].dropna()
            return s.iloc[-1] if not s.empty else None
        return None

    # 1. Riesgo de Quiebra (Deuda)
    deuda_cap = get_last(res_bs["ratios"], "Deuda / Capital")
    if deuda_cap and deuda_cap > 1.2:
        alertas.append(f"🚨 **Apalancamiento Peligroso:** Deuda altísima ({deuda_cap:.2f}x el capital).")

    # 2. Hemorragia de Efectivo
    fcf = get_last(res_cf["ratios"], "Free Cash Flow (B USD)")
    if fcf and fcf < 0:
        alertas.append(f"🔥 **Quema de Caja:** El Free Cash Flow es negativo (${fcf:.2f}B).")

    # 3. Rentabilidad Basura (Márgenes)
    margen_neto = get_last(res_is["ratios"], "Margen Neto %")
    if margen_neto and margen_neto < 5:
        alertas.append(f"⚠️ **Márgenes Críticos:** El margen neto es solo del {margen_neto:.1f}%.")

    # 4. Destrucción de Valor (ROIC)
    roic = get_last(res_bs["ratios"], "ROIC %")
    if roic and roic < 7:
        alertas.append(f"📉 **Destrucción de Capital:** El ROIC ({roic:.1f}%) es menor que el coste de capital promedio.")

    return alertas

def render_tradingview_widget(ticker):
    """Inyecta el terminal avanzado interactivo de TradingView mediante iframe"""
    ticker_tv = ticker.replace("-", ".") 
    html_code = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tradingview_terminal" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true, "symbol": "{ticker_tv}", "interval": "D", "timezone": "exchange",
      "theme": "dark", "style": "1", "locale": "es", "enable_publishing": false,
      "backgroundColor": "#0b1426", "gridColor": "#1e3354", "hide_top_toolbar": false,
      "hide_legend": false, "save_image": false, "container_id": "tradingview_terminal",
      "toolbar_bg": "#0b1426"
      }});
      </script>
    </div>
    """
    import streamlit.components.v1 as components
    components.html(html_code, height=600)

@st.cache_data(show_spinner=False)
def cargar_datos(ticker: str, años: int):
    try:
        return obtener_estados_financieros(ticker, años, usar_cache=True)
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return None, None, None

def calcular_score_buffett(df_is, df_bs, df_cf):
    """Calcula una nota del 0 al 100 basada en las reglas estrictas de Buffett"""
    score = 0
    
    def get_last(df, col):
        if df is not None and col in df.columns:
            s = df[col].dropna()
            return s.iloc[-1] if not s.empty else None
        return None

    mb = get_last(df_is, "Margen Bruto %")
    mn = get_last(df_is, "Margen Neto %")
    roe = get_last(df_bs, "ROE %")
    roic = get_last(df_bs, "ROIC %")
    deuda = get_last(df_bs, "Deuda / Capital")
    capex = get_last(df_cf, "CAPEX % sobre Beneficio")
    fcf = get_last(df_cf, "Free Cash Flow (B USD)")
    buybacks = get_last(df_cf, "Recompras (B USD)")

    # 1. Poder de Precios (25 pts)
    if mb and mb > 40: score += 10
    elif mb and mb > 20: score += 5
    if mn and mn > 20: score += 15
    elif mn and mn > 10: score += 7

    # 2. Eficiencia (30 pts)
    if roe and roe > 15: score += 15
    if roic and roic > 15: score += 15

    # 3. Solidez (25 pts)
    if deuda is not None and deuda < 0.8: score += 15
    elif deuda is not None and deuda < 1.5: score += 7
    if capex is not None and capex < 25: score += 10
    elif capex is not None and capex < 50: score += 5

    # 4. Trato al Accionista (20 pts)
    if fcf and fcf > 0: score += 10
    if buybacks and buybacks > 0: score += 10

    return score

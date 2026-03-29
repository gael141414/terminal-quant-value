import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components

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

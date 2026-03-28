import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import yfinance as yf
from fpdf import FPDF
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import requests
import plotly.express as px
import streamlit.components.v1 as components
import google.generativeai as genai

from downloader import obtener_estados_financieros
from income_analyzer import analizar_cuenta_resultados
from balance_analyzer import analizar_balance
from cashflow_analyzer import analizar_flujo_efectivo
from valuator import valorar_empresa
from plotly.subplots import make_subplots
from textblob import TextBlob
from streamlit_lottie import st_lottie
from charts import (
    plot_dashboard_interactivo, plot_per_bands, plot_tsr_vs_sp500, plot_calidad_beneficios,
    plot_auditoria_forense, plot_flujo_opciones, plot_proyeccion_dividendos, plot_beneish_m_score,
    plot_treemap_competidores, plot_adn_financiero, plot_anillo_puntuacion, plot_frontera_eficiente,
    plot_estacionalidad_quant, plot_grafico_tecnico_pro, plot_termometro_macro, plot_radar_comparativo,
    plot_football_field, plot_termometro_deuda, plot_capital_allocation_waterfall, plot_comparativa_historica,
    plot_owner_earnings, plot_shareholder_yield_historico, plot_ev_fcf_historico, plot_rotacion_sectorial
)
from modulos.roboadvisor import ejecutar_roboadvisor
from modulos.proyeccion import ejecutar_proyeccion
from modulos.backtest import ejecutar_maquina_del_tiempo
from modulos.radar import ejecutar_radar_multibagger
from modulos.forense import ejecutar_auditoria_forense

genai.configure(api_key="AIzaSyAcKJlq_hy1TdaX19ioPIzkYKvYWiUZYh4")
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ---------------- CONFIGURACIÓN ---------------- #
# 1. CONFIGURACIÓN DE PÁGINA (Debe ser el primer comando de Streamlit)
st.set_page_config(
    page_title="ValueQuant Terminal", 
    page_icon="🦅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. INYECCIÓN DE CSS INSTITUCIONAL (Estilo TradingView/Bloomberg)
st.markdown("""
<style>
    /* Importar tipografía profesional (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Aplicar fuente y color de fondo global */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Fondo principal: Negro azulado profundo */
    .stApp {
        background-color: #0b0e14; 
    }

    /* Ocultar la marca de Streamlit (Header, Footer, Menú hamburguesa) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Estilizar el panel lateral (Sidebar) */
    [data-testid="stSidebar"] {
        background-color: #131722; /* Color exacto del sidebar de TradingView */
        border-right: 1px solid #2a2e39;
    }

    /* Ajustar los márgenes para aprovechar el 100% de la pantalla */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 100% !important;
    }

    /* Estilo de las tarjetas de métricas (Metrics Cards) */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #d1d4dc !important; /* Blanco roto suave */
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: #8a93a6 !important; /* Gris azulado */
    }

    /* Estilo de los botones genéricos */
    .stButton>button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        border: 1px solid #2962ff !important; /* Azul TradingView */
        background-color: rgba(41, 98, 255, 0.05) !important;
        color: #2962ff !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: rgba(41, 98, 255, 0.15) !important;
        border: 1px solid #2962ff !important;
    }
    
    /* Botón primario (Los que dicen type="primary") */
    .stButton>button[kind="primary"] {
        background-color: #2962ff !important;
        color: white !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #1e4bd8 !important;
    }

    /* Líneas separadoras más sutiles */
    hr {
        border-top: 1px solid #2a2e39 !important;
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
    }
    
    /* Cajas de Alertas (Success, Info, Warning) */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INYECCIÓN DE CSS (ANIMACIONES Y ESTILOS)
# ==========================================
def aplicar_estilos_premium():
    st.markdown("""
        <style>
        /* 1. Ocultar marcas de agua de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* 2. Animación "Hover" para las Tarjetas de Métricas */
        div[data-testid="metric-container"] {
            background-color: #16243d;
            border: 1px solid #1e3354;
            padding: 5% 5% 5% 10%;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease-in-out;
        }
        
        /* Efecto al pasar el ratón */
        div[data-testid="metric-container"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 192, 242, 0.2);
            border: 1px solid #00C0F2;
        }

        /* 3. Animación de "Pulso" para alertas importantes */
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(214, 39, 40, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(214, 39, 40, 0); }
            100% { box-shadow: 0 0 0 0 rgba(214, 39, 40, 0); }
        }
        .alerta-pulso {
            animation: pulse 2s infinite;
            border-radius: 5px;
        }

        /* 4. Estilizar las pestañas (Tabs) para que parezcan botones premium */
        div[data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        div[data-baseweb="tab"] {
            background-color: #16243d;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 16px;
            border: 1px solid #1e3354;
            border-bottom: none;
        }
        div[aria-selected="true"] {
            background-color: #00C0F2 !important;
            color: #000000 !important;
            font-weight: bold;
        }
        .stApp {
            background: radial-gradient(circle at 15% 50%, rgba(0, 192, 242, 0.08), transparent 25%),
                        radial-gradient(circle at 85% 30%, rgba(255, 0, 85, 0.05), transparent 25%);
            background-color: #0b1426;
        }
        div[data-testid="metric-container"] {
            background: rgba(22, 36, 61, 0.6) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important;
            padding: 15px !important;
        }
        div[data-testid="stDataFrame"] > div {
            background: rgba(22, 36, 61, 0.6) !important;
            border-radius: 10px;
            border: 1px solid rgba(0, 192, 242, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

# Llama a la función inmediatamente
aplicar_estilos_premium()

# ==========================================
# WIDGET RADICAL: TICKER TAPE ANIMADO
# ==========================================
@st.cache_data(ttl=3600) # Se actualiza cada 1 hora para no saturar la API
def obtener_datos_ticker_tape():
    indices = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI", "VIX": "^VIX", "ORO": "GC=F", "PETRÓLEO": "CL=F"}
    items = []
    for nombre, ticker in indices.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")
            if len(data) >= 2:
                change = ((data["Close"].iloc[-1] - data["Close"].iloc[-2]) / data["Close"].iloc[-2]) * 100
                clase = "positivo" if change > 0 else "negativo"
                simbolo = "▲" if change > 0 else "▼"
                items.append(f'<div class="ticker-item">{nombre} <span class="{clase}">{simbolo} {change:.2f}%</span></div>')
        except:
            continue
    return ''.join(items)

def render_ticker_tape():
    items_html = obtener_datos_ticker_tape()
    html = f"""
    <style>
    .ticker-wrap {{ width: 100%; background-color: #0b1426; border-top: 1px solid #1e3354; border-bottom: 1px solid #1e3354; padding: 8px 0; overflow: hidden; white-space: nowrap; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; }}
    .ticker {{ display: inline-block; white-space: nowrap; padding-right: 100%; animation: ticker 30s linear infinite; }}
    .ticker:hover {{ animation-play-state: paused; }}
    .ticker-item {{ display: inline-block; padding: 0 2rem; font-size: 1.1rem; color: #E0E6ED; font-weight: 600; }}
    .positivo {{ color: #00ff88; text-shadow: 0 0 5px rgba(0,255,136,0.5); }}
    .negativo {{ color: #ff0055; text-shadow: 0 0 5px rgba(255,0,85,0.5); }}
    @keyframes ticker {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-100%, 0, 0); }} }}
    </style>
    <div class="ticker-wrap"><div class="ticker">{items_html}</div></div>
    """
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=86400) # Se guarda en memoria durante 24 horas
def analizar_rotacion_sectores():
    """Descarga el rendimiento de los 11 sectores del S&P 500 usando sus ETFs"""
    etfs = {
        '💻 Tecnología': 'XLK', '💊 Salud': 'XLV', '🏦 Finanzas': 'XLF',
        '🛍️ Cons. Discrecional': 'XLY', '🍞 Cons. Básico': 'XLP', '🛢️ Energía': 'XLE',
        '🏭 Industriales': 'XLI', '🧱 Materiales': 'XLB', '🏠 Inmobiliario': 'XLRE',
        '⚡ Utilities': 'XLU', '📡 Comunicaciones': 'XLC'
    }
    datos = []
    for sector, ticker_etf in etfs.items():
        try:
            # Descargamos 3 meses de historia de cada ETF
            hist = yf.Ticker(ticker_etf).history(period="3mo")
            if len(hist) >= 21: # 21 días laborables = 1 mes
                p_actual = hist['Close'].iloc[-1]
                p_1m = hist['Close'].iloc[-21]
                p_3m = hist['Close'].iloc[0]
                
                r_1m = ((p_actual - p_1m) / p_1m) * 100
                r_3m = ((p_actual - p_3m) / p_3m) * 100
                
                datos.append({'Sector': sector, '1 Mes (%)': r_1m, '3 Meses (%)': r_3m})
        except:
            continue
            
    return pd.DataFrame(datos) if datos else None

# ---------------- DATA LOADER ---------------- #
@st.cache_data(show_spinner=False)
def cargar_datos(ticker: str, años: int):
    try:
        return obtener_estados_financieros(ticker, años, usar_cache=True)
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return None, None, None

def obtener_transacciones_insiders(ticker):
    """Descarga las últimas compras/ventas de los directivos (Form 4)"""
    try:
        import pandas as pd
        ticker_yf = yf.Ticker(ticker)
        transacciones = ticker_yf.insider_transactions
        
        if transacciones is not None and not transacciones.empty:
            # Seleccionamos columnas útiles si están disponibles
            cols_deseadas = ['Start Date', 'Insider', 'Position', 'Transaction', 'Value', 'Shares']
            cols_presentes = [c for c in cols_deseadas if c in transacciones.columns]
            
            df_limpio = transacciones[cols_presentes].copy()
            # Formatear la fecha para que sea legible
            if 'Start Date' in df_limpio.columns:
                df_limpio['Start Date'] = pd.to_datetime(df_limpio['Start Date']).dt.strftime('%Y-%m-%d')
                
            return df_limpio.head(15) # Devolvemos las 15 más recientes
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=86400 * 7) # Se actualiza 1 vez a la semana
def obtener_tickers_filtrados():
    """Descarga la lista de la SEC y filtra ETFs, SPACS y empresas extranjeras"""
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {'User-Agent': 'ValueQuant Terminal (contacto@valuequant.com)'} 
        r = requests.get(url, headers=headers, timeout=5)
        datos = r.json()
        
        # 🛡️ FILTRO ANTI-BASURA EXTREMO
        filtros_basura = [
            " ADR", " LTD", " LIMITED", " PLC", " S.A.", " N.V.", 
            " FUND", " TRUST", " ETF", " ACQUISITION", " SPAC",
            " BLANK CHECK", " BANCORP" # Añadimos más filtros de Wall Street
        ]
        
        lista_formateada = []
        for v in datos.values():
            nombre_mayus = str(v['title']).upper()
            
            if not any(basura in nombre_mayus for basura in filtros_basura):
                lista_formateada.append(f"{v['ticker']} - {v['title'].title()}")
                
        return sorted(lista_formateada)
    except Exception as e:
        return ["AAPL - Apple Inc.", "MSFT - Microsoft Corp."]

# ==========================================
# WIDGET RADICAL 2: MOTOR TRADINGVIEW EN VIVO
# ==========================================
def render_tradingview_widget(ticker):
    """Inyecta el terminal avanzado interactivo de TradingView mediante iframe"""
    
    # Algunos tickers de Yahoo Finance (ej. BRK-B) necesitan limpieza para TradingView
    ticker_tv = ticker.replace("-", ".") 
    
    html_code = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tradingview_terminal" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{ticker_tv}",
      "interval": "D",
      "timezone": "exchange",
      "theme": "dark",
      "style": "1",
      "locale": "es",
      "enable_publishing": false,
      "backgroundColor": "#0b1426",
      "gridColor": "#1e3354",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "container_id": "tradingview_terminal",
      "toolbar_bg": "#0b1426"
    }}
      );
      </script>
    </div>
    <!-- TradingView Widget END -->
    """
    # Renderizamos el HTML incrustado con una altura de 600 píxeles
    components.html(html_code, height=600)

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

import streamlit.components.v1 as components

def renderizar_grafico_tradingview(ticker):
    """Inyecta el widget avanzado y nativo de TradingView interactivo"""
    codigo_html = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tv_chart_container" style="height:600px;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{ticker}",
      "interval": "D",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "es",
      "enable_publishing": false,
      "backgroundColor": "#0b0e14",
      "gridColor": "#1f293d",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "container_id": "tv_chart_container",
      "toolbar_bg": "#131722",
      "studies": [
        "Volume@tv-basicstudies",
        "MASimple@tv-basicstudies"
      ]
    }}
      );
      </script>
    </div>
    """
    components.html(codigo_html, height=600)

def obtener_valoracion_sectorial(ticker):
    """Aplica la regla de valoración relativa según el sector (Basado en el marco institucional)"""
    try:
        info = yf.Ticker(ticker).info
        sector = info.get('sector', 'Desconocido')
        
        # Rescatamos todos los múltiplos posibles
        multiplos = {
            'P/E (Price/Earnings)': info.get('trailingPE', 0),
            'P/B (Price/Book)': info.get('priceToBook', 0),
            'EV / EBITDA': info.get('enterpriseToEbitda', 0),
            'EV / Ventas': info.get('enterpriseToRevenue', 0)
        }
        
        # Limpiamos nulos
        for k, v in multiplos.items():
            if v is None: multiplos[k] = 0
            
        # Lógica de Selección Institucional
        metrica_clave = 'P/E (Price/Earnings)' # Métrica por defecto
        racionalidad = "Para empresas maduras, las ganancias netas estables son el mejor indicador de valor."
        umbral_barato = 15.0
        
        if sector in ['Technology', 'Communication Services']:
            metrica_clave = 'EV / Ventas'
            racionalidad = "En tecnología y software, se valora el crecimiento y la captura de mercado (Top-Line). Muchas reinvierten todo y no tienen beneficio neto hoy."
            umbral_barato = 5.0
            
        elif sector in ['Financial Services', 'Real Estate']:
            metrica_clave = 'P/B (Price/Book)'
            racionalidad = "En bancos y aseguradoras, los activos financieros son un proxy directo del valor. Un ratio menor a 1 indica que compras sus activos con descuento."
            umbral_barato = 1.2
            
        elif sector in ['Industrials', 'Basic Materials', 'Energy', 'Utilities']:
            metrica_clave = 'EV / EBITDA'
            racionalidad = "En industria pesada, elimina el ruido de las agresivas políticas de amortización de maquinaria y diferencias impositivas."
            umbral_barato = 10.0
            
        elif sector in ['Consumer Defensive', 'Healthcare']:
            metrica_clave = 'P/E (Price/Earnings)'
            racionalidad = "Sectores estables y predecibles. El mercado paga por la seguridad del beneficio neto constante."
            umbral_barato = 15.0
            
        valor_metrica = multiplos.get(metrica_clave, 0)
        
        return sector, metrica_clave, valor_metrica, racionalidad, multiplos, umbral_barato
        
    except Exception as e:
        return None, None, 0, str(e), {}, 0

from textblob import TextBlob # 👈 ¡AÑADE ESTO ARRIBA DEL TODO EN TUS IMPORTS!

def escanear_vulnerabilidades(res_is, res_bs, res_cf):
    """Escanea los estados financieros en busca de Red Flags críticas."""
    alertas = []
    
    # Función auxiliar rápida
    def get_last(df, col):
        if df is not None and col in df.columns:
            s = df[col].dropna()
            return s.iloc[-1] if not s.empty else None
        return None

    # 1. Riesgo de Quiebra (Deuda)
    deuda_cap = get_last(res_bs["ratios"], "Deuda / Capital")
    if deuda_cap and deuda_cap > 1.2:
        alertas.append(f"🚨 **Apalancamiento Peligroso:** Deuda altísima ({deuda_cap:.2f}x el capital). Muy vulnerable a subidas de tipos de interés.")

    # 2. Hemorragia de Efectivo
    fcf = get_last(res_cf["ratios"], "Free Cash Flow (B USD)")
    if fcf and fcf < 0:
        alertas.append(f"🔥 **Quema de Caja:** El Free Cash Flow es negativo (${fcf:.2f}B). La empresa está perdiendo dinero real y podría necesitar emitir acciones o más deuda.")

    # 3. Rentabilidad Basura (Márgenes)
    margen_neto = get_last(res_is["ratios"], "Margen Neto %")
    if margen_neto and margen_neto < 5:
        alertas.append(f"⚠️ **Márgenes Críticos:** El margen neto es solo del {margen_neto:.1f}%. La empresa no tiene poder de fijación de precios (Moat débil).")

    # 4. Destrucción de Valor (ROIC)
    roic = get_last(res_bs["ratios"], "ROIC %")
    if roic and roic < 7:
        alertas.append(f"📉 **Destrucción de Capital:** El ROIC ({roic:.1f}%) es menor que el coste de capital promedio. Crecer destruye valor para el accionista.")

    return alertas

def analizar_sentimiento_noticias(ticker):
    """Extrae las últimas noticias y usa NLP para medir el sentimiento (Alcista/Bajista)"""
    try:
        noticias = yf.Ticker(ticker).news
        if not noticias: return None, 0

        resultados = []
        polaridad_total = 0
        
        # Leemos solo las 5 noticias más recientes para no saturar
        for noticia in noticias[:5]:
            titulo = noticia.get('title', '')
            editor = noticia.get('publisher', '')
            enlace = noticia.get('link', '')
            
            # --- Magia NLP (Análisis de Sentimiento) ---
            # TextBlob lee el texto en inglés y le asigna un valor de -1 (Muy Negativo) a +1 (Muy Positivo)
            analisis = TextBlob(titulo)
            polaridad = analisis.sentiment.polarity 
            
            estado = "Neutral ⚖️"
            if polaridad > 0.15: estado = "Alcista 🟢"
            elif polaridad < -0.15: estado = "Bajista 🔴"
            
            polaridad_total += polaridad
            
            resultados.append({
                "Titular": titulo,
                "Fuente": editor,
                "Sentimiento": estado,
                "Polaridad": polaridad,
                "Link": enlace
            })
            
        polaridad_media = polaridad_total / len(resultados) if resultados else 0
        
        return resultados, polaridad_media
    except Exception as e:
        return None, 0

def generar_reporte_pdf(ticker, precio, res_val, nota, fcf_yield, buyback_yield):
    """Genera un informe institucional en PDF de 1 página (Tear Sheet)"""
    pdf = FPDF()
    pdf.add_page()
    
    # --- CABECERA ---
    pdf.set_fill_color(31, 119, 180) # Azul corporativo
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 18, f" TEAR SHEET VALUE: {ticker} ", ln=True, align='C', fill=True)
    
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 8, "Generado por Buffett Terminal Analytics (IA Cuantitativa)", ln=True, align='C')
    pdf.ln(5)
    
    # --- 1. SCORE GENERAL ---
    color_score = (44, 160, 44) if nota >= 80 else (255, 127, 14) if nota >= 50 else (214, 39, 40)
    pdf.set_fill_color(*color_score)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 12, f" CALIDAD FUNDAMENTAL (BUFFETT SCORE): {nota} / 100 ", ln=True, align='C', fill=True)
    pdf.ln(8)
    
    # --- 2. VALORACIÓN Y MARGEN DE SEGURIDAD ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Valoracion Intrinseca (Modelo DCF Automizado)", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Línea separadora
    pdf.ln(3)
    
    pdf.set_font("Arial", '', 11)
    if res_val and precio:
        g = res_val.get('crecimiento_sostenible', 0.05)
        r = res_val.get('tasa_descuento_capm', 0.10)
        eps = res_val.get('eps_actual', 0)
        per = res_val.get('per_asumido', 15)
        
        v_i = (eps * ((1 + g)**10) * per) / ((1 + r)**10)
        margen = ((precio - v_i) / v_i) * 100
        estado = "SOBREVALORADA" if margen > 0 else "INFRAVALORADA (Ganga)"
        
        pdf.cell(90, 8, f"Precio Mercado Hoy: ${precio:.2f}")
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, f"Valor Intrinseco Justo: ${v_i:.2f}", ln=True)
        pdf.set_font("Arial", '', 11)
        
        pdf.cell(90, 8, f"Crecimiento asig. (g): {g*100:.1f}%")
        pdf.cell(0, 8, f"Tasa Descuento (CAPM): {r*100:.1f}%", ln=True)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(*((214,39,40) if margen > 0 else (44,160,44)))
        pdf.cell(0, 10, f">> ESTADO ACTUAL: {estado} ({abs(margen):.1f}%)", ln=True)
    else:
        pdf.cell(0, 8, "Datos insuficientes para valoracion matematica.", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)
    
    # --- 3. RETORNO AL ACCIONISTA ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "2. Retribucion Real al Accionista", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Arial", '', 11)
    total_yield = fcf_yield + buyback_yield
    pdf.cell(0, 8, f"- FCF Yield (Caja libre sobre precio): {fcf_yield:.2f}%", ln=True)
    pdf.cell(0, 8, f"- Buyback Yield (Recompra de acciones): {buyback_yield:.2f}%", ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f">> RENDIMIENTO TOTAL EFECTIVO: {total_yield:.2f}%", ln=True)
    pdf.ln(8)
    
    # --- 4. VEREDICTO ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Veredicto del Algoritmo Value", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font("Arial", '', 11)
    if nota >= 80:
        texto = "EXCELENTE. Foso economico inquebrantable, rentabilidad sobresaliente y deuda controlada. Un claro candidato para mantener a largo plazo al estilo Berkshire Hathaway."
    elif nota >= 50:
        texto = "PRECAUCION. Negocio solido pero presenta debilidades en margenes, niveles de deuda, o su cotizacion exige demasiado crecimiento futuro. Mantener en el radar."
    else:
        texto = "ALERTA ROJA. Fundamentales deteriorados. Alta probabilidad de destruccion de valor por mala asignacion de capital o deuda asfixiante."
        
    pdf.multi_cell(0, 6, texto)
    
    # Guardar
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name

def analizar_macro_avanzado():
    """Descarga commodities, ratios institucionales y noticias RSS en crudo"""
    
    def obtener_precio_seguro(ticker_symbol):
        try:
            data = yf.Ticker(ticker_symbol).history(period="5d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except:
            pass
        return 0.0

    # 1. INDICADORES BÁSICOS E INFLACIÓN
    irx = obtener_precio_seguro('^IRX')       
    tnx = obtener_precio_seguro('^TNX')       
    oro = obtener_precio_seguro('GC=F')       
    petroleo = obtener_precio_seguro('CL=F')  
    dxy = obtener_precio_seguro('DX-Y.NYB')   

    # 2. INDICADORES ADELANTADOS (SMART MONEY)
    cobre = obtener_precio_seguro('HG=F')
    xly = obtener_precio_seguro('XLY') # Consumo Cíclico (Lujos)
    xlp = obtener_precio_seguro('XLP') # Consumo Defensivo (Básicos)
    spy = obtener_precio_seguro('SPY') # S&P 500 Ponderado por Capitalización
    rsp = obtener_precio_seguro('RSP') # S&P 500 Equitativo (Igual peso)

    # Cálculos de Ratios
    spread_curva = tnx - irx if tnx > 0 and irx > 0 else 0
    ratio_cobre_oro = (cobre / oro) * 100 if oro > 0 else 0
    ratio_riesgo = xly / xlp if xlp > 0 else 0
    amplitud_mercado = rsp / spy if spy > 0 else 0

    # 3. EXTRACCIÓN DE NOTICIAS BLINDADA (VÍA RSS RAW)
    titulares_macro = []
    polaridad_media = 0
    polaridad_total = 0
    
    try:
        url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY&region=US&lang=en-US"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        
        for item in root.findall('./channel/item')[:6]:
            titulo = item.find('title').text
            enlace = item.find('link').text
            
            # Análisis NLP
            polaridad = TextBlob(titulo).sentiment.polarity
            estado = "Neutral ⚖️"
            if polaridad > 0.05: estado = "Alcista 🟢"
            elif polaridad < -0.05: estado = "Bajista 🔴"
            
            polaridad_total += polaridad
            titulares_macro.append({
                "Titular": titulo,
                "Link": enlace,
                "Sentimiento": estado,
            })
            
        if titulares_macro:
            polaridad_media = polaridad_total / len(titulares_macro)
            
    except Exception as e:
        print(f"Error RSS: {e}")

    return {
        "spread_curva": spread_curva, "oro": oro, "petroleo": petroleo, 
        "dxy": dxy, "cobre": cobre, "ratio_cobre_oro": ratio_cobre_oro,
        "ratio_riesgo": ratio_riesgo, "amplitud_mercado": amplitud_mercado,
        "noticias": titulares_macro, "polaridad": polaridad_media
    }

@st.cache_data(show_spinner=False)
def obtener_datos_directiva(ticker):
    """Extrae qué porcentaje de la empresa tienen los directivos y fondos"""
    try:
        info = yf.Ticker(ticker).info
        insiders = info.get('heldPercentInsiders', 0) * 100
        instituciones = info.get('heldPercentInstitutions', 0) * 100
        short_ratio = info.get('shortRatio', 0)
        return insiders, instituciones, short_ratio
    except:
        return None, None, None

# ==========================================
# INYECCIÓN DE CSS FINTECH (UI/UX AVANZADO)
# ==========================================
st.markdown("""
    <style>
    /* 1. Importar tipografía moderna de Google Fonts (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* 2. Títulos con degradado metálico/neón */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #00C0F2, #ffffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* 3. El Botón Principal: Gradiente, Sombra y Efecto Hover 3D */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00C0F2 0%, #0063f2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 192, 242, 0.4);
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 192, 242, 0.6);
        background: linear-gradient(90deg, #0063f2 0%, #00C0F2 100%);
    }

    /* 4. Estilizar el Fondo de Pantalla (Glassmorphism sutil) */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* 5. Inputs de Texto (Cajas de Ticker) estilo Premium */
    .stTextInput input {
        background-color: #16243d !important;
        color: #00C0F2 !important;
        border: 1px solid #1e3354 !important;
        border-radius: 8px !important;
        font-weight: bold;
        text-align: center;
        letter-spacing: 2px;
        font-size: 1.1rem !important;
    }
    .stTextInput input:focus {
        border-color: #00C0F2 !important;
        box-shadow: 0 0 10px rgba(0, 192, 242, 0.3) !important;
    }

    /* 6. Scrollbars Invisibles (Barras de desplazamiento limpias) */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent; 
    }
    ::-webkit-scrollbar-thumb {
        background: #1e3354; 
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00C0F2; 
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- UI PREMIUM & CONTROL CENTRAL ---------------- #        

# 1. SIDEBAR (CONTROL CENTRAL)
with st.sidebar:
    lottie_url = "https://assets3.lottiefiles.com/packages/lf20_fi0ty9ak.json" 
    lottie_trading = load_lottieurl(lottie_url)
    if lottie_trading:
        st_lottie(lottie_trading, height=180, key="trading_anim")
    
    st.markdown("<h3 style='text-align: center; color: #E0E6ED;'>⚙️ Configuración</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 1. Cargamos la base de datos gigante de forma instantánea desde la caché
    lista_tickers_sec = obtener_tickers_filtrados()
    
    # 2. Buscamos el índice de Apple para que siga siendo el valor por defecto
    indice_aapl = next((i for i, item in enumerate(lista_tickers_sec) if item.startswith("AAPL -")), 0)
    
    # 3. El Buscador Principal
    seleccion_principal = st.selectbox(
        "🎯 Buscar Empresa (Ticker o Nombre)", 
        options=lista_tickers_sec, 
        index=indice_aapl,
        help="Escribe el nombre de la empresa o el Ticker. Ej: 'Nvidia' o 'NVDA'"
    )
    # Extraemos solo el Ticker (lo que hay antes del guión) para que el código siga funcionando
    ticker_input = seleccion_principal.split(" - ")[0]

    # 4. El Buscador del Competidor
    lista_competidores = [""] + lista_tickers_sec # Le añadimos una opción vacía al principio
    seleccion_competidor = st.selectbox(
        "🥊 Comparador (Opcional)", 
        options=lista_competidores, 
        index=0,
        help="Selecciona un rival para habilitar el modo Batalla Head-to-Head."
    )
    ticker_competidor = seleccion_competidor.split(" - ")[0] if seleccion_competidor else ""
    años_hist = st.slider("Años históricos", 5, 20, 10)
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Botón de análisis
    ejecutar = st.button("🚀 ANALIZAR TERMINAL", use_container_width=True)
    
    # 1. GESTIÓN DEL ESTADO (MEMORIA)
    if ejecutar and ticker_input:
        st.session_state['analizado'] = True
        st.session_state['ticker_actual'] = ticker_input

    # 2. MENÚ DE NAVEGACIÓN (Solo aparece si ya hemos analizado)
    if st.session_state.get('analizado', False):
        st.markdown("---")
        st.markdown("<h4 style='color: #8c9bba;'>🧭 Navegación</h4>", unsafe_allow_html=True)
        seccion_actual = st.radio("Ir a:", [
            "📊 Resumen Ejecutivo",
            "🔎 Análisis Fundamental",
            "📈 Técnico y Opciones",
            "🌍 Radar Macro y Sectores",
            "🧠 Auditoría Forense",
            "🤖 Robo-Advisor & Test Perfil",
            "🔮 Proyección IA y Catalizadores",
            "⏳ Máquina del Tiempo (Backtest)",
            "🚀 Radar Multibaggers (Small/Mid Caps)"
        ], label_visibility="collapsed")

# ==========================================
# PANTALLA DE INICIO (LANDING PAGE SAAS)
# ==========================================
if not st.session_state.get('analizado', False):
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Dividimos la pantalla: 60% texto a la izquierda, 40% animación a la derecha
    col_hero_texto, col_hero_anim = st.columns([1.2, 1])
    
    with col_hero_texto:
        st.markdown("<h1 style='font-size: 4.5rem; color: #E0E6ED;'>🦅 Value<span style='color: #00C0F2;'>Quant</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.2rem; color: #8c9bba;'>La terminal institucional para el inversor inteligente.<br>Inteligencia Artificial, Análisis Forense y Cuantitativo en un solo lugar.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #00C0F2;'>👈 Introduce un Ticker en el panel lateral para comenzar</h4>", unsafe_allow_html=True)
        
    with col_hero_anim:
        # Cargamos una animación de análisis de datos para rellenar el espacio derecho
        lottie_landing = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_1w3l1m2h.json") 
        if lottie_landing:
            st_lottie(lottie_landing, height=250, key="landing_anim")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Las 3 tarjetas de información debajo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📊 **Datos Institucionales**\n\nConéctate en tiempo real a la SEC y obtén décadas de historia financiera.")
    with col2:
        st.success("🧠 **Inteligencia Artificial**\n\nUn copiloto RAG integrado que audita los balances por ti en milisegundos.")
    with col3:
        st.warning("⚠️ **Auditoría Forense**\n\nDetecta quema de caja, deuda tóxica y manipulación contable (Z-Score & M-Score).")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_ticker_tape()
    st.stop() # Detenemos la app aquí para que no cargue nada más

    st.markdown("---")
    st.caption("Terminal v3.0 | Arquitectura Institucional")
    
# 2. CARGA DE DATOS (SILENCIOSA Y PROFESIONAL)
render_ticker_tape()

with st.spinner(f"Sincronizando con Wall Street... Descargando {años_hist} años de datos para {ticker_input}"):
    is_df, bs_df, cf_df = cargar_datos(ticker_input, años_hist)

if is_df is None:
    st.error("🚨 Fallo de conexión con la SEC/Yahoo Finance. Verifica el Ticker.")
    st.stop()

# Procesamiento en background
res_is = analizar_cuenta_resultados(is_df, cf_df)
res_bs = analizar_balance(bs_df, is_df)
res_cf = analizar_flujo_efectivo(cf_df, is_df)
res_val = valorar_empresa(is_df, bs_df, cf_df, ticker_input)
nota_final = calcular_score_buffett(res_is["ratios"], res_bs["ratios"], res_cf["ratios"])

# --- EXTRACCIÓN GLOBAL DE VARIABLES SEGURAS ---
precio_actual = res_val.get('precio_actual', 0) if res_val else 0
eps_actual = res_val.get('eps_actual', 0) if res_val else 0
earnings_yield = res_val.get('earnings_yield', 0) if res_val else 0
tasa_riesgo = res_val.get('tasa_libre_riesgo', 0) if res_val else 0
acciones_actuales = res_val.get('acciones_actuales', 0) if res_val else 0

# ==========================================
# ENRUTADOR DE VISTAS (SPA ROUTER)
# ==========================================
if seccion_actual == "📊 Resumen Ejecutivo":
    # ======== HERO SECTION & SCORECARD ========
    precio_mercado = res_val.get('precio_actual', 0) if res_val else 0

    col_hero1, col_hero2, col_hero3 = st.columns([2, 1, 1])
    
    with col_hero1:
        st.markdown(f"<h1 style='font-size: 3.5rem; margin-bottom: 0px;'>{ticker_input}</h1>", unsafe_allow_html=True)
        st.caption("Value Intelligence Terminal | Análisis Cuantitativo")
    
    with col_hero2:
        st.metric("Precio de Mercado", f"${precio_mercado:.2f}" if precio_mercado else "N/A")
    
    with col_hero3:
        fig_score_hero = plot_anillo_puntuacion(nota_final, 100, "Buffett Score (Calidad)", "#00C0F2")
        st.plotly_chart(fig_score_hero, use_container_width=True)
    
    st.markdown("#### 📊 Scorecard Ejecutivo")
    
    # Función auxiliar rápida para el scorecard
    def get_last(df, col):
        if df is not None and col in df.columns:
            s = df[col].dropna()
            return s.iloc[-1] if not s.empty else None
        return None
    
    sc_roe = get_last(res_bs["ratios"], "ROE %")
    sc_roic = get_last(res_bs["ratios"], "ROIC %")
    sc_fcf = get_last(res_cf["ratios"], "Free Cash Flow (B USD)")
    sc_deuda = get_last(res_bs["ratios"], "Deuda / Capital")
    
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("ROE (Rentabilidad)", f"{sc_roe:.1f}%" if sc_roe else "N/A", "Aprobado" if sc_roe and sc_roe > 15 else "Bajo")
    sc2.metric("ROIC (Calidad)", f"{sc_roic:.1f}%" if sc_roic else "N/A", "Aprobado" if sc_roic and sc_roic > 15 else "Bajo")
    sc3.metric("FCF Último Año", f"${sc_fcf:.1f}B" if sc_fcf else "N/A", "Genera Caja" if sc_fcf and sc_fcf > 0 else "Quema Caja")
    sc4.metric("Deuda / Capital", f"{sc_deuda:.2f}x" if sc_deuda else "N/A", "Sano" if sc_deuda and sc_deuda < 0.8 else "Peligro", delta_color="inverse")

    st.markdown("### 📈 Gráfico Interactivo Pro")
    renderizar_grafico_tradingview(ticker_input)

    # ======== VEREDICTO ========
    if res_val and precio_mercado:
        v_justo = res_val.get('graham_value', 0) # Usamos Graham como base rápida
        margen_seguridad = ((precio_mercado - v_justo) / v_justo) * 100 if v_justo > 0 else 0
        estado_precio = "Infravalorada (Descuento)" if margen_seguridad < 0 else "Sobrevalorada (Prima)"
    else:
        estado_precio = "Datos insuficientes"
    
    st.subheader("🧠 Veredicto del Algoritmo")
    
    if nota_final >= 80:
        st.success(f"**Negocio de Clase Mundial:** {ticker_input} obtiene un {nota_final}/100. Muestra un foso económico inquebrantable y alta rentabilidad. Actualmente cotiza en un estado de **{estado_precio}**.")
    elif nota_final >= 50:
        st.warning(f"**Negocio Promedio/Cíclico:** {ticker_input} obtiene un {nota_final}/100. Tiene puntos fuertes pero presenta debilidades estructurales (ej. deuda o márgenes bajos). Estado actual: **{estado_precio}**.")
    else:
        st.error(f"**Riesgo Fundamental Alto:** {ticker_input} obtiene un {nota_final}/100. La máquina detecta posible destrucción de valor. Operar con extrema precaución.")
    
    st.markdown("<br>", unsafe_allow_html=True) # Espacio antes de las pestañas

    # ======== VULNERABILIDADES ========
    st.markdown("### 🔎 Auditoría de Puntos Débiles (Bear Case)")
    
    alertas_detectadas = escanear_vulnerabilidades(res_is, res_bs, res_cf)
    
    if len(alertas_detectadas) == 0:
        st.success("✅ **Foso Económico Intacto:** El escáner no ha detectado vulnerabilidades estructurales graves a nivel contable en el último año.")
    else:
        st.error(f"Se han detectado **{len(alertas_detectadas)} vulnerabilidades críticas** que debes investigar:")
        for alerta in alertas_detectadas:
            st.markdown(f"- {alerta}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
elif seccion_actual == "🔎 Análisis Fundamental":
    # Mueve aquí:
    # 1. Todo lo que tenías en tab1, tab2, tab3 (Dashboard, Ratios, ADN)
    # 2. Modelos de Valoración (Graham, DCF)

    # ======== ANÁLISIS BUFFET ========
    st.markdown("#### ⚖️ Test de Coste de Oportunidad (Buffett)")
    c4, c5, c6 = st.columns(3)
    if earnings_yield and tasa_riesgo:
        spread = (earnings_yield - tasa_riesgo) * 100
        color_spread = "normal" if spread > 0 else "inverse"
        c4.metric("Earnings Yield (Rentabilidad)", f"{earnings_yield*100:.2f}%")
        c5.metric("Tasa Libre de Riesgo (Bono 10Y)", f"{tasa_riesgo*100:.2f}%")
        c6.metric("Prima de Riesgo (Spread)", f"{spread:+.2f} pts", delta_color=color_spread)
        if spread < 0:
            st.error(f"🚨 **Alerta Value:** El Bono del Tesoro ({tasa_riesgo*100:.2f}%) rinde más que los beneficios de esta empresa ({earnings_yield*100:.2f}%). Asumes riesgo para ganar menos que un activo garantizado.")
        else:
            st.success(f"✅ **Favorable:** La empresa ofrece una prima de riesgo positiva frente a la renta fija.")
    st.markdown("---")

    st.markdown("#### 💵 Retorno de Efectivo Real (Caja vs Precio de Mercado)")
    
    acciones = res_val.get('acciones_actuales')
    if precio_actual and acciones and "Free Cash Flow (B USD)" in res_cf["ratios"].columns:
        market_cap = precio_actual * acciones
        
        ultimo_fcf_b = res_cf["ratios"]["Free Cash Flow (B USD)"].dropna().iloc[-1]
        ultimas_recompras_b = res_cf["ratios"]["Recompras (B USD)"].dropna().iloc[-1]
        
        fcf_real = ultimo_fcf_b * 1e9
        recompras_reales = ultimas_recompras_b * 1e9
        
        fcf_yield = (fcf_real / market_cap) * 100
        buyback_yield = (recompras_reales / market_cap) * 100
        
        c7, c8, c9 = st.columns(3)
        
        if market_cap >= 1e12:
            c7.metric("Market Cap (Capitalización)", f"${market_cap / 1e12:.2f} Trillones")
        else:
            c7.metric("Market Cap (Capitalización)", f"${market_cap / 1e9:.2f} Billones")
        
        color_fcf = "normal" if fcf_yield >= 4.0 else "inverse"
        c8.metric("FCF Yield (Rendimiento Efectivo)", f"{fcf_yield:.2f}%", "Óptimo > 4%" if fcf_yield >= 4.0 else "Pobre/Caro", delta_color=color_fcf)
        
        c9.metric("Buyback Yield (Recompras)", f"{buyback_yield:.2f}%", "Destrucción de acciones" if buyback_yield > 0 else "")

        st.write("")
        total_yield = fcf_yield + buyback_yield
        
        if total_yield >= 8.0:
            st.success(f"✅ **Veredicto (Máquina de Efectivo):** Excepcional. La empresa te está devolviendo un **{total_yield:.2f}%** de tu inversión anual de forma 'invisible' (sumando su FCF Yield y las recompras). Está destruyendo acciones a buen ritmo y generando muchísima caja.")
        elif total_yield >= 4.0:
            st.info(f"⚖️ **Veredicto (Sano):** Razonable. Un rendimiento de efectivo total del **{total_yield:.2f}%**, en línea con empresas sólidas y estables. El dinero fluye correctamente hacia el accionista.")
        else:
            st.warning(f"⚠️ **Veredicto (Caja Pobre):** Un rendimiento del **{total_yield:.2f}%** significa que la empresa está muy cara respecto al dinero real que genera, o bien que su negocio requiere reinvertir todo lo que gana (muy intensivo en capital) dejando poco para ti.")
        
    else:
        st.info("No hay datos suficientes de Flujo de Caja para calcular el FCF Yield.")
        
    st.markdown("---")

    st.markdown("#### 🏭 Valoración Relativa (Múltiplos de Mercado)")
    
    with st.spinner("Determinando múltiplo sectorial óptimo..."):
        sector_empresa, metrica_optima, valor_metrica, explicacion, todos_multiplos, umbral = obtener_valoracion_sectorial(ticker_input)
        
        if sector_empresa and sector_empresa != 'Desconocido':
            st.caption(f"**Sector Detectado:** {sector_empresa} | **Métrica Institucional Asignada:** {metrica_optima}")
            st.info(f"💡 **Racionalidad:** {explicacion}")
            
            c_rel1, c_rel2, c_rel3, c_rel4 = st.columns(4)
            
            # Resaltamos la métrica elegida por el algoritmo
            for i, (nombre, valor) in enumerate(todos_multiplos.items()):
                if nombre == metrica_optima:
                    estado = "Barata" if valor > 0 and valor < umbral else "Cara"
                    color_rel = "normal" if estado == "Barata" else "inverse"
                    # Usamos st.metric pero con un fondo destacado o emoji
                    if i == 0: c_rel1.metric(f"🎯 {nombre}", f"{valor:.2f}x", estado, delta_color=color_rel)
                    elif i == 1: c_rel2.metric(f"🎯 {nombre}", f"{valor:.2f}x", estado, delta_color=color_rel)
                    elif i == 2: c_rel3.metric(f"🎯 {nombre}", f"{valor:.2f}x", estado, delta_color=color_rel)
                    elif i == 3: c_rel4.metric(f"🎯 {nombre}", f"{valor:.2f}x", estado, delta_color=color_rel)
                else:
                    # Múltiplos secundarios sin destacar
                    if i == 0: c_rel1.metric(nombre, f"{valor:.2f}x" if valor > 0 else "N/A")
                    elif i == 1: c_rel2.metric(nombre, f"{valor:.2f}x" if valor > 0 else "N/A")
                    elif i == 2: c_rel3.metric(nombre, f"{valor:.2f}x" if valor > 0 else "N/A")
                    elif i == 3: c_rel4.metric(nombre, f"{valor:.2f}x" if valor > 0 else "N/A")
        else:
            st.warning("No se pudo detectar el sector de la empresa para asignar un múltiplo relativo.")
    
    st.markdown("---")

    # --- Fila 4: Análisis DuPont (Calidad del ROE) ---
    st.markdown("#### 🔬 Análisis DuPont: Desmontando el ROE")
    st.caption("Charlie Munger dice: 'Un ROE alto es inútil si se logra a base de deudas'. Aquí vemos de dónde viene realmente el ROE del último año.")
    
    # Función escudo para evitar el IndexError si la columna entera son NaNs
    def get_safe_last_val(df, col):
        if col in df.columns:
            s = df[col].dropna()
            if not s.empty:
                return s.iloc[-1]
        return 0.0

    # Extraemos el último año usando nuestra función escudo
    dupont_margen = get_safe_last_val(res_bs["ratios"], "DuPont: Margen Neto %")
    dupont_rotacion = get_safe_last_val(res_bs["ratios"], "DuPont: Rotación Activos")
    dupont_apalan = get_safe_last_val(res_bs["ratios"], "DuPont: Apalancamiento")
    roe_ultimo = get_safe_last_val(res_bs["ratios"], "ROE %")
    
    c_dp1, c_dp2, c_dp3, c_dp4 = st.columns(4)
    c_dp1.metric("1. Margen Neto (Eficiencia)", f"{dupont_margen:.1f}%")
    c_dp2.metric("2. Rotación Activos (Volumen)", f"{dupont_rotacion:.2f}x")
    
    estado_apalan = "Riesgo si > 3.0x" if dupont_apalan > 3.0 else "Sano"
    color_apalan = "inverse" if dupont_apalan > 3.0 else "normal"
    c_dp3.metric("3. Apalancamiento (Deuda)", f"{dupont_apalan:.2f}x", estado_apalan, delta_color=color_apalan)
    
    c_dp4.metric("= ROE Total", f"{roe_ultimo:.1f}%")

    st.write("")
    if dupont_apalan > 3.0:
        st.error(f"🚨 **Veredicto (Riesgo Oculto):** ¡Cuidado! El ROE parece alto, pero es una ilusión creada por el endeudamiento. La empresa asume un apalancamiento peligroso (**{dupont_apalan:.2f}x**). Si los tipos de interés suben, sus beneficios se hundirán.")
    elif dupont_margen > 15.0:
        st.success(f"✅ **Veredicto (Foso Económico):** El ROE es de máxima calidad. Está impulsado por unos excelentes márgenes de beneficio neto (**{dupont_margen:.1f}%**). La empresa tiene poder de fijación de precios y no depende de deudas masivas.")
    else:
        st.info(f"⚖️ **Veredicto (Modelo de Rotación):** La rentabilidad de la empresa no viene de tener grandes márgenes de beneficio, sino de vender mucho volumen y rotar sus activos rápidamente (**{dupont_rotacion:.2f}x**). Es el clásico modelo de un supermercado como Walmart.")
    
    st.markdown("---")

    # --- Fila 5: Test Piotroski Modificado (Salud Value) ---
    st.markdown("#### 🛡️ Test de Resistencia: Piotroski F-Score (Adaptación Value)")
    st.caption("Sistema de 9 puntos que evalúa la solidez financiera y la tendencia operativa. Un 7-9 indica una empresa blindada. Menos de 4 indica peligro estructural.")

    # Unimos todos los datos para evaluarlos cómodamente
    df_all = pd.concat([res_is["ratios"], res_bs["ratios"], res_cf["ratios"]], axis=1)
    
    # Motor de evaluación de reglas
    def check_cond(col, condition):
        if col not in df_all.columns: return False
        s = df_all[col].dropna()
        if len(s) < 2: return False
        val_act = s.iloc[-1]
        val_prev = s.iloc[-2]
        
        if condition == "pos": return val_act > 0
        if condition == "up": return val_act > val_prev
        if condition == "down": return val_act < val_prev
        if condition == "roic": return val_act >= 15
        return False

    # Las 9 pruebas de fuego de Buffett/Munger
    criterios = [
        (check_cond("Margen Neto %", "pos"), "Beneficios Positivos"),
        (check_cond("Free Cash Flow (B USD)", "pos"), "Genera Caja Real"),
        (check_cond("ROE %", "up"), "ROE Creciente"),
        (check_cond("Margen Bruto %", "up"), "Márgenes Crecientes"),
        (check_cond("DuPont: Rotación Activos", "up"), "Eficiencia al Alza"),
        (check_cond("Deuda / Capital", "down"), "Desapalancamiento"),
        (check_cond("Caja Neta (B USD)", "up"), "Liquidez Creciente"),
        (check_cond("Recompras (B USD)", "pos"), "No Diluye Acciones"),
        (check_cond("ROIC %", "roic"), "ROIC Premium (>15%)")
    ]

    # Calculamos la nota final
    score = sum([1 for p, txt in criterios if p])
    
    # Renderizado visual espectacular
    c_f1, c_f2 = st.columns([1, 3])
    
    with c_f1:
        color_str = "#2ca02c" if score >= 7 else "#ff7f0e" if score >= 4 else "#d62728"
        st.markdown(f"<h1 style='text-align: center; color: {color_str}; font-size: 5rem; margin-bottom: 0;'>{score}/9</h1>", unsafe_allow_html=True)
        if score >= 7: st.success("🟢 Blindaje Total")
        elif score >= 4: st.warning("🟡 Calidad Media")
        else: st.error("🔴 Riesgo Financiero")
        
    with c_f2:
        cols_grid = st.columns(3)
        for i, (passed, text) in enumerate(criterios):
            icono = "✅" if passed else "❌"
            cols_grid[i % 3].markdown(f"**{icono}** {text}")
            
    st.markdown("---")
    
    st.markdown("#### 🏆 Retorno Histórico vs Mercado (S&P 500)")
    fig_tsr = plot_tsr_vs_sp500(ticker_input)
    if fig_tsr:
        st.plotly_chart(fig_tsr, use_container_width=True)
        
        st.caption("💡 *Warren Buffett dice: 'Si no puedes batir al índice, invierte en el índice'. Este gráfico asume una inversión de $10,000 hace 10 años, midiendo si el riesgo de elegir esta acción individual ha sido recompensado frente a comprar el S&P 500.*")
    else:
        st.info("No hay suficientes datos de mercado para generar la comparativa con el S&P 500.")

    # ======== TAB 1 ========
    fig = plot_dashboard_interactivo(
        res_is["ratios"],
        res_bs["ratios"],
        res_cf["ratios"],
        ticker_input
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- FILA DEL EFECTIVO Y CAPITAL ALLOCATION ---
    st.markdown("---")
    col_caja1, col_caja2 = st.columns(2)
    
    with col_caja1:
        st.markdown("#### 💸 Asignación de Capital (10 Años)")
        st.caption("Suma de todos los flujos de caja de la década.")
        fig_waterfall = plot_capital_allocation_waterfall(res_cf["ratios"], ticker_input)
        if fig_waterfall:
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
    with col_caja2:
        st.markdown("#### 👑 Beneficios del Dueño (Owner Earnings)")
        st.caption("Ajuste de Buffett: Separa el CAPEX de mantenimiento del de crecimiento.")
        fig_oe = plot_owner_earnings(res_cf["ratios"], ticker_input)
        if fig_oe:
            st.plotly_chart(fig_oe, use_container_width=True)

    # --- FILA DE GRÁFICOS AVANZADOS ---
    st.markdown("---")
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### 🎁 Retribución al Accionista")
        fig_sy = plot_shareholder_yield_historico(res_cf["ratios"], ticker_input)
        if fig_sy:
            st.plotly_chart(fig_sy, use_container_width=True)
            
    with col_graf2:
        st.markdown("#### 📊 Valoración Real (EV / FCF)")
        st.caption("Compara el precio actual (limpio de deuda y caja) contra su media histórica.")
        if res_val and res_val.get('acciones_actuales'):
            fig_ev = plot_ev_fcf_historico(ticker_input, res_bs["ratios"], res_cf["ratios"], res_val['acciones_actuales'])
            if fig_ev:
                st.plotly_chart(fig_ev, use_container_width=True)
                
                # Extraer el último múltiplo y la mediana para el veredicto
                try:
                    ultimos_fcf = res_cf["ratios"]['Free Cash Flow (B USD)'].dropna()
                    ultimos_caja = res_bs["ratios"]['Caja Neta (B USD)'].dropna()
                    if not ultimos_fcf.empty and not ultimos_caja.empty and ultimos_fcf.iloc[-1] > 0:
                        market_cap_b = (res_val['precio_actual'] * res_val['acciones_actuales']) / 1e9
                        ev_actual = market_cap_b - ultimos_caja.iloc[-1]
                        multiplo_actual = ev_actual / ultimos_fcf.iloc[-1]
                        
                        st.info(f"💡 **Interpretación:** Hoy pagas **{multiplo_actual:.1f}x** su caja libre. Si este número está muy por debajo de la línea punteada naranja (su media histórica), históricamente estás comprando con descuento. Si está muy por encima, Wall Street está pagando una prima exigente.")
                except: pass
        else:
            st.info("No se pudo calcular el EV/FCF por falta de datos de acciones en circulación.")

    st.markdown("#### 🔎 Calidad del Beneficio (Filtro Anti-Fraude)")
    st.caption("Si la barra azul (Beneficio) es sistemáticamente mayor que la verde (Caja), la empresa no está cobrando lo que vende o maquilla sus cuentas.")
    fig_calidad = plot_calidad_beneficios(ticker_input)
    if fig_calidad:
        st.plotly_chart(fig_calidad, use_container_width=True)

    # ======== TAB 2 ========
    st.markdown("### 📝 Calidad Fundamental y ADN Financiero")
    
    # --- CÁLCULO RÁPIDO DE PIOTROSPI PARA EL ANILLO ---
    df_all = pd.concat([res_is["ratios"], res_bs["ratios"], res_cf["ratios"]], axis=1)
    def check_cond_rapido(col, condition):
        if col not in df_all.columns: return False
        s = df_all[col].dropna()
        if len(s) < 2: return False
        if condition == "pos": return s.iloc[-1] > 0
        if condition == "up": return s.iloc[-1] > s.iloc[-2]
        if condition == "down": return s.iloc[-1] < s.iloc[-2]
        if condition == "roic": return s.iloc[-1] >= 15
        return False

    piotroski_score = sum([
        check_cond_rapido("Margen Neto %", "pos"), check_cond_rapido("Free Cash Flow (B USD)", "pos"),
        check_cond_rapido("ROE %", "up"), check_cond_rapido("Margen Bruto %", "up"),
        check_cond_rapido("DuPont: Rotación Activos", "up"), check_cond_rapido("Deuda / Capital", "down"),
        check_cond_rapido("Caja Neta (B USD)", "up"), check_cond_rapido("Recompras (B USD)", "pos"),
        check_cond_rapido("ROIC %", "roic")
    ])

    # --- ANILLOS NEÓN Y RADAR ---
    col_adn1, col_adn2, col_adn3 = st.columns([1, 1, 1.5])
    
    with col_adn1:
        # 🛠️ CORRECCIÓN 1: Ahora usamos 'nota_final'
        fig_buffett = plot_anillo_puntuacion(nota_final, 100, "Buffett Score", "#00C0F2")
        st.plotly_chart(fig_buffett, use_container_width=True)
        
    with col_adn2:
        # 🛠️ CORRECCIÓN 2: Ahora usamos 'piotroski_score'
        fig_piotroski = plot_anillo_puntuacion(piotroski_score, 9, "Piotroski F-Score", "#00ff88")
        st.plotly_chart(fig_piotroski, use_container_width=True)
        
    with col_adn3:
        fig_adn = plot_adn_financiero(ticker_input)
        if fig_adn:
            st.plotly_chart(fig_adn, use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### 📑 Histórico de Ratios y Reglas Inquebrantables")
            
    # 1. Unimos todos los ratios
    df_completo = pd.concat(
        [res_is["ratios"], res_bs["ratios"], res_cf["ratios"]],
        axis=1
    ).T
    
    # 2. Inyectamos los Umbrales de Buffett
    umbrales_buffett = {
        "Margen Bruto %": "> 40% (Ventaja Duradera)", "SG&A % (s/MB)": "< 30% (Fantástico)",
        "I+D % (s/MB)": "< 30% (Foso tecnológico frágil)", "Depreciación % (s/MB)": "< 10% (Poco gasto en maquinaria)",
        "Intereses % (s/OpInc)": "< 15% (Poca deuda)", "Margen Neto %": "> 20% (Monopolio)",
        "ROE %": "> 15% constante", "ROIC %": "> 15% (Verdadera calidad)", 
        "Deuda / Capital": "< 0.80 (Bajo apalancamiento)",
        "CAPEX % sobre Beneficio": "< 50% (Ideal < 25%)", "Crecimiento Gan. Retenidas %": "~ 10% constante"
    }
    df_completo.insert(0, "Criterio Buffett", [umbrales_buffett.get(idx, "-") for idx in df_completo.index])

    # 3. Mostramos la tabla en la web
    # Función para pintar las celdas según reglas Value
    def colorear_matriz(row):
        metric = row.name
        styles = [''] * len(row)
        
        # Reglas: (Operador, Umbral)
        reglas = {
            "Margen Bruto %": ('>', 40), "SG&A % (s/MB)": ('<', 30), "I+D % (s/MB)": ('<', 30),
            "Depreciación % (s/MB)": ('<', 10), "Intereses % (s/OpInc)": ('<', 15),
            "Margen Neto %": ('>', 20), "ROE %": ('>', 15), "ROIC %": ('>', 15),
            "Deuda / Capital": ('<', 0.80), "CAPEX % sobre Beneficio": ('<', 25)
        }
        
        if metric in reglas:
            op, limite = reglas[metric]
            for i, col in enumerate(row.index):
                if col != "Criterio Buffett":
                    try:
                        val = float(row[col])
                        if pd.isna(val): continue
                        if op == '>':
                            styles[i] = 'background-color: rgba(44, 160, 44, 0.2)' if val >= limite else 'background-color: rgba(214, 39, 40, 0.2)'
                        else:
                            styles[i] = 'background-color: rgba(44, 160, 44, 0.2)' if val <= limite else 'background-color: rgba(214, 39, 40, 0.2)'
                    except: pass
        return styles

    st.dataframe(df_completo.style.apply(colorear_matriz, axis=1).format(precision=2), use_container_width=True, height=500)
    
    st.markdown("---")
    
    # Convertimos el DataFrame a CSV usando codificación utf-8 para no perder acentos
    csv_data = df_completo.to_csv(index_label="Métrica").encode('utf-8-sig')
    
    st.download_button(
        label="📥 Descargar Reporte (CSV/Excel)",
        data=csv_data,
        file_name=f"{ticker_input}_Reporte_Buffett.csv",
        mime="text/csv",
        type="primary"
    )

    # ======== TAB 3 ========
    if ticker_competidor:
        with st.spinner(f"Descargando informes de la SEC para el competidor {ticker_competidor}..."):
            is_df2, bs_df2, cf_df2 = cargar_datos(ticker_competidor, 10)
            
            if is_df2 is not None:
                # Analizamos al competidor completo
                res_is2 = analizar_cuenta_resultados(is_df2, cf_df2)
                res_bs2 = analizar_balance(bs_df2, is_df2)
                res_cf2 = analizar_flujo_efectivo(cf_df2, is_df2)
                res_val2 = valorar_empresa(is_df2, bs_df2, cf_df2, ticker_competidor)
                
                if res_is2 and res_bs2 and res_cf2:
                    # 1. MARCADOR HEAD-TO-HEAD
                    st.markdown(f"### 🥊 {ticker_input} vs {ticker_competidor}")
                    
                    st.markdown("#### 🗺️ Mapa de Mercado Relativo")
                    fig_treemap = plot_treemap_competidores(ticker_input, ticker_competidor)
                    if fig_treemap:
                        st.plotly_chart(fig_treemap, use_container_width=True)
                    st.markdown("---")
                    
                    nota1 = calcular_score_buffett(res_is["ratios"], res_bs["ratios"], res_cf["ratios"])
                    nota2 = calcular_score_buffett(res_is2["ratios"], res_bs2["ratios"], res_cf2["ratios"])
                    
                    c_h1, c_h2, c_h3, c_h4 = st.columns(4)
                    
                    # Empresa 1
                    c_h1.metric(f"Score Value ({ticker_input})", f"{nota1}/100", "Ganador" if nota1 >= nota2 else "Perdedor", delta_color="normal" if nota1 >= nota2 else "inverse")
                    if res_val:
                        c_h2.metric(f"PER Actual ({ticker_input})", f"{res_val['precio_actual'] / res_val['eps_actual']:.1f}x" if res_val['precio_actual'] else "N/A")
                        
                    # Empresa 2
                    c_h3.metric(f"Score Value ({ticker_competidor})", f"{nota2}/100", "Ganador" if nota2 > nota1 else "Perdedor", delta_color="normal" if nota2 > nota1 else "inverse")
                    if res_val2:
                        c_h4.metric(f"PER Actual ({ticker_competidor})", f"{res_val2['precio_actual'] / res_val2['eps_actual']:.1f}x" if res_val2['precio_actual'] else "N/A")

                    st.markdown("---")
                    
                    # 2. GRÁFICOS COMPARATIVOS
                    col_comp1, col_comp2 = st.columns(2)
                    
                    with col_comp1:
                        fig_radar = plot_radar_comparativo(
                            ticker_input, res_is["ratios"], res_bs["ratios"],
                            ticker_competidor, res_is2["ratios"], res_bs2["ratios"]
                        )
                        if fig_radar:
                            st.plotly_chart(fig_radar, use_container_width=True)
                            st.info("💡 **Foso Actual:** El radar muestra quién tiene los fundamentales más fuertes en el último año reportado.")
                            
                    with col_comp2:
                        # Comparativa histórica de ROIC (El foso económico en el tiempo)
                        fig_hist = plot_comparativa_historica(
                            ticker_input, res_bs["ratios"], 
                            ticker_competidor, res_bs2["ratios"], 
                            "ROIC %"
                        )
                        if fig_hist:
                            st.plotly_chart(fig_hist, use_container_width=True)
                        
                        # Comparativa histórica de Márgenes
                        fig_hist2 = plot_comparativa_historica(
                            ticker_input, res_is["ratios"], 
                            ticker_competidor, res_is2["ratios"], 
                            "Margen Neto %"
                        )
                        if fig_hist2:
                            st.plotly_chart(fig_hist2, use_container_width=True)
                            
                        st.caption("📈 **Consistencia:** Buffett prefiere una empresa con un 15% estable durante 10 años, que una con picos del 30% y caídas al 5%.")

            else:
                st.error(f"No se pudieron descargar los datos del competidor {ticker_competidor}. Comprueba el ticker.")
    else:
        st.info("🥊 **El Ring está vacío.** Introduce un ticker rival en el panel lateral (Ej: 'MSFT', 'PEP', 'AMD') para activar la batalla de calidad empresarial.")

    # ======== MODELOS DE VALORACIÓN ========
    st.subheader(f"⚖️ Triangulación de Valor Intrínseco — {ticker_input}")

    if res_val:
        precio_actual = res_val.get('precio_actual')
        eps_actual = res_val.get('eps_actual', 0)
    
        earnings_yield = res_val.get('earnings_yield', 0)
        tasa_riesgo = res_val.get('tasa_libre_riesgo', 0)
        
        # Extracción de Modelos
        v_graham = res_val.get('graham_value', 0)
        v_lynch = res_val.get('lynch_value', 0)
        v_epv = res_val.get('epv_value', 0)
        
        # --- SECCIÓN 1: MODELOS MATEMÁTICOS ESTÁTICOS ---
        st.markdown("#### 🏛️ Modelos Institucionales (Suelo y Techo)")
        st.caption("Diferentes metodologías de inversión aplicadas a los beneficios actuales de la empresa.")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # 1. Graham
        # Blindaje contra fallos de red en la nube (NoneType)
        if isinstance(precio_actual, (int, float)) and isinstance(v_graham, (int, float)) and v_graham > 0:
            margen_graham = ((precio_actual - v_graham) / v_graham) * 100
        else:
            margen_graham = 0
        color_g = "inverse" if margen_graham > 0 else "normal"
        estado_g = "Cara" if margen_graham > 0 else "Barata"
        col_m1.metric("Benjamin Graham (Value)", f"${v_graham:.2f}", f"{estado_g} ({margen_graham:+.1f}%)", delta_color=color_g)
        col_m1.caption("Combina beneficios y crecimiento ajustado a los bonos del tesoro actuales.")
        
        # 2. Peter Lynch
        margen_lynch = ((precio_actual - v_lynch) / v_lynch) * 100 if v_lynch > 0 else 0
        color_l = "inverse" if margen_lynch > 0 else "normal"
        estado_l = "Cara" if margen_lynch > 0 else "Barata"
        col_m2.metric("Peter Lynch (Crecimiento)", f"${v_lynch:.2f}", f"{estado_l} ({margen_lynch:+.1f}%)", delta_color=color_l)
        col_m2.caption("Asume que el PER justo de una empresa debería ser igual a su crecimiento (PEG=1).")
        
        # 3. EPV
        margen_epv = ((precio_actual - v_epv) / v_epv) * 100 if v_epv > 0 else 0
        col_m3.metric("EPV (Cero Crecimiento)", f"${v_epv:.2f}")
        col_m3.caption(f"Valor 'suelo'. Lo que vale la empresa si sus beneficios se estancan y no vuelve a crecer nunca más.")

    st.markdown("#### 🎛️ Tu Modelo DCF (Flujos de Caja Descontados)")
    st.caption("Crea tu propio escenario. Los valores por defecto han sido calculados por nuestro algoritmo.")
    
    col_slider1, col_slider2, col_slider3 = st.columns(3)
    
    with col_slider1:
        g_sugerido = res_val.get('crecimiento_sostenible', 0.05) * 100
        cagr_usr = st.slider("Crecimiento Anual Estimado %", min_value=1.0, max_value=25.0, value=float(g_sugerido), step=0.5)
        
    with col_slider2:
        wacc_sugerido = res_val.get('tasa_descuento_capm', 0.10) * 100
        tasa_desc_usr = st.slider("Tasa de Descuento (CAPM) %", min_value=5.0, max_value=20.0, value=float(wacc_sugerido), step=0.5)
        
    with col_slider3:
        margen_seguridad_usr = st.slider("Margen de Seguridad %", min_value=0, max_value=50, value=25, step=5)

    # Cálculo de tu DCF Personalizado
    per_asumido = res_val.get('per_asumido', 15)
    eps_futuro = eps_actual * ((1 + (cagr_usr / 100)) ** 10)
    precio_futuro = eps_futuro * per_asumido
    v_dcf = precio_futuro / ((1 + (tasa_desc_usr / 100)) ** 10)
    precio_compra = v_dcf * (1 - (margen_seguridad_usr / 100))

    c1, c2, c3 = st.columns(3)

    if precio_actual:
        descuento_dcf = ((precio_actual - v_dcf) / v_dcf) * 100
        estado_valor = "Sobrevalorada" if descuento_dcf > 0 else "Infravalorada"
        color_valor = "inverse" if descuento_dcf > 0 else "normal"
        c1.metric("Precio de Mercado Hoy", f"${precio_actual:.2f}", f"{estado_valor} ({descuento_dcf:+.1f}%)", delta_color=color_valor)
    else:
        c1.metric("Precio de Mercado", "No disp.")
        
    c2.metric("Valor Justo (Tu DCF)", f"${v_dcf:.2f}")
    c3.metric(f"Precio Seguro (-{margen_seguridad_usr}%)", f"${precio_compra:.2f}")

    st.markdown("#### 🧠 Reverse DCF: ¿Qué crecimiento asume el mercado hoy?")
    st.caption("En lugar de adivinar el futuro, calculamos qué crecimiento anual (CAGR) exige el precio actual de la acción para justificar su cotización en bolsa.")

    if precio_actual and eps_actual > 0:
        try:
            r = tasa_desc_usr / 100
            base = (precio_actual * ((1 + r) ** 10)) / (eps_actual * per_asumido)
            if base > 0:
                implied_g = (base ** 0.1) - 1
                implied_g_pct = implied_g * 100
                
                c_rev1, c_rev2 = st.columns([1, 2])
                
                color_delta = "inverse" if implied_g_pct > cagr_usr else "normal"
                c_rev1.metric(
                    "Crecimiento Implícito (Priced In)", 
                    f"{implied_g_pct:.2f}%", 
                    f"vs {cagr_usr:.2f}% (Tu estimación)", 
                    delta_color=color_delta
                )
                
                if implied_g_pct > cagr_usr:
                    c_rev2.error(f"⚠️ **Sobrevaloración probable:** El mercado ya está asumiendo que la empresa crecerá al **{implied_g_pct:.2f}%** anual durante 10 años. Si tú crees que solo crecerá al **{cagr_usr:.2f}%**, la acción está cara hoy.")
                else:
                    c_rev2.success(f"✅ **Margen de seguridad:** El mercado es pesimista y solo le exige crecer al **{implied_g_pct:.2f}%**. Como tú estimas un crecimiento del **{cagr_usr:.2f}%**, estás comprando barato.")
            else:
                st.info("Matemáticamente imposible calcular el Reverse DCF (Base negativa).")
        except Exception as e:
            st.error(f"Error en el cálculo del Reverse DCF: {e}")
    else:
        st.info("Se necesita un Precio de Mercado actual y un EPS positivo para realizar la ingeniería inversa.")

    # ====== Matriz de Sensibilidad DCF (Heatmap) =======
    st.markdown("#### 🗺️ Matriz de Sensibilidad (Precio Seguro)")
    st.caption("Esta matriz muestra a qué precio deberías comprar la acción dependiendo de si el crecimiento futuro (Eje Y) y la rentabilidad exigida (Eje X) cambian. Las celdas verdes son precios más seguros.")
    
    # Generar variaciones de +/- 2% alrededor de lo que el usuario ha puesto en los sliders
    tasas_desc = [tasa_desc_usr - 2, tasa_desc_usr - 1, tasa_desc_usr, tasa_desc_usr + 1, tasa_desc_usr + 2]
    crecimientos = [cagr_usr - 2, cagr_usr - 1, cagr_usr, cagr_usr + 1, cagr_usr + 2]

    matriz_precios = []
    for g in crecimientos:
        fila = []
        for d in tasas_desc:
            eps_f = eps_actual * ((1 + (g / 100)) ** 10)
            p_f = eps_f * per_asumido
            v_i = p_f / ((1 + (d / 100)) ** 10)
            p_c = v_i * (1 - (margen_seguridad_usr / 100))
            fila.append(p_c)
        matriz_precios.append(fila)

    fig_hm = go.Figure(data=go.Heatmap(
        z=matriz_precios,
        x=[f"{d}%" for d in tasas_desc],
        y=[f"{g}%" for g in crecimientos],
        colorscale='RdYlGn', # Rojo (Peligro) a Verde (Seguro)
        text=[[f"${val:.2f}" for val in fila] for fila in matriz_precios],
        texttemplate="%{text}",
        hoverinfo="skip"
    ))
    fig_hm.update_layout(
        xaxis_title="Tasa de Descuento (Retorno Exigido)",
        yaxis_title="Crecimiento Anual Estimado (CAGR)",
        height=350,
        margin=dict(l=40, r=40, t=20, b=40)
    )
    st.plotly_chart(fig_hm, use_container_width=True)
    st.markdown("---")

    st.markdown("#### Football Field Chart")
    fig_ff = plot_football_field(ticker_input, precio_actual, res_val)

    if fig_ff:
        st.plotly_chart(fig_ff, use_container_width=True)
    else:
        st.info("No se pudo generar el gráfico Football Field...")
    st.markdown("---")

    # ======== TAB 8 ========
    st.markdown("### 💸 Estrategia de Dividendos Crecientes (DGI)")
    st.caption("No mires el dividendo actual, mira el futuro. El *Yield on Cost* (Rentabilidad sobre Coste) te dice cuánto dinero te pagará la empresa anualmente respecto a lo que pagaste por ella el día que la compraste.")
    
    if precio_actual:
        with st.spinner("Calculando histórico y proyecciones de dividendos..."):
            fig_dgi, texto_dgi = plot_proyeccion_dividendos(ticker_input, precio_actual)
            
            if fig_dgi:
                st.plotly_chart(fig_dgi, use_container_width=True)
                st.success(texto_dgi)
            else:
                st.info(texto_dgi) # Muestra el mensaje de error si la empresa no paga dividendo
    else:
        st.warning("Se necesita un precio de mercado actual para calcular el Yield on Cost.")

elif seccion_actual == "📈 Técnico y Opciones":
    # Mueve aquí:
    # 1. Tu terminal de TradingView (Pestaña 5)
    # 2. El gráfico de Opciones (Miedo/Codicia)
    # 3. La Pestaña 4 (Insiders y Piel en el juego)

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
    
elif seccion_actual == "🌍 Radar Macro y Sectores":
    # Mueve aquí:
    # 1. Tu nuevo Radar de Rotación Sectorial
    # 2. La Pestaña 9 (Estacionalidad Cuantitativa)

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

elif seccion_actual == "🧠 Auditoría Forense":
    ejecutar_auditoria_forense(ticker_input)

elif seccion_actual == "🤖 Robo-Advisor & Test Perfil":
    ejecutar_roboadvisor()

elif seccion_actual == "🔮 Proyección IA y Catalizadores":
    ejecutar_proyeccion(ticker_input)
                
elif seccion_actual == "⏳ Máquina del Tiempo (Backtest)":
    ejecutar_maquina_del_tiempo(ticker_input)

elif seccion_actual == "🚀 Radar Multibaggers (Small/Mid Caps)":
    ejecutar_radar_multibagger(ticker_input)
            
# ==========================================
# 🤖 CHATBOT QUANTITATIVO (COPILOTO IA)
# ==========================================
# Lo ponemos al final del código para asegurarnos de que TODAS las variables matemáticas ya existen
with st.sidebar:
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #00ff88;'>🤖 Analista Quant AI</h3>", unsafe_allow_html=True)
    st.caption("Habla con el algoritmo sobre los fundamentales de la empresa.")

    if "mensajes_chat" not in st.session_state:
        st.session_state.mensajes_chat = [
            {"role": "assistant", "content": "Hola, soy tu analista quant. ¿Qué quieres saber sobre esta empresa?"}
        ]

    chat_container = st.container(height=400)
    with chat_container:
        for msg in st.session_state.mensajes_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt_usuario := st.chat_input("Ej: ¿Cuál es el mayor riesgo de esta empresa?"):
        st.session_state.mensajes_chat.append({"role": "user", "content": prompt_usuario})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt_usuario)
        
        try:
            # Ahora estas variables SIEMPRE existirán porque se calcularon más arriba
            p_actual = res_val.get('precio_actual', 'Desconocido') if 'res_val' in locals() and res_val else 'Desconocido'
            nota = nota_final if 'nota_final' in locals() else 'Desconocida'
            fcf_actual = sc_fcf if 'sc_fcf' in locals() else 'Desconocido'
            
            # 1. Recuperamos el contexto de Rotación Sectorial
            contexto_macro = ""
            if 'df_sectores' in locals() and df_sectores is not None and not df_sectores.empty:
                mejor_sec = df_sectores.loc[df_sectores['1 Mes (%)'].idxmax()]['Sector']
                peor_sec = df_sectores.loc[df_sectores['1 Mes (%)'].idxmin()]['Sector']
                contexto_macro = f"- Flujo de Capital (Macro): En los últimos 30 días, los grandes fondos están comprando masivamente {mejor_sec} y abandonando {peor_sec}."

            # 2. Preparamos el informe forense (Abogado del Diablo)
            if 'alertas_detectadas' in locals() and len(alertas_detectadas) > 0:
                texto_alertas = "\n".join(alertas_detectadas)
                modo_abogado_diablo = f"\n⚠️ BANDERAS ROJAS DETECTADAS:\n{texto_alertas}\n\nINSTRUCCIÓN CRÍTICA: Eres un inversor bajista (Short Seller). Destruye la tesis de inversión usando estas banderas rojas y advierte al usuario si el sector macro no acompaña."
            else:
                modo_abogado_diablo = "\n✅ BANDERAS ROJAS: Ninguna grave detectada. Balance limpio. Puedes ser más optimista, pero evalúa siempre el contexto macro."

            # 3. Ensamblamos la mente de la IA
            contexto_oculto = f"""
            Eres un gestor de fondos cuantitativo senior. 
            Analizas la empresa {ticker_input} basándote ESTRICTAMENTE en estos datos de tu Terminal:
            - Buffett Score (Calidad): {nota}/100
            - Precio actual: ${p_actual}
            - Free Cash Flow: {fcf_actual} Billones.
            {contexto_macro}
            
            {modo_abogado_diablo}
            
            Responde de forma implacable, profesional y muy directa. Si el sector de la empresa está entre los perdedores, menciónalo como un viento en contra.
            Pregunta del usuario: {prompt_usuario}
            """
            
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("Pensando como un analista de Wall Street..."):
                        if nota == 'Desconocida':
                            respuesta_ia = "⚠️ Por favor, introduce un Ticker y pulsa 'Analizar Terminal' primero para que pueda descargar los estados financieros y darte una opinión informada."
                            st.markdown(respuesta_ia)
                        else:
                            modelo_disponible = None
                            for m in genai.list_models():
                                if 'generateContent' in m.supported_generation_methods:
                                    modelo_disponible = m.name
                                    # Priorizamos la versión flash si está disponible por ser más rápida
                                    if "flash" in m.name.lower(): 
                                        break 
                            
                            if not modelo_disponible:
                                st.error("Tu API Key no tiene permisos para generar texto.")
                            else:
                                # 2. Cargamos el modelo exacto que Google nos ha devuelto
                                model = genai.GenerativeModel(modelo_disponible)
                                prompt_final = f"{contexto_oculto}\n\nResponde directamente y sin rodeos."
                                
                                response = model.generate_content(prompt_final)
                                respuesta_ia = response.text
                                st.markdown(respuesta_ia)
                            
            st.session_state.mensajes_chat.append({"role": "assistant", "content": respuesta_ia})
            
        except Exception as e:
            st.error(f"Error procesando la IA: {e}")

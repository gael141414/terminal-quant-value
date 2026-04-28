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
from modulos.insiders import ejecutar_rastreador_insiders
from modulos.screener import ejecutar_escaner_global
from modulos.etf import ejecutar_radiografia_etf
from modulos.resumen import ejecutar_resumen_ejecutivo
from modulos.fundamental import ejecutar_analisis_fundamental
from modulos.tecnico import ejecutar_tecnico_y_opciones
from modulos.macro import ejecutar_radar_macro
from modulos.reloj_macro import ejecutar_reloj_macro
from modulos.liquidez import ejecutar_monitor_liquidez
from modulos.cisnes_negros import ejecutar_simulador_crisis
from modulos.coberturas import ejecutar_radar_coberturas
from modulos.chatbot import render_chatbot
from modulos.consejos import ejecutar_apartado_consejos
from modulos.predictor import ejecutar_predictor_techos_suelos
from modulos.minero_smallcaps import ejecutar_visor_smallcaps

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

import requests

@st.cache_data(ttl=3600, show_spinner=False)
def buscar_etf_yahoo(query):
    """Consulta la API oculta de Yahoo Finance para autocompletar nombres de fondos."""
    if not query or len(query) < 2:
        return []
    
    # Endpoint interno de búsqueda de Yahoo
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=15&newsCount=0"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        datos = res.json()
        resultados = []
        
        for quote in datos.get('quotes', []):
            # Filtramos estrictamente para que solo salgan ETFs y Fondos
            if quote.get('quoteType') in ['ETF', 'MUTUALFUND']:
                simbolo = quote.get('symbol')
                nombre = quote.get('shortname', quote.get('longname', 'Desconocido'))
                resultados.append(f"{simbolo} ➔ {nombre}")
                
        return resultados
    except Exception:
        return []

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

# ---------------------------------------------------------
# 1. SIDEBAR (CONTROL CENTRAL Y NAVEGACIÓN)
# ---------------------------------------------------------
with st.sidebar:
    # --- ANIMACIÓN LOTTIE ---
    lottie_url = "https://assets3.lottiefiles.com/packages/lf20_fi0ty9ak.json" 
    lottie_trading = load_lottieurl(lottie_url)
    if lottie_trading:
        st_lottie(lottie_trading, height=180, key="trading_anim")

    # --- EL MENÚ VA PRIMERO (Siempre visible) ---
    st.markdown("<h3 style='text-align: center; color: #E0E6ED;'>🧭 Navegación Quant</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    seccion_actual = st.radio("Ir a:", [
        "📊 Resumen Ejecutivo",
        "🔎 Análisis Fundamental",
        "📈 Técnico y Opciones",
        "🌍 Radar Macro y Sectores",
        "🕰️ Reloj Económico (Regímenes)",
        "🚰 Monitor de Liquidez (FED)",
        "🦢 Test Cisnes Negros (Crisis)",
        "🛡️ Radar de Coberturas (Hedging)",
        "🧠 Auditoría Forense",
        "💡 Consejos y Mentoría",
        "⛏️ Minero de Small Caps",
        "🔭 Predictor de Techos/Suelos",
        "🔮 Proyección IA y Catalizadores",
        "⏳ Máquina del Tiempo (Backtest)",
        "🚀 Radar Multibaggers (Small/Mid Caps)",
        "🕵️‍♂️ Rastreador de Insiders (SEC)",
        "🩻 Radiografía de ETFs (X-Ray)",
        "🌐 Escáner Global (Screener)",
        "🤖 Robo-Advisor & Test Perfil",
        "🤖 Chatbot Inversor"
    ], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("<h4 style='color: #8c9bba;'>⚙️ Configuración</h4>", unsafe_allow_html=True)

    # Inicializamos variables para evitar errores si no se usan
    ticker_input = "AAPL"
    etf_input = "SPY"
    ticker_competidor = ""
    años_hist = 10
    analizar_btn = False # Control para las herramientas de empresa

    # --- LÓGICA CONTEXTUAL (La barra se adapta a la herramienta elegida) ---

    # CASO 1: RADIOGRAFÍA DE ETFs
    if seccion_actual == "🩻 Radiografía de ETFs (X-Ray)":
        st.info("🏦 Modo: Análisis de Fondos")
        busqueda_etf = st.text_input("Buscar ETF (Ej: Vanguard, SPY):", value="", placeholder="Escribe para buscar...")
        
        if busqueda_etf:
            try:
                resultados_busqueda = buscar_etf_yahoo(busqueda_etf)
                if resultados_busqueda:
                    seleccion = st.selectbox("Selecciona el fondo correcto:", resultados_busqueda)
                    etf_input = seleccion.split(" ➔ ")[0].strip()
                else:
                    st.warning("Buscando por Ticker exacto...")
                    etf_input = busqueda_etf.upper()
            except Exception:
                etf_input = busqueda_etf.upper()

    # CASO 2: HERRAMIENTAS INDEPENDIENTES (El input está en el centro de la pantalla)
    elif seccion_actual in ["🤖 Robo-Advisor & Test Perfil", "🌐 Escáner Global (Screener)", "🤖 Chatbot Inversor"]:
        st.success("👉 Dirígete a la parte central de la pantalla para utilizar esta herramienta.")

    # CASO 3: ANÁLISIS DE EMPRESAS (Tu buscador original)
    else:
        st.info("🏢 Modo: Análisis de Acciones")
        
        # 1. Cargamos la base de datos
        try:
            lista_tickers_sec = obtener_tickers_filtrados()
        except:
            lista_tickers_sec = ["AAPL - Apple", "MSFT - Microsoft"]
            
        indice_aapl = next((i for i, item in enumerate(lista_tickers_sec) if item.startswith("AAPL -")), 0)
        
        # 2. Buscadores
        seleccion_principal = st.selectbox("🎯 Buscar Empresa", options=lista_tickers_sec, index=indice_aapl)
        ticker_input = seleccion_principal.split(" - ")[0]

        lista_competidores = [""] + lista_tickers_sec
        seleccion_competidor = st.selectbox("🥊 Comparador (Opcional)", options=lista_competidores, index=0)
        ticker_competidor = seleccion_competidor.split(" - ")[0] if seleccion_competidor else ""
        
        años_hist = st.slider("Años históricos", 5, 20, 10)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Reintroducimos el botón de Análisis SOLO para las herramientas de empresa
        analizar_btn = st.button("🚀 ANALIZAR EMPRESA", use_container_width=True, type="primary")

# ---------------------------------------------------------
# 2. ENRUTADOR PRINCIPAL (Gestión de la pantalla central)
# ---------------------------------------------------------

herramientas_independientes = [
    "🤖 Robo-Advisor & Test Perfil", 
    "🌐 Escáner Global (Screener)", 
    "🩻 Radiografía de ETFs (X-Ray)",
    "🕰️ Reloj Económico (Regímenes)",
    "🚰 Monitor de Liquidez (FED)",
    "🤖 Chatbot Inversor",
    "💡 Consejos y Mentoría",
    "⛏️ Minero de Small Caps"
]

# CASOS INDEPENDIENTES (No necesitan darle al botón del sidebar)
if seccion_actual in herramientas_independientes:
    # ---------------------------------------------------------
    # RUTA A: HERRAMIENTAS QUE NO NECESITAN BOTÓN DE "ANALIZAR"
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)

    if seccion_actual == "🕰️ Reloj Económico (Regímenes)":
        ejecutar_reloj_macro()
        
    elif seccion_actual == "🤖 Robo-Advisor & Test Perfil":
        ejecutar_roboadvisor()

    elif seccion_actual == "🌐 Escáner Global (Screener)":
        ejecutar_escaner_global()

    elif seccion_actual == "🩻 Radiografía de ETFs (X-Ray)":
        ejecutar_radiografia_etf(etf_input)

    elif seccion_actual == "🚰 Monitor de Liquidez (FED)":
        ejecutar_monitor_liquidez()

    elif seccion_actual == "🤖 Chatbot Inversor":
        render_chatbot()

    elif seccion_actual == "💡 Consejos y Mentoría":
        ejecutar_apartado_consejos()

    elif seccion_actual == "⛏️ Minero de Small Caps":
        ejecutar_visor_smallcaps()

# CASOS DE EMPRESA (Requieren pulsar el botón del sidebar la primera vez)
else:
    # ---------------------------------------------------------
    # RUTA B: HERRAMIENTAS DE EMPRESA (Requieren pulsar el botón)
    # ---------------------------------------------------------
    
    # 1. Escuchamos al botón de la barra lateral
    if analizar_btn:
        st.session_state['empresa_analizada'] = True

    # 2. Si AÚN NO han pulsado el botón -> Mostramos la Landing Page
    if not st.session_state.get('empresa_analizada', False):
        st.markdown("<br><br>", unsafe_allow_html=True)
        col_hero_texto, col_hero_anim = st.columns([1.2, 1])
        
        with col_hero_texto:
            st.markdown("<h1 style='font-size: 4.5rem; color: #E0E6ED;'>🦅 Value<span style='color: #00C0F2;'>Quant</span></h1>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 1.2rem; color: #8c9bba;'>La terminal institucional para el inversor inteligente.<br>Inteligencia Artificial, Análisis Forense y Cuantitativo en un solo lugar.</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #00C0F2;'>👈 Selecciona una empresa en el panel lateral y pulsa 'Analizar' para comenzar</h4>", unsafe_allow_html=True)
            
        with col_hero_anim:
            lottie_landing = load_lottieurl("https://assets1.lottiefiles.com/packages/lf20_1w3l1m2h.json") 
            if lottie_landing:
                st_lottie(lottie_landing, height=250, key="landing_anim")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("📊 **Datos Institucionales**\n\nConéctate en tiempo real a la SEC.")
        with col2:
            st.success("🧠 **Inteligencia Artificial**\n\nCopiloto integrado que audita balances.")
        with col3:
            st.warning("⚠️ **Auditoría Forense**\n\nDetecta quema de caja y deuda tóxica.")
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        render_ticker_tape()
        st.stop() # 🛑 AHORA SÍ es seguro detener la app aquí, porque sabemos que están en el "Modo Empresa"

    # 3. Si YA han pulsado el botón -> Cargamos los datos y mostramos la herramienta
    render_ticker_tape()

    with st.spinner(f"Sincronizando con Wall Street... Descargando {años_hist} años de datos para {ticker_input}"):
        is_df, bs_df, cf_df = cargar_datos(ticker_input, años_hist)

    if is_df is None:
        st.error("🚨 Fallo de conexión con la SEC/Yahoo Finance. Verifica el Ticker.")
        st.stop()

    # Procesamiento matemático de fondo (Para el Chatbot y otras funciones futuras)
    res_is = analizar_cuenta_resultados(is_df, cf_df)
    res_bs = analizar_balance(bs_df, is_df)
    res_cf = analizar_flujo_efectivo(cf_df, is_df)
    res_val = valorar_empresa(is_df, bs_df, cf_df, ticker_input)
    nota_final = calcular_score_buffett(res_is["ratios"], res_bs["ratios"], res_cf["ratios"])
    
    # Invocamos la herramienta correspondiente
    if seccion_actual == "📊 Resumen Ejecutivo":
        ejecutar_resumen_ejecutivo(ticker_input, is_df, bs_df, cf_df, res_is, res_bs, res_cf, res_val, nota_final)
        
    elif seccion_actual == "🔎 Análisis Fundamental":
        ejecutar_analisis_fundamental(ticker_input, is_df, bs_df, cf_df, res_is, res_bs, res_cf, res_val, nota_final, ticker_competidor)    
    
    elif seccion_actual == "📈 Técnico y Opciones":
        ejecutar_tecnico_y_opciones(ticker_input)

    elif seccion_actual == "🌍 Radar Macro y Sectores":
        df_sectores = analizar_rotacion_sectores()
        ejecutar_radar_macro(ticker_input, ticker_competidor, df_sectores)
        
    elif seccion_actual == "🧠 Auditoría Forense":
        ejecutar_auditoria_forense(ticker_input, is_df, bs_df, cf_df, res_val, res_bs)

    elif seccion_actual == "🔭 Predictor de Techos/Suelos":
        ejecutar_predictor_techos_suelos(ticker_input)

    elif seccion_actual == "🔮 Proyección IA y Catalizadores":
        ejecutar_proyeccion(ticker_input)

    elif seccion_actual == "⏳ Máquina del Tiempo (Backtest)":
        ejecutar_maquina_del_tiempo(ticker_input)
        
    elif seccion_actual == "🚀 Radar Multibaggers (Small/Mid Caps)":
        ejecutar_radar_multibagger(ticker_input)
        
    elif seccion_actual == "🕵️‍♂️ Rastreador de Insiders (SEC)":
        ejecutar_rastreador_insiders(ticker_input)

    elif seccion_actual == "🦢 Test Cisnes Negros (Crisis)":
        ejecutar_simulador_crisis(ticker_input)

    elif seccion_actual == "🛡️ Radar de Coberturas (Hedging)":
        ejecutar_radar_coberturas(ticker_input)
                           
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

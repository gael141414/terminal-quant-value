import pandas as pd
import numpy as np
import yfinance as yf
from income_analyzer import extraer_dato_robusto # ¡Importamos el motor blindado de la Fase 1!

def valorar_empresa(is_df, bs_df, cf_df, ticker_symbol=None):
    if is_df is None or bs_df is None: return None

    def obtener_años(df):
        cols = sorted([c for c in df.columns if str(c).isdigit() and len(str(c)) == 4])
        return df, cols

    is_df, años_is = obtener_años(is_df)
    bs_df, años_bs = obtener_años(bs_df)
    años_comunes = sorted(list(set(años_is) & set(años_bs)))

    if not años_comunes: return None

    # 1. EXTRACCIÓN CON EL MOTOR DE LA FASE 1
    net_income = extraer_dato_robusto(is_df, ['NetIncomeLoss', 'ProfitLoss', 'Net income', 'Net earnings'], años_comunes)
    equity = extraer_dato_robusto(bs_df, ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'Total Equity', "Total stockholders' equity"], años_comunes)
    
    # Búsqueda ampliada de acciones en circulación
    terminos_acciones = ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic", "EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding", "diluted shares", "basic shares"]
    shares_fila = extraer_dato_robusto(is_df, terminos_acciones, años_comunes)
    
    if shares_fila.isna().all(): # Si no está en resultados, buscamos en balance
        shares_fila = extraer_dato_robusto(bs_df, terminos_acciones, años_comunes)

    if net_income.isna().all(): return None

    # 2. FALLBACK A YFINANCE SI LA SEC NO REPORTA LAS ACCIONES CLARAMENTE
    acciones_actuales = shares_fila.dropna().iloc[-1] if not shares_fila.isna().all() else None
    
    if pd.isna(acciones_actuales) or acciones_actuales == 0:
        try:
            ticker_yf = yf.Ticker(ticker_symbol)
            acciones_actuales = ticker_yf.info.get('sharesOutstanding', ticker_yf.info.get('impliedSharesOutstanding', None))
        except:
            pass
            
    if not acciones_actuales: return None # Sin acciones no hay EPS posible

    # 3. CÁLCULO DE SERIE EPS Y CAGR HISTÓRICO
    if shares_fila.isna().all():
        eps_serie = (net_income / acciones_actuales).dropna()
    else:
        eps_serie = (net_income / shares_fila).dropna()

    if len(eps_serie) < 2: return None

    año_ini, año_fin = int(eps_serie.index[0]), int(eps_serie.index[-1])
    n_años = len(eps_serie) - 1
    
    eps_inicial = eps_serie.iloc[0]
    eps_final = eps_serie.iloc[-1]
    
    # Blindaje contra crecimientos matemáticamente imposibles por años de pérdidas
    if eps_inicial <= 0 or eps_final <= 0:
        cagr_historico = 0.05 
    else:
        cagr_historico = ((eps_final / eps_inicial) ** (1 / n_años)) - 1
    
    equity_avg = (equity + equity.shift(1)) / 2
    equity_avg = equity_avg.replace(0, np.nan).apply(lambda x: x if x > 0 else np.nan)
    roe_medio = (net_income / equity_avg).dropna().mean()

    # Asignación de PER lógico según foso económico
    if roe_medio > 0.30 and cagr_historico > 0.15: per_futuro = 25
    elif roe_medio > 0.15 and cagr_historico > 0.08: per_futuro = 20
    elif roe_medio > 0.10 and cagr_historico > 0.00: per_futuro = 15
    else: per_futuro = 10 

    eps_actual = eps_final

    # 4. DATOS DE MERCADO EN VIVO
    precio_actual = None
    tasa_libre_riesgo = 0.045  # 4.5% por defecto
    beta = 1.0 # Riesgo neutro por defecto
    payout_ratio = 0.0

    try:
        ticker_yf = yf.Ticker(ticker_symbol)
        info = ticker_yf.info
        
        hist_precio = ticker_yf.history(period="5d")
        if not hist_precio.empty:
            precio_actual = float(hist_precio['Close'].iloc[-1])
            
        tnx = yf.Ticker("^TNX")
        hist_tnx = tnx.history(period="5d")
        if not hist_tnx.empty:
            tasa_libre_riesgo = float(hist_tnx['Close'].iloc[-1]) / 100
            
        # Extraemos Beta (Riesgo) y Payout Ratio (cuánto dividendo paga)
        beta = info.get('beta', 1.0)
        payout_ratio = info.get('payoutRatio', 0.0)
            
    except Exception as e:
        pass

    earnings_yield = (eps_actual / precio_actual) if precio_actual else None
    
    # ==========================================
    # MÚLTIPLES MODELOS DE VALORACIÓN
    # ==========================================
    # 1. Variables Base
    tasa_retencion = 1 - payout_ratio
    roe_normalizado = min(roe_medio, 0.35) # Tope del 35% por si recompran muchas acciones
    g_sostenible = roe_normalizado * tasa_retencion
    
    # Crecimiento estimado realista (mezcla histórico y sostenible, tope del 18%)
    g_estimado = (g_sostenible * 0.5) + (min(cagr_historico, 0.20) * 0.5)
    g_estimado = min(max(g_estimado, 0.05), 0.18) 
    g_pct = g_estimado * 100
    
    tasa_descuento_capm = tasa_libre_riesgo + (beta * 0.055)
    tasa_descuento_capm = max(tasa_descuento_capm, 0.07) # Mínimo 7% de descuento
    
    rf_pct = tasa_libre_riesgo * 100
    
    # 2. Fórmula Benjamin Graham Actualizada: V = (EPS * (8.5 + 2g) * 4.4) / RF
    graham_value = 0
    if eps_actual > 0 and rf_pct > 0:
        graham_value = (eps_actual * (8.5 + 2 * g_pct) * 4.4) / rf_pct
        
    # 3. Peter Lynch Fair Value (PEG = 1) -> Precio Justo = EPS * (Crecimiento + Dividend Yield)
    lynch_value = 0
    if eps_actual > 0:
        div_yield = payout_ratio * earnings_yield * 100 if payout_ratio and earnings_yield else 0
        lynch_value = eps_actual * (g_pct + div_yield)
        
    # 4. Earnings Power Value (EPV): Valor asumiendo CERO crecimiento futuro
    epv_value = 0
    if eps_actual > 0 and tasa_descuento_capm > 0:
        epv_value = eps_actual / tasa_descuento_capm

    return {
        "año_inicio": año_ini, "año_fin": año_fin,
        "eps_actual": eps_actual, "cagr_historico": cagr_historico, 
        "roe": roe_medio, "per_asumido": per_futuro,
        "precio_actual": precio_actual,
        "earnings_yield": earnings_yield,
        "tasa_libre_riesgo": tasa_libre_riesgo,
        "acciones_actuales": acciones_actuales,
        "beta": beta,
        "crecimiento_sostenible": g_estimado,
        "tasa_descuento_capm": tasa_descuento_capm,
        "graham_value": graham_value,
        "lynch_value": lynch_value,
        "epv_value": epv_value
    }

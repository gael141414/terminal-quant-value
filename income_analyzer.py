# Añadir imports
import re
import pandas as pd
import numpy as np

# Limpieza de bloque
def _clean_numeric_block(df_block):
    rep = {
        r',': '', r'\$': '', r'—': '', r'–': '', r'%': '',
    }
    cleaned = df_block.astype(str).replace(rep, regex=True)
    cleaned = cleaned.replace(r'^\((.*)\)$', r'-\1', regex=True)
    return cleaned.apply(pd.to_numeric, errors='coerce')

def extraer_dato_robusto(df, terminos, cols, verbose=False):
    if df is None or df.empty:
        return pd.Series([np.nan] * len(cols), index=cols)

    meta_cols = [c for c in ["standard_concept", "concept", "label"] if c in df.columns]
    escaped_terms = [re.escape(t) for t in terminos]

    # 1) MATCH EXACTO AVANZADO
    patron_exacto = r"(?i)^(?:[a-zA-Z0-9\-]+_)?(" + "|".join(escaped_terms) + r")$"
    
    for meta in meta_cols:
        col_data = df[meta]
        # BLINDAJE: Si hay columnas duplicadas, nos quedamos solo con la primera
        if isinstance(col_data, pd.DataFrame):
            col_data = col_data.iloc[:, 0]
            
        mask = col_data.astype(str).str.match(patron_exacto, na=False)
        if mask.any():
            block = df.loc[mask, cols]
            res = _clean_numeric_block(block)
            res['nulos'] = res.isnull().sum(axis=1)
            res['len'] = col_data.loc[mask].astype(str).str.len().values
            chosen = res.sort_values(['nulos','len']).drop(columns=['nulos','len']).iloc[0]
            return chosen

    # 2) MATCH AMPLIO
    patron_loose = r"(?i)(" + "|".join(escaped_terms) + r")"
    mask_loose = pd.Series(False, index=df.index)
    
    for meta in meta_cols:
        col_data = df[meta]
        if isinstance(col_data, pd.DataFrame):
            col_data = col_data.iloc[:, 0]
        mask_loose = mask_loose | col_data.astype(str).str.contains(patron_loose, na=False, regex=True)
        
    if mask_loose.any():
        block = df.loc[mask_loose, cols]
        res = _clean_numeric_block(block)
        
        min_lens = []
        for idx in block.index:
            l = 999
            for meta in meta_cols:
                col_data = df[meta]
                if isinstance(col_data, pd.DataFrame):
                    col_data = col_data.iloc[:, 0]
                    
                val = col_data.loc[idx]
                if isinstance(val, pd.Series):
                    val = str(val.iloc[0])
                else:
                    val = str(val)
                    
                if pd.Series([val]).str.contains(patron_loose, case=False, regex=True).iloc[0]:
                    l = min(l, len(val))
            min_lens.append(l)
            
        res['len'] = min_lens
        res['nulos'] = res.isnull().sum(axis=1)
        chosen = res.sort_values(['nulos','len']).drop(columns=['nulos','len']).iloc[0]
        return chosen

    return pd.Series([np.nan] * len(cols), index=cols)

def analizar_cuenta_resultados(df, cf_df=None):
    if df is None: return None
    cols = sorted([c for c in df.columns if str(c).isdigit() and len(str(c)) == 4])
    if not cols: return None

    ventas = extraer_dato_robusto(df, ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenueFromContractWithCustomer', 'SalesRevenueNet', 'SalesRevenueGoodsNet', 'SalesRevenueServicesNet', 'TotalRevenues', 'Net sales', 'Total Revenues', 'Net revenues'], cols)
    margen_bruto = extraer_dato_robusto(df, ['GrossProfit', 'Gross margin', 'Gross profit'], cols)
    
    cogs = extraer_dato_robusto(df, ['CostOfRevenue', 'CostOfGoodsAndServicesSold', 'CostOfGoodsSold', 'CostOfServices', 'Cost of sales', 'Cost of revenues'], cols)
    if margen_bruto.isna().all() and not cogs.isna().all():
        margen_bruto = ventas - cogs.fillna(0)
        
    vga = extraer_dato_robusto(df, ['SellingGeneralAndAdministrativeExpense', 'GeneralAndAdministrativeExpense', 'SellingAndMarketingExpense', 'Selling, general', 'SG&A'], cols)
    id_gasto = extraer_dato_robusto(df, ['ResearchAndDevelopmentExpense', 'Research and development', 'R&D'], cols)
        
    #print("\nVENTAS")
    #print(ventas)
    #print("\nMARGEN BRUTO")
    #print(margen_bruto)
    #print("\nVG&A")
    #print(vga)
    #print("\nID")
    #print(id_gasto)
    
    # --- DEPRECIACIÓN E INTERESES BLINDADOS (Se buscan en CashFlow si fallan en Resultados) ---
    if cf_df is not None:
        cols_cf = sorted([c for c in cf_df.columns if str(c).isdigit() and len(str(c)) == 4])
        depreciacion = extraer_dato_robusto(cf_df, ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretion", "Depreciation", "Amortization", "Depreciation, depletion and amortization"], cols_cf).abs()
        intereses = extraer_dato_robusto(cf_df, ["InterestPaidNet", "Cash paid for interest", "InterestExpense", "InterestExpenseDebt", "InterestExpenseNonoperating", "InterestAndDebtExpense", "InterestAndOtherIncomeExpenseNet", "InterestPaid", "Interest expense", "Interest and dividend expense"], cols_cf).abs()
    else:
        depreciacion = extraer_dato_robusto(df, ['DepreciationDepletionAndAmortization', 'DepreciationAndAmortization', 'Depreciation'], cols).abs()
        intereses = pd.Series([np.nan] * len(cols), index=cols)
        
    if depreciacion.isna().all():
        depreciacion = extraer_dato_robusto(df, ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "DepreciationAmortizationAndAccretion", "Depreciation", "Amortization"], cols).abs()
    if intereses.isna().all() or (intereses == 0).all():
        intereses = extraer_dato_robusto(cf_df, ["InterestPaidNet", "Cash paid for interest", "InterestExpense", "InterestExpenseDebt", "InterestExpenseNonoperating", "InterestAndDebtExpense", "InterestAndOtherIncomeExpenseNet", "InterestPaid", "Interest expense", "Interest and dividend expense"], cols_cf).abs()

    op_income = extraer_dato_robusto(df, ['OperatingIncomeLoss', 'Operating income', 'Income from operations'], cols)
    beneficio_neto = extraer_dato_robusto(df, ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic', 'ProfitLoss', 'Net income', 'Net earnings'], cols)

    if margen_bruto.isna().all():
        cogs = extraer_dato_robusto(df, ['CostOfGoodsAndServicesSold', 'Cost of sales'], cols)
        margen_bruto = ventas - cogs.fillna(0)

    #print("\nDEPRECIACIÓN")
    #print(depreciacion)
    #print("\nINTERESES")
    #print(intereses)
    
    df_ratios = pd.DataFrame(index=cols)
    df_ratios['Margen Bruto %'] = (margen_bruto / ventas.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    df_ratios['SG&A % (s/MB)'] = (vga / margen_bruto.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    df_ratios['I+D % (s/MB)'] = (id_gasto / margen_bruto.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    df_ratios['Depreciación % (s/MB)'] = (depreciacion / margen_bruto.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    df_ratios['Intereses % (s/OpInc)'] = (intereses / op_income.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    df_ratios['Margen Neto %'] = (beneficio_neto / ventas.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan).clip(lower=-1000, upper=1000)
    
    cols_ordenados = sorted(cols)
    beneficio_ordenado = beneficio_neto[cols_ordenados]
    df_ratios['Crecimiento Benef. Neto %'] = beneficio_ordenado.pct_change(fill_method=None) * 100

    #print("\nRATIOS")
    #print(df_ratios)

    return {"ratios": df_ratios.round(2)}

if __name__ == "__main__":

    from downloader import obtener_estados_financieros

    ticker = "AAPL"

    is_df, bs_df, cf_df = obtener_estados_financieros(ticker)

    resultado = analizar_cuenta_resultados(is_df, cf_df)

    print(resultado["ratios"])
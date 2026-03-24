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


def analizar_balance(bs_df, is_df=None):
    if bs_df is None: return None
    cols_bs = sorted([c for c in bs_df.columns if str(c).isdigit() and len(str(c)) == 4])    

    patrimonio = extraer_dato_robusto(bs_df, ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest', 'Total Equity', "Total stockholders' equity"], cols_bs)
    activos = extraer_dato_robusto(bs_df, ['Assets', 'Total assets', 'Total Assets'], cols_bs)

    deuda_largo = extraer_dato_robusto(bs_df, ['LongTermDebtNoncurrent', 'LongTermDebt', 'UnsecuredDebt', 'Term debt', 'Long-term debt'], cols_bs).fillna(0)
    cp = extraer_dato_robusto(bs_df, ['CommercialPaper', 'Commercial Paper'], cols_bs).fillna(0)
    ltd_curr = extraer_dato_robusto(bs_df, ['LongTermDebtCurrent', 'Current portion of term debt', 'Current portion of long-term debt', 'LongTermDebtAndCapitalLeaseObligationsCurrent'], cols_bs).fillna(0)
    short_term_debt = extraer_dato_robusto(bs_df, ['ShortTermBorrowings', 'Short-term debt'], cols_bs).fillna(0)
    deuda_total = deuda_largo + cp + ltd_curr + short_term_debt

    caja_efectivo = extraer_dato_robusto(bs_df, ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 'Cash and cash equivalents'], cols_bs).fillna(0)
    caja_inv_cp = extraer_dato_robusto(bs_df, ["MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesCurrent", "ShortTermInvestments", "Short-term marketable securities"], cols_bs).fillna(0)
    caja_inv_lp = extraer_dato_robusto(bs_df, ["MarketableSecuritiesNoncurrent", "AvailableForSaleSecuritiesNoncurrent", "Long-term marketable securities"], cols_bs).fillna(0)
    caja_total = caja_efectivo + caja_inv_cp + caja_inv_lp

    ganancias_retenidas = extraer_dato_robusto(bs_df, ['RetainedEarningsAccumulatedDeficit', 'RetainedEarnings', 'Retained earnings', 'Accumulated deficit'], cols_bs)
    ppe = extraer_dato_robusto(bs_df, ['PropertyPlantAndEquipmentNet', 'Property, plant and equipment, net', 'Property and equipment, net'], cols_bs)

    #print("\nPATRIMONIO:")
    #print(patrimonio)
    #print("\nACTIVOS:")
    #print(activos)
    #print("\nDEUDA LARGO PLAZO:")
    #print(deuda_largo)
    #print("\nCP:")
    #print(cp)
    #print("\nDEUDA CURR PLAZO:")
    #print(ltd_curr)
    #print("\nDEUDA CURR PLAZO:")
    #print(short_term_debt)
    #print("\nDEUDA TOTAL:")
    #print(deuda_total)
    #print("\nCAJA EFECTIVO:")
    #print(caja_efectivo)
    #print("\nCAJA INV CP:")
    #print(caja_inv_cp)
    #print("\nCAJA INV LP:")
    #print(caja_inv_lp)
    #print("\nCAJA TOTAL:")
    #print(caja_total)
    #print("\nGANANCIAS RETENIDAS:")
    #print(ganancias_retenidas)
    #print("\nPPE:")
    #print(ppe)

    df_bal_ratios = pd.DataFrame(index=cols_bs)

    if is_df is not None:
        cols_is = [c for c in is_df.columns if str(c).isdigit() and len(str(c)) == 4]
        
        beneficio_neto = extraer_dato_robusto(is_df, ['NetIncomeLoss', 'Net income'], cols_is)
        ventas = extraer_dato_robusto(is_df, ['RevenueFromContractWithCustomerExcludingAssessedTax', 'RevenueFromContractWithCustomer', 'SalesRevenueNet', 'Net sales'], cols_is)
        op_income = extraer_dato_robusto(is_df, ['OperatingIncomeLoss', 'Operating income'], cols_is)
        tax_expense = extraer_dato_robusto(is_df, ['IncomeTaxExpenseBenefit', 'Income tax expense'], cols_is)
        ebt = extraer_dato_robusto(is_df, ['IncomeBeforeIncomeTaxes', 'Income before provision for income taxes', 'Income before income taxes'], cols_is)

        #print("\nBENEFICIO NETO:")
        #print(beneficio_neto)
        #print("\nVENTAS:")
        #print(ventas)
        #print("\nOP INCOME:")
        #print(op_income)
        #print("\nTAX EXPENSE:")
        #print(tax_expense)
        #print("\nEBT:")
        #print(ebt)
        
        beneficio_neto_aligned = pd.Series(index=cols_bs, dtype=float)
        op_income_aligned = pd.Series(index=cols_bs, dtype=float)
        ventas_aligned = pd.Series(index=cols_bs, dtype=float)
        tax_rate_aligned = pd.Series(index=cols_bs, dtype=float).fillna(0.21)
        
        for c in cols_bs:
            if c in cols_is:
                beneficio_neto_aligned[c] = beneficio_neto[c]
                op_income_aligned[c] = op_income[c]
                ventas_aligned[c] = ventas[c]
                if ebt[c] != 0 and not pd.isna(ebt[c]):
                    tax_rate_aligned[c] = tax_expense[c] / ebt[c]

        # ⚠️ SOLUCIÓN AL ERROR DE AÑOS VACÍOS (shift(1) en lugar de shift(-1) y fillna)
        equity_avg = (patrimonio + patrimonio.shift(1)) / 2
        equity_avg = equity_avg.fillna(patrimonio) # Respaldo para el primer año
        
        activos_avg = (activos + activos.shift(1)) / 2
        activos_avg = activos_avg.fillna(activos)
        
        df_bal_ratios['ROE %'] = (beneficio_neto_aligned / equity_avg.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan)
        df_bal_ratios['DuPont: Margen Neto %'] = (beneficio_neto_aligned / ventas_aligned.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan)
        df_bal_ratios['DuPont: Rotación Activos'] = (ventas_aligned / activos_avg.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        df_bal_ratios['DuPont: Apalancamiento'] = (activos_avg / equity_avg.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)

        nopat = op_income_aligned * (1 - tax_rate_aligned)
        capital_invertido = patrimonio + deuda_total
        capital_invertido_avg = (capital_invertido + capital_invertido.shift(1)) / 2
        capital_invertido_avg = capital_invertido_avg.fillna(capital_invertido)
        
        df_bal_ratios['ROIC %'] = (nopat / capital_invertido_avg.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan)
        
        df_bal_ratios['Años para pagar Deuda LP'] = (deuda_largo / beneficio_neto_aligned.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
        df_bal_ratios['Carga PP&E (PP&E/Benef.)'] = (ppe / beneficio_neto_aligned.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)

    df_bal_ratios['Deuda / Capital'] = (deuda_total / patrimonio.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    
    # Esta caja neta ahora sí incluirá todas las inversiones de Apple, dando un número muy positivo (+54B)
    df_bal_ratios['Caja Neta (B USD)'] = (caja_total - deuda_total) / 1e9

    ganancias_ordenadas = ganancias_retenidas.sort_index()
    df_bal_ratios['Crecimiento Gan. Retenidas %'] = (ganancias_ordenadas.diff() / ganancias_ordenadas.shift(1).abs()) * 100

    #print("\nDF BAL RATIOS:\n")
    #print(df_bal_ratios)

    return {"ratios": df_bal_ratios.round(2)}

if __name__ == "__main__":

    from downloader import obtener_estados_financieros

    ticker = "AAPL"

    is_df, bs_df, cf_df = obtener_estados_financieros(ticker)

    resultado = analizar_balance(bs_df, is_df)

    print(resultado["ratios"])
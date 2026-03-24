import pandas as pd
import os

from downloader import obtener_estados_financieros
from income_analyzer import analizar_cuenta_resultados
from balance_analyzer import analizar_balance
from cashflow_analyzer import analizar_flujo_efectivo
from valuator import valorar_empresa
from plotter import generar_graficos_buffett

def generar_reporte_excel(ticker, is_ratios, bs_ratios, cf_ratios, val_data):
    print(f"[*] Generando reporte Excel para {ticker}...")
    
    # 1. Unir métricas
    df_completo = pd.concat([is_ratios, bs_ratios, cf_ratios], axis=1)
    df_transpuesto = df_completo.T
    
    # 2. Diccionario Maestro de Buffett (Alineado con los Capítulos)
    umbrales_buffett = {
        # Cuenta de Resultados
        "Margen Bruto %": "> 40% (Ventaja Duradera) / < 20% (Sin ventaja)",
        "SG&A % (s/MB)": "< 30% (Fantástico) / > 80% (Peligro, demasiada competencia)",
        "I+D % (s/MB)": "< 30% (Si es alto, su foso se basa en innovar o morir)",
        "Depreciación % (s/MB)": "< 10% (Excelentes negocios no requieren reponer maquinaria)",
        "Intereses % (s/OpInc)": "< 15% (Poca dependencia de la deuda bancaria)",
        "Margen Neto %": "> 20% (Señal clara de monopolio o dominio en su sector)",
        "Crecimiento Beneficio Neto %": "Debe mostrar una tendencia ascendente histórica",
        
        # Balance
        "ROE %": "> 15% constante (Muestra si la directiva asigna bien el capital)",
        "Deuda/Capital": "< 0.80 (Bajo apalancamiento, se financia con sus beneficios)",
        "Años para pagar Deuda LP": "3 a 4 años usando todo el Beneficio Neto",
        "Crecimiento Ganancias Retenidas %": "~ 10% anual constante (El secreto para hacerse rico)",
        "Carga PP&E (PP&E / Beneficio)": "Menos es mejor (No requiere fábricas gigantescas)",
        "Caja Neta (B USD)": "Positiva indica que no necesita pedir prestado para sobrevivir",
        
        # Flujo de Efectivo
        "CAPEX % sobre Beneficio": "< 50% (Ideal < 25%, genera dinero sin gastarlo en mantenimiento)",
        "Recompras (B USD)": "Cifra positiva y constante indica que devuelven valor al accionista",
        "Free Cash Flow (B USD)": "Flujo de caja libre. El dinero real que pertenece al dueño."
    }
    
    # 3. Mapear los umbrales a una nueva columna
    df_transpuesto.insert(0, "Umbral Buffett (Criterio)", df_transpuesto.index.map(umbrales_buffett))
    
    # 4. Guardar en Excel
    nombre_archivo = f"{ticker}_Buffett_Analysis.xlsx"
    
    try:
        with pd.ExcelWriter(nombre_archivo, engine='openpyxl') as writer:
            # Hoja 1: Ratios Históricos
            df_transpuesto.to_excel(writer, sheet_name="Métricas y Umbrales")
            
            # Hoja 2: Resumen de Valoración
            if val_data:
                # Damos formato a los resultados de valoración
                val_resumen = {
                    "Periodo Analizado": f"{val_data['año_inicio']} - {val_data['año_fin']}",
                    "BPA (EPS) Actual": f"${val_data['eps_actual']:.2f}",
                    "CAGR Histórico": f"{val_data['cagr']*100:.2f}%",
                    "ROE Promedio": f"{val_data['roe']*100:.2f}%",
                    "PER Asumido (Múltiplo)": f"{val_data['per_asumido']}x",
                    "Valor Intrínseco (Justo)": f"${val_data['valor_intrinseco']:.2f}",
                    "PRECIO COMPRA SEGURO (Margen 25%)": f"${val_data['precio_compra_seguro']:.2f}"
                }
                df_val = pd.DataFrame([val_resumen]).T
                df_val.columns = ["Valor"]
                df_val.to_excel(writer, sheet_name="Valoración (Equity Bond)")
                
        print(f"[+] Excel generado con éxito: {os.path.abspath(nombre_archivo)}")
    except Exception as e:
        print(f"[!] Error al generar el Excel: {e}\n(Asegúrate de tener cerrado el archivo si ya existía y de haber instalado 'openpyxl')")

def main():
    print("="*65)
    print("   SISTEMA DE ANÁLISIS FUNDAMENTAL - ESTILO WARREN BUFFETT   ")
    print("="*65)
    
    ticker = input("Introduce el Ticker de la empresa (Ej. AAPL, MSFT, KO): ").upper().strip()
    if not ticker: ticker = "AAPL"
        
    años_historial = 10

    # 1. Obtener Datos (Usa caché automáticamente por el nuevo downloader)
    is_df, bs_df, cf_df = obtener_estados_financieros(ticker, años_historial)

    if is_df is None or bs_df is None or cf_df is None:
        print("[!] No se pudieron obtener los datos. Abortando.")
        return

    # 2. Analizar Estados
    res_is = analizar_cuenta_resultados(is_df)
    res_bs = analizar_balance(bs_df, is_df)
    res_cf = analizar_flujo_efectivo(cf_df, is_df)

    # 3. Valorar
    res_val = valorar_empresa(is_df, bs_df, cf_df)

    # 4. Consolidar Resultados
    if res_is and res_bs and res_cf:
        generar_reporte_excel(ticker, res_is["ratios"], res_bs["ratios"], res_cf["ratios"], res_val)
        
        # 5. Dashboard Visual
        print("[*] Generando Dashboard Visual...")
        generar_graficos_buffett(res_is["ratios"], res_bs["ratios"], res_cf["ratios"], ticker)
        
        print("\n" + "="*65)
        print(f" [+] ANÁLISIS COMPLETADO EXITOSAMENTE PARA {ticker}")
        if res_val:
            print(f"     Valor Intrínseco: ${res_val['valor_intrinseco']:.2f}")
            print(f"     Precio de Compra (Margen de Seguridad): ${res_val['precio_compra_seguro']:.2f}")
        print("="*65)

if __name__ == "__main__":
    main()
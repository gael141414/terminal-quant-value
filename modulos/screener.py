import streamlit as st
import yfinance as yf
import pandas as pd

def ejecutar_escaner_global():
    st.markdown("### 🌐 Escáner Cuantitativo de Oportunidades")
    st.markdown("Introduce una cesta de acciones y aplica filtros institucionales estrictos para separar las empresas excepcionales de las mediocres.")

    # 1. Input de Tickers
    tickers_input = st.text_area("📦 Cesta de Tickers a escanear (separados por comas):", "AAPL, MSFT, GOOGL, META, TSLA, NVDA, AMZN, NFLX, AMD, INTC, CRM, ADBE")
    
    st.markdown("#### ⚙️ Configura tus Filtros (Reglas Quant)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_per = st.number_input("📉 PER Máximo (Value)", min_value=1, max_value=200, value=30, help="Relación Precio/Beneficio. Menor es más barato.")
    with col2:
        min_roe = st.number_input("📈 ROE Mínimo % (Calidad)", min_value=-50, max_value=100, value=15, help="Retorno sobre el Capital. Mayor a 15% es excelente.")
    with col3:
        min_growth = st.number_input("🚀 Crecimiento Ventas Mínimo %", min_value=-50, max_value=200, value=10, help="Crecimiento de ingresos YoY.")

    if st.button("⚡ Ejecutar Escáner", type="primary", use_container_width=True):
        lista_tickers = [t.strip().upper() for t in tickers_input.split(',')]
        
        if not lista_tickers or lista_tickers == ['']:
            st.warning("Introduce al menos un Ticker.")
            return

        # Barra de progreso para UX
        progress_text = "Escanenando mercado..."
        barra_progreso = st.progress(0, text=progress_text)
        
        resultados = []
        
        for i, ticker in enumerate(lista_tickers):
            try:
                info = yf.Ticker(ticker).info
                
                # Extraer métricas clave de forma segura
                per = info.get('trailingPE', 999) # 999 si no tiene beneficios
                roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
                crecimiento = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
                deuda = info.get('debtToEquity', 0)
                
                # Guardar datos en crudo
                resultados.append({
                    'Ticker': ticker,
                    'Sector': info.get('sector', 'N/A'),
                    'PER': round(per, 2),
                    'ROE (%)': round(roe, 2),
                    'Crecimiento YoY (%)': round(crecimiento, 2),
                    'Deuda/Equity': round(deuda, 2)
                })
            except Exception:
                pass # Si un ticker falla (ej. está mal escrito), lo ignoramos
            
            # Actualizar barra de progreso
            barra_progreso.progress((i + 1) / len(lista_tickers), text=f"Analizando {ticker}...")
            
        barra_progreso.empty() # Borrar barra al terminar
        
        if resultados:
            df = pd.DataFrame(resultados)
            
            # 2. Aplicar los Filtros del Usuario
            df_filtrado = df[
                (df['PER'] <= max_per) & 
                (df['ROE (%)'] >= min_roe) & 
                (df['Crecimiento YoY (%)'] >= min_growth)
            ]
            
            st.markdown("---")
            if df_filtrado.empty:
                st.error("🩸 Masacre Cuantitativa: NINGUNA empresa de tu cesta ha sobrevivido a tus filtros estrictos. El mercado está caro o exige peores calidades.")
                st.markdown("#### Datos Crudos (Antes de filtrar)")
                st.dataframe(df)
            else:
                st.success(f"🏆 ¡Éxito! {len(df_filtrado)} empresas han superado el escáner de calidad.")
                
                # Mostrar tabla con formato condicional (verde si es muy bueno)
                st.dataframe(
                    df_filtrado.style.highlight_max(subset=['ROE (%)', 'Crecimiento YoY (%)'], color='#1e4bd8')
                                    .highlight_min(subset=['PER'], color='#00C0F2'),
                    use_container_width=True
                )

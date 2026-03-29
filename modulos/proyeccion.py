import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import re
import google.generativeai as genai

def ejecutar_proyeccion(ticker_input):
    """Modelo probabilístico de 3 escenarios (Toro, Base, Oso) y extracción de Catalizadores"""

    st.markdown(f"### 🔮 Proyección Cuantitativa y Catalizadores: {ticker_input}")
    st.markdown("Modelo probabilístico: La IA evalúa fundamentales y sentimiento actual para trazar 3 escenarios de precio a 12 meses.")
    
    if st.button("🚀 Ejecutar Modelo Probabilístico", type="primary", use_container_width=True):
        with st.spinner("Procesando flujo de noticias y calculando proyecciones de precio..."):
            try:
                import yfinance as yf
                import pandas as pd
                import plotly.graph_objects as go
                import json
                import re
                
                # 1. Extraer datos actuales
                empresa_yf = yf.Ticker(ticker_input)
                noticias_crudas = empresa_yf.news
                info = empresa_yf.info
                
                precio_actual = info.get('currentPrice', info.get('previousClose', 100))
                sector = info.get('sector', 'Desconocido')
                
                text_noticias = "Sin noticias recientes."
                if noticias_crudas:
                    lista_titulares = [f"- {n.get('title', '')}" for n in noticias_crudas[:6] if n.get('title')]
                    text_noticias = "\n".join(lista_titulares)
                
                separador = "`" * 3
                
                # 2. Prompt estructurado para forzar estadísticas
                prompt_proyeccion = f"""
                Eres un Analista Cuantitativo. Acción: {ticker_input}. Sector: {sector}. Precio Actual: ${precio_actual}.
                Titulares recientes:
                {text_noticias}
                
                Genera un análisis y devuelve OBLIGATORIAMENTE este JSON estructurado al final. Debes mojarte y dar precios objetivo (Target Price) realistas a 12 meses.
                
                Estructura del JSON requerida al final de tu respuesta:
                {separador}json
                {{
                  "analisis_narrativo": "Tu tesis de inversión resumida en 3 líneas...",
                  "puntos_fuertes": ["Foso 1", "Foso 2", "Foso 3"],
                  "catalizadores": ["Evento A", "Evento B"],
                  "probabilidad_alcista_pct": 65,
                  "precio_toro": 150.50,
                  "precio_base": 120.00,
                  "precio_oso": 90.00
                }}
                {separador}

                REGLA CRÍTICA DE PROGRAMACIÓN: NO uses comillas dobles (") bajo ningún concepto DENTRO de los textos del JSON. Si necesitas entrecomillar algo, usa obligatoriamente comillas simples (').
                """
                
                modelo_disponible = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        modelo_disponible = m.name
                        if "flash" in m.name.lower(): break 
                        
                if modelo_disponible:
                    model = genai.GenerativeModel(modelo_disponible)
                    response = model.generate_content(prompt_proyeccion)
                    respuesta_ia = response.text
                    
                    # 3. Extraer el JSON
                    patron_busqueda = separador + r'(?:json)?\s*(\{.*?\})\s*' + separador
                    match = re.search(patron_busqueda, respuesta_ia, re.DOTALL | re.IGNORECASE)
                    if not match:
                        match = re.search(r'(\{.*?\})', respuesta_ia, re.DOTALL)
                        
                    if match:
                        texto_json = match.group(1)
                        texto_json = texto_json.replace("'\n", "',\n").strip() 
                        
                        try:
                            datos_json = json.loads(texto_json, strict=False)
                        except json.JSONDecodeError:
                            import ast
                            datos_json = ast.literal_eval(texto_json)
                        datos_json = json.loads(match.group(1).replace("'", '"'))
                        
                        p_toro = float(datos_json.get("precio_toro", precio_actual * 1.2))
                        p_base = float(datos_json.get("precio_base", precio_actual * 1.05))
                        p_oso = float(datos_json.get("precio_oso", precio_actual * 0.8))
                        prob_alcista = datos_json.get("probabilidad_alcista_pct", 50)
                        
                        # Cálculos de rentabilidad
                        ret_toro = ((p_toro / precio_actual) - 1) * 100
                        ret_base = ((p_base / precio_actual) - 1) * 100
                        ret_oso = ((p_oso / precio_actual) - 1) * 100
                        
                        st.markdown("---")
                        
                        # 📊 TARJETAS VISUALES DE PROYECCIÓN
                        st.markdown(f"### 🎯 Precio Objetivo a 12 Meses (Probabilidad Alcista: {prob_alcista}%)")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("🟢 Caso Toro (Optimista)", f"${p_toro:,.2f}", f"{ret_toro:+.2f}%")
                        c2.metric("🟡 Caso Base (Probable)", f"${p_base:,.2f}", f"{ret_base:+.2f}%")
                        c3.metric("🔴 Caso Oso (Pesimista)", f"${p_oso:,.2f}", f"{ret_oso:+.2f}%")
                        
                        # 📈 GRÁFICO DE ABANICO (FAN CHART)
                        fecha_hoy = pd.Timestamp.today()
                        fecha_futura = fecha_hoy + pd.DateOffset(months=12)
                        
                        fig = go.Figure()
                        # Punto de origen (Hoy)
                        fig.add_trace(go.Scatter(x=[fecha_hoy], y=[precio_actual], mode='markers', marker=dict(color='white', size=10), name='Precio Actual'))
                        # Linea Toro
                        fig.add_trace(go.Scatter(x=[fecha_hoy, fecha_futura], y=[precio_actual, p_toro], mode='lines+markers', line=dict(color='#00C0F2', width=3, dash='dot'), name='Caso Toro'))
                        # Linea Base
                        fig.add_trace(go.Scatter(x=[fecha_hoy, fecha_futura], y=[precio_actual, p_base], mode='lines+markers', line=dict(color='#8c9bba', width=3), name='Caso Base'))
                        # Linea Oso
                        fig.add_trace(go.Scatter(x=[fecha_hoy, fecha_futura], y=[precio_actual, p_oso], mode='lines+markers', line=dict(color='#ff4b4b', width=3, dash='dot'), name='Caso Oso'))
                        
                        fig.update_layout(height=400, margin=dict(t=20, b=20, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown("---")
                        # 🛡️ LISTAS CLARAS DE CATALIZADORES
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("#### 🛡️ Fosos Defensivos (Moats)")
                            for foso in datos_json.get("puntos_fuertes", []):
                                st.success(f"✔️ {foso}")
                        with col_b:
                            st.markdown("#### ⚡ Catalizadores (Drivers)")
                            for cat in datos_json.get("catalizadores", []):
                                st.info(f"🚀 {cat}")
                                
                        st.markdown("<br>#### 🧠 Tesis del Algoritmo", unsafe_allow_html=True)
                        st.write(datos_json.get("analisis_narrativo", ""))
                    else:
                        st.error("Error al estructurar los datos numéricos. Inténtalo de nuevo.")
                        
            except Exception as e:
                st.error(f"Error procesando la proyección: {e}")

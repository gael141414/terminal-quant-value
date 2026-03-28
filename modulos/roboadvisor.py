import streamlit as st
import re
import json
import plotly.express as px
import google.generativeai as genai

def ejecutar_roboadvisor():
    """Motor del test psicológico y Asset Allocation con IA"""
    st.markdown("### 🤖 Robo-Advisor Institucional: Perfilado Cuantitativo")
    
    # Lista de las 17 preguntas (Base de datos interna)
    preguntas_test = [
        {"pilar": "🏛️ PILAR 1: Horizonte Temporal", "q": "1. ¿En qué etapa vital te encuentras?", "op": ["a) Joven (18-35) - Acumulación agresiva", "b) Adulto (36-50) - Crecimiento con consolidación", "c) Maduro (51-65) - Preparando jubilación", "d) Jubilado (>65) - Distribución y preservación"]},
        {"pilar": "🏛️ PILAR 1: Liquidez", "q": "2. ¿Cuándo planeas retirar más del 30% del capital?", "op": ["a) En menos de 2 años", "b) Entre 2 y 5 años", "c) Entre 5 y 10 años", "d) En más de 10 años"]},
        {"pilar": "🏛️ PILAR 1: Colchón de Seguridad", "q": "3. ¿Cómo está tu Fondo de Emergencia (en efectivo)?", "op": ["a) No tengo, invierto todo", "b) Cubre 1-3 meses de gastos", "c) Cubre 3-6 meses", "d) Más de 6 meses cubiertos"]},
        {"pilar": "🧠 PILAR 2: Psicología del Inversor", "q": "4. Sleep Test: Tu cartera cae un 20% en un mes por pánico global. ¿Qué haces?", "op": ["a) Vendo todo por pánico", "b) Vendo una parte para sentirme seguro", "c) No hago nada (Hold)", "d) Compro más agresivamente (Buy the dip)"]},
        {"pilar": "🧠 PILAR 2: Aversión a la Pérdida", "q": "5. Elige tu escenario ideal para 10.000$ a 1 año:", "op": ["a) Ganar 400$ seguros (Cero riesgo)", "b) Ganar 800$, riesgo de perder 200$", "c) Ganar 1.500$, riesgo de perder 1.000$", "d) Ganar 3.000$, riesgo de perder 2.500$"]},
        {"pilar": "🧠 PILAR 2: Expectativas Visuales", "q": "6. Al invertir, ¿qué prefieres ver en tu cuenta?", "op": ["a) Cero volatilidad y dividendos altos", "b) Equilibrio: dividendos y algo de crecimiento", "c) Crecimiento rápido, aunque sea muy volátil"]},
        {"pilar": "🎯 PILAR 3: Nivel de Sofisticación", "q": "7. ¿Cuál es tu experiencia real en bolsa?", "op": ["a) Novato (Solo banco)", "b) Intermedio (Acciones y ETFs)", "c) Avanzado (Opciones, fundamentales, macro)"]},
        {"pilar": "🎯 PILAR 3: Objetivo del Capital", "q": "8. ¿Cuál es tu objetivo principal?", "op": ["a) Preservación (Batir inflación)", "b) Rentas (Dividendos pasivos)", "c) Crecimiento a largo plazo", "d) Especulación agresiva"]},
        {"pilar": "🎯 PILAR 3: Visión de Refugios", "q": "9. ¿Qué opinas de la Renta Fija y el Oro?", "op": ["a) Me encantan, dan seguridad", "b) Está bien tener un poco por si acaso", "c) No los quiero. 100% Acciones"]},
        {"pilar": "🎯 PILAR 3: Implicación Temporal", "q": "10. ¿Con qué frecuencia revisarás tu cartera?", "op": ["a) Todos los días", "b) Una vez al mes", "c) Una vez al año", "d) Comprar y olvidar (Buy & Hold)"]},
        {"pilar": "🔬 PILAR 4: Track Record", "q": "11. ¿En qué has invertido dinero REAL en el pasado?", "op": ["a) Nunca he invertido", "b) Letras, bonos o depósitos", "c) Fondos indexados globales", "d) Acciones sueltas o Criptomonedas"]},
        {"pilar": "🔬 PILAR 4: Autocrítica", "q": "12. ¿Cuál ha sido tu mayor error financiero?", "op": ["a) El miedo (no invertir y perder frente a la inflación)", "b) Vender en pánico", "c) Comprar en la cima por avaricia (FOMO)", "d) Ninguno, soy muy disciplinado"]},
        {"pilar": "🌍 PILAR 5: Megatendencias", "q": "13. ¿Qué sector sobreponderarías para la próxima década?", "op": ["a) Defensivo (Salud, Consumo Básico)", "b) Tecnológico / Inteligencia artificial", "c) Cíclico / Value (Energía, Bancos)", "d) Agnóstico (Compro el mundo entero)"]},
        {"pilar": "🌍 PILAR 5: Geopolítica", "q": "14. ¿Cuál es tu sesgo geográfico?", "op": ["a) 100% Estados Unidos", "b) Global Desarrollado (EEUU, Europa, Japón)", "c) Apuesta por Emergentes (Asia, Latam)"]},
        {"pilar": "💎 PILAR 6: Activos Digitales", "q": "15. ¿Qué papel juegan las Criptomonedas para ti?", "op": ["a) Rechazo absoluto (0%)", "b) Curiosidad / Asimetría (1% - 5%)", "c) Convicción alta (>10%)"]},
        {"pilar": "💎 PILAR 6: Ingresos Personales", "q": "16. ¿Cómo de estables son tus ingresos laborales?", "op": ["a) Inestables / Autónomo", "b) Normales / Contrato", "c) Muy seguros / Funcionario"]},
        {"pilar": "💎 PILAR 6: Valores Morales", "q": "17. ¿Te importa la inversión ética (ESG)?", "op": ["a) Sí, no quiero empresas contaminantes o de armas", "b) Me da igual, busco máxima rentabilidad"]}
    ]

    # --- INICIALIZACIÓN DE LA MÁQUINA DE ESTADOS (WIZARD) ---
    if "robo_step" not in st.session_state:
        st.session_state.robo_step = 0
    if "robo_answers" not in st.session_state:
        st.session_state.robo_answers = {}
    if "robo_submit" not in st.session_state:
        st.session_state.robo_submit = False

    # --- FASE 1: EL TEST INTERACTIVO ---
    if not st.session_state.robo_submit:
        q_idx = st.session_state.robo_step
        total_q = len(preguntas_test)
        
        # 1. Interfaz Visual Superior
        st.progress((q_idx + 1) / total_q)
        st.caption(f"Pregunta {q_idx + 1} de {total_q} — **{preguntas_test[q_idx]['pilar']}**")
        
        # 2. Tarjeta de la Pregunta
        st.markdown(f"<h3 style='color: #00C0F2; font-weight: 600;'>{preguntas_test[q_idx]['q']}</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recuperar respuesta si el usuario tiró "Hacia atrás"
        respuesta_guardada = st.session_state.robo_answers.get(q_idx, None)
        try: index_guardado = preguntas_test[q_idx]["op"].index(respuesta_guardada) if respuesta_guardada else None
        except: index_guardado = None
            
        opcion_elegida = st.radio("Elige una opción:", preguntas_test[q_idx]["op"], index=index_guardado, label_visibility="collapsed")
        
        # 3. Botones de Navegación (Diapositivas)
        st.markdown("<br><hr>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn1:
            if q_idx > 0:
                if st.button("⬅️ Anterior", use_container_width=True):
                    st.session_state.robo_answers[q_idx] = opcion_elegida
                    st.session_state.robo_step -= 1
                    st.rerun()
                    
        with col_btn3:
            if q_idx < total_q - 1:
                if st.button("Siguiente ➡️", use_container_width=True, type="primary"):
                    if opcion_elegida is None:
                        st.warning("⚠️ Selecciona una opción para avanzar.")
                    else:
                        st.session_state.robo_answers[q_idx] = opcion_elegida
                        st.session_state.robo_step += 1
                        st.rerun()
            else:
                if st.button("🚀 Crear Cartera", use_container_width=True, type="primary"):
                    if opcion_elegida is None:
                        st.warning("⚠️ Selecciona una opción para terminar.")
                    else:
                        st.session_state.robo_answers[q_idx] = opcion_elegida
                        st.session_state.robo_submit = True
                        st.rerun()

    # --- FASE 2: RESULTADOS Y ORÁCULO IA ---
    else:
        st.success("✅ Test Completado. Calculando Perfil Cuantitativo...")
        if st.button("🔄 Repetir el Test"):
            st.session_state.robo_step = 0
            st.session_state.robo_answers = {}
            st.session_state.robo_submit = False
            st.rerun()
            
        with st.spinner("🧠 La Inteligencia Artificial está analizando tu psicología y estructurando tu cartera..."):
            import re
            import json
            
            # Formatear el historial para la IA
            texto_respuestas = "\n".join([f"P{i+1}: {st.session_state.robo_answers[i]}" for i in range(17)])
            
            # TRUCO ANTI-BUGS: Generamos las comillas triples matemáticamente para no romper el visor
            separador = "`" * 3
            
            prompt_roboadvisor = f"""
            Eres el Director de Inversiones (CIO) de un Wealth Management Suizo. Crea un "Asset Allocation" perfecto basado en estas respuestas de tu cliente:
            {texto_respuestas}

            INSTRUCCIONES:
            1. Escribe un perfil psicológico detallado (Nivel de riesgo, sesgos, horizonte temporal).
            2. Tesis de Inversión: Explica en formato texto qué Tickers recomiendas y POR QUÉ los has elegido para esta persona. Enuméralos.
            3. CRÍTICO: Al final del todo, separado del texto, incluye obligatoriamente un bloque de código JSON con los Tickers exactos (ej. SPY, QQQ, GLD, SGOV) y sus porcentajes numéricos que sumen 100.
            
            Formato exacto del JSON al final:
            {separador}json
            {{
              "S&P 500 (SPY)": 50,
              "Oro (GLD)": 10,
              "Bonos (SGOV)": 40
            }}
            {separador}
            """
            
            try:
                # Buscar un modelo que funcione
                modelo_disponible = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        modelo_disponible = m.name
                        if "flash" in m.name.lower(): break 
                        
                if modelo_disponible:
                    model = genai.GenerativeModel(modelo_disponible)
                    response = model.generate_content(prompt_roboadvisor)
                    respuesta_ia = response.text
                    
                    # 1. Buscamos el JSON usando las variables dinámicas para evitar fallos de formato
                    patron_busqueda = separador + r'(?:json)?\s*(\{.*?\})\s*' + separador
                    match = re.search(patron_busqueda, respuesta_ia, re.DOTALL | re.IGNORECASE)
                    
                    if not match:
                        match = re.search(r'(\{.*?\})', respuesta_ia, re.DOTALL)

                    respuesta_limpia = respuesta_ia

                    if match:
                        try:
                            json_str = match.group(1).strip()
                            json_str = json_str.replace("'", '"')
                            cartera_dict = json.loads(json_str)
                            
                            st.markdown("---")
                            st.markdown("### 🍩 Tu Asset Allocation Recomendado")
                            
                            fig_pie = px.pie(
                                values=list(cartera_dict.values()), 
                                names=list(cartera_dict.keys()), 
                                hole=0.5,
                                color_discrete_sequence=px.colors.sequential.Tealgrn
                            )
                            fig_pie.update_traces(
                                textposition='inside',
                                textinfo='percent+label',
                                textfont_size=14,
                                hoverinfo='label+percent'
                            )
                            fig_pie.update_layout(
                                margin=dict(t=20, b=20, l=0, r=0),
                                height=450,
                                showlegend=True,
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                            
                            # Limpieza de texto usando la misma variable dinámica
                            respuesta_limpia = re.sub(patron_busqueda, '', respuesta_ia, flags=re.DOTALL | re.IGNORECASE)
                            respuesta_limpia = re.sub(r'\{.*?\}', '', respuesta_limpia, flags=re.DOTALL).strip()
                            respuesta_limpia += "\n\n*(Nota: Los porcentajes exactos han sido extraídos al gráfico interactivo superior 👆)*"
                            
                        except Exception as e:
                            st.error(f"Se estructuró la cartera, pero hubo un error generando el gráfico visual: {e}")
                    else:
                        st.warning("⚠️ La IA generó tu perfil pero omitió la tabla de datos matemáticos.")

                    # 2. IMPRIMIR EL ANÁLISIS
                    st.markdown("### 🧠 Análisis del Gestor Cuantitativo y Perfil Psicológico")
                    st.markdown(respuesta_limpia)

            except Exception as e:
                st.error(f"Error general en la ejecución: {e}")

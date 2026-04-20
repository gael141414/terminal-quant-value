import streamlit as st
import random

def ejecutar_apartado_consejos():
    st.markdown("### 🧠 Centro de Mentoría Quant y Modelos Mentales")
    st.markdown("La psicología es el 80% del éxito en la inversión. Revisa estos principios antes de tomar decisiones impulsivas.")
    
    # Base de datos de consejos institucionales
    consejos = [
        {"tipo": "Gestión de Riesgo", "texto": "El objetivo no es ganar mucho dinero rápido, sino sobrevivir lo suficiente para que el interés compuesto haga su magia. Protege siempre tu lado a la baja.", "autor": "Warren Buffett"},
        {"tipo": "Valoración", "texto": "Un gran negocio a un precio terrible es una mala inversión. Exige siempre un Margen de Seguridad de al menos el 30%.", "autor": "Benjamin Graham"},
        {"tipo": "Psicología", "texto": "El mercado es un péndulo que oscila entre el optimismo injustificado y el pesimismo injustificado. Compra a los pesimistas y vende a los optimistas.", "autor": "Howard Marks"},
        {"tipo": "Macroeconomía", "texto": "No intentes adivinar qué hará la economía. Observa dónde está la liquidez de la FED. Si la liquidez baja, sube tu nivel de efectivo.", "autor": "Stanley Druckenmiller"},
        {"tipo": "Técnico/Tendencia", "texto": "Nunca promedies a la baja en una acción que está en tendencia bajista. Promediar perdedores es el camino a la ruina.", "autor": "Paul Tudor Jones"}
    ]
    
    # Consejo Aleatorio Destacado
    consejo_dia = random.choice(consejos)
    
    st.info(f"**💡 Principio Aleatorio:**\n\n*\"{consejo_dia['texto']}\"*\n\n— **{consejo_dia['autor']}** ({consejo_dia['tipo']})")
    
    st.markdown("---")
    st.markdown("#### 🏛️ Los 3 Pilares del Inversor Institucional")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ **QUÉ COMPRAR (Filtro Fundamental)**")
        st.markdown("""
        * Alta rentabilidad sobre el capital (ROIC > 15%).
        * Deuda controlada (Deuda/EBITDA < 3).
        * Ventaja competitiva duradera (Moat).
        """)
        
    with col2:
        st.warning("⏱️ **CUÁNDO COMPRAR (Filtro Valoración)**")
        st.markdown("""
        * Cotiza por debajo de su valor intrínseco (Graham/EPV).
        * PER histórico en su rango bajo (Suelo).
        * Pánico generalizado en su sector.
        """)
        
    with col3:
        st.error("🛡️ **CÓMO PROTEGERSE (Filtro Riesgo)**")
        st.markdown("""
        * No concentres más del 10-15% en una sola acción.
        * Ten coberturas descorrelacionadas (Oro, VIX, Bonos).
        * Mantén liquidez (Cash) si no hay oportunidades.
        """)

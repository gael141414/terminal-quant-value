import streamlit as st
import google.generativeai as genai
import os

def cargar_contexto_real():
    path = "data/brain_context.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Advertencia: El administrador aún no ha descargado la base de datos."

def render_chatbot():
    st.title("🤖 Oráculo Quant - Gestor de Riesgos")
    st.caption("Asesoramiento basado EXCLUSIVAMENTE en Warren Buffett y Fernando (Invertir desde cero).")
    
    # 1. Configurar API
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Falta tu GEMINI_API_KEY en los secrets de Streamlit.")
        return
        
    genai.configure(api_key=api_key)

    # 2. Cargar el "Cerebro" (El archivo de texto súper rápido)
    contexto_videos = cargar_contexto_real()

    # 3. System Prompt con Inyección de Datos (Long-Context RAG)
    system_instruction = f"""
    Eres el 'Oráculo ValueQuant', un Gestor de Riesgos Cuantitativo. 
    Tu regla absoluta e inquebrantable es que tu conocimiento se basa ESTRICTAMENTE en las siguientes transcripciones:
    
    --- INICIO DE BASE DE CONOCIMIENTO ---
    {contexto_videos}
    --- FIN DE BASE DE CONOCIMIENTO ---
    
    REGLAS DE COMPORTAMIENTO:
    1. Si te pregunto algo y la respuesta NO está en el texto anterior, debes responder: "Esa información no está en mis fuentes de referencia de Fernando o Buffett". No te inventes nada.
    2. Cita siempre tus fuentes: "Como explica Fernando en sus vídeos..." o "Siguiendo la filosofía de Warren Buffett...".
    3. Tu tono debe ser analítico, racional y enfocado en la preservación del capital.
    """

    # 4. Inicializar Modelo y Chat usando EXCLUSIVAMENTE las variables 'oraculo'
    if "oraculo_model" not in st.session_state:
        st.session_state.oraculo_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Usamos flash que es súper rápido para leer textos
            system_instruction=system_instruction
        )
        st.session_state.oraculo_chat = st.session_state.oraculo_model.start_chat(history=[])

    if "oraculo_messages" not in st.session_state:
        st.session_state.oraculo_messages = [
            {"role": "assistant", "content": "Hola. He interiorizado todos los vídeos de Invertir desde Cero y la filosofía de Buffett. ¿Qué duda de inversión tienes?"}
        ]

    # 5. Interfaz Visual
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.oraculo_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ej: ¿Qué parámetros debo mirar para saber si una empresa tiene ventaja competitiva?"):
        # Guardar y mostrar pregunta
        st.session_state.oraculo_messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Generar y mostrar respuesta
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Consultando los archivos y vídeos..."):
                    try:
                        # AQUÍ USAMOS LA VARIABLE CORRECTA: oraculo_chat
                        response = st.session_state.oraculo_chat.send_message(prompt)
                        st.markdown(response.text)
                        st.session_state.oraculo_messages.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Error consultando al oráculo: {e}")

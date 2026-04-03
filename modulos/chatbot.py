import streamlit as st
import google.generativeai as genai
import os

def cargar_contexto_real():
    path = "data/brain_context.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "No hay datos de transcripciones disponibles."

def render_chatbot():
    st.title("🦅 ValueQuant - Oráculo de Inversión")
    
    # 1. Configurar API
    api_key = st.secrets.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # 2. Cargar el "Cerebro" (Transcripciones de Fernando y Buffett)
    contexto_videos = cargar_contexto_real()

    # 3. System Prompt con Inyección de Datos
    system_instruction = f"""
    Eres el 'Oráculo ValueQuant'. Tu conocimiento se basa ESTRICTAMENTE en los siguientes textos:
    
    DOCUMENTACIÓN DE REFERENCIA (Transcripciones de Fernando 'Invertir desde Cero' y Filosofía Buffett):
    {contexto_videos}
    
    REGLAS DE COMPORTAMIENTO:
    1. Si la respuesta no se puede deducir de la documentación anterior, di: "Esa información no está en mis fuentes de referencia de Fernando o Buffett".
    2. Cita siempre que puedas: "Como explica Fernando en sus vídeos sobre análisis..." o "Siguiendo la lógica de Warren Buffett...".
    3. Tu tono es técnico, conservador y centrado en el 'Margen de Seguridad'.
    """

    # 4. Inicializar Modelo y Chat
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            system_instruction=system_instruction
        )
        st.session_state.chat_session = st.session_state.gemini_model.start_chat(history=[])

    # 5. Interfaz de Chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("¿Qué diría Fernando sobre el PER de esta empresa?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = st.session_state.chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

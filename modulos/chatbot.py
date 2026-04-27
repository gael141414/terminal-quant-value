# 1. Parche obligatorio para Streamlit Cloud
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

# 2. Imports normales
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

# Obtenemos la API Key de los secrets de Streamlit
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

@st.cache_resource
def cargar_motor_chatbot():
    """Carga la base de datos y el modelo en caché para no recargarlo en cada mensaje"""
    modelo_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vectorstore = Chroma(
        persist_directory="./db_inversion", 
        embedding_function=modelo_embeddings
    )
    
    # Llama 3 ultrarrápido por Groq
    llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.2)

    system_prompt = (
        "Eres un asesor financiero experto e IA de un terminal de inversión de alto nivel. "
        "Tu filosofía de inversión se basa estrictamente en el 'Value Investing' de Warren Buffett "
        "y en las enseñanzas del canal de educación financiera 'Invertir desde 0'. "
        "Utiliza la información de contexto proporcionada para responder a las preguntas de los usuarios. "
        "Si no sabes la respuesta basándote en el contexto, o si te piden especular (ej. trading intradía), "
        "advierte al usuario educadamente basándote en tus principios de inversión en valor.\n\n"
        "Contexto:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    chatbot_chain = create_retrieval_chain(retriever, question_answer_chain)
    return chatbot_chain

def render_chatbot():
    """Esta es la función exacta que tu app.py está buscando importar"""
    st.title("Terminal de Inversión: Asistente Value Investing")
    
    # Cargamos el motor (gracias al caché, esto es instantáneo)
    chatbot_chain = cargar_motor_chatbot()

    # Inicializamos el historial en la memoria de Streamlit
    if "mensajes_ia" not in st.session_state:
        st.session_state.mensajes_ia = []

    # Pintar el historial de mensajes anteriores
    for mensaje in st.session_state.mensajes_ia:
        with st.chat_message(mensaje["rol"]):
            st.markdown(mensaje["contenido"])

    # Caja de texto para que el usuario pregunte
    pregunta = st.chat_input("Pregunta sobre una empresa, valoración, filosofía...")

    if pregunta:
        # 1. Mostrar la pregunta del usuario
        with st.chat_message("user"):
            st.markdown(pregunta)
        st.session_state.mensajes_ia.append({"rol": "user", "contenido": pregunta})

        # 2. Generar y mostrar la respuesta de la IA
        with st.chat_message("assistant"):
            with st.spinner("Analizando con filosofía Value..."):
                # Pedimos la respuesta a LangChain
                respuesta_obj = chatbot_chain.invoke({"input": pregunta})
                texto_respuesta = respuesta_obj['answer']
                
                st.markdown(texto_respuesta)
                
        # 3. Guardar la respuesta en el historial
        st.session_state.mensajes_ia.append({"rol": "assistant", "contenido": texto_respuesta})

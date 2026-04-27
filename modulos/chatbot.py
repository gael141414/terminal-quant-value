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
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2)

    system_prompt = (
        "Eres un asesor financiero experto e IA de un terminal de inversión de alto nivel. "
        "Tu filosofía de inversión se basa estrictamente en el 'Value Investing' de Warren Buffett "
        "y en las enseñanzas de 'Invertir desde 0'. "
        "INSTRUCCIONES DE FORMATO OBLIGATORIAS:\n"
        "1. Sé extremadamente VISUAL. Utiliza tablas en formato Markdown siempre que puedas para comparar datos, métricas o empresas.\n"
        "2. Usa listas con viñetas y texto en negrita para destacar conceptos clave.\n"
        "3. Fundamenta siempre tu respuesta basándote EXCLUSIVAMENTE en el contexto proporcionado.\n"
        "4. Si el usuario pide ejemplos, da nombres reales de empresas a modo didáctico, explicando por qué encajan con la filosofía Value, pero advirtiendo que no es una recomendación de compra.\n\n"
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
            with st.spinner("Analizando documentos e historial Value..."):
                respuesta_obj = chatbot_chain.invoke({"input": pregunta})
                texto_respuesta = respuesta_obj['answer']
                
                # Mostrar la respuesta visual (con tablas y negritas)
                st.markdown(texto_respuesta)
                
                # Novedad: Extraer y mostrar las FUENTES en un desplegable
                if "context" in respuesta_obj and len(respuesta_obj["context"]) > 0:
                    with st.expander("📚 Ver documentos fuente utilizados"):
                        for i, doc in enumerate(respuesta_obj["context"]):
                            # Intentamos sacar el nombre del archivo de los metadatos
                            origen = doc.metadata.get("source", "Documento local")
                            st.caption(f"**Fuente {i+1}:** {origen}")
                            # Mostramos un pequeño fragmento del texto original usado
                            st.text(doc.page_content[:250] + "...")
                
        # 3. Guardar la respuesta en el historial
        st.session_state.mensajes_ia.append({"rol": "assistant", "contenido": texto_respuesta})

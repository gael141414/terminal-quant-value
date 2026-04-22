import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

# La API Key sigue siendo necesaria para que el chatbot "hable"
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

@st.cache_resource
def cargar_motor_chatbot():
    # Usamos el modelo gratuito para LEER la base de datos
    modelo_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    vectorstore = Chroma(
        persist_directory="./db_inversion", 
        embedding_function=modelo_embeddings
    )
    
    # El modelo de chat (el "cerebro" que redacta)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

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

def obtener_respuesta_inversor(pregunta, chatbot_chain):
    respuesta = chatbot_chain.invoke({"input": pregunta})
    return respuesta['answer']

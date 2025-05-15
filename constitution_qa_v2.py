import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
import chromadb
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, UnstructuredFileLoader
from langchain_community.document_loaders import UnstructuredPDFLoader, Docx2txtLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain_community.vectorstores import Chroma

# Constants
DB_DIR = "vectorstore/"
CHAT_COLLECTION = "chat_history"
CONSTITUTION_COLLECTION = "constitution"
UPLOADS_COLLECTION = "uploaded_docs"

# Custom prompt template for Constitution Q&A
CUSTOM_PROMPT = """You are a helpful AI assistant specializing in the Constitution of the Republic of Kazakhstan. Your task is to provide accurate and relevant information.

RULES:
1. Only answer based on the provided content
2. If the answer is not in the documents, say so clearly
3. Use bullet points for structured info
4. Cite article numbers if mentioned
5. Keep a formal and respectful tone

Question: {question}
Context: {context}
Chat History: {chat_history}

Please answer:"""

def initialize_vectorstore(embeddings, collection_name):
    client_settings = chromadb.Settings(
        is_persistent=True,
        persist_directory=DB_DIR,
        anonymized_telemetry=False
    )
    chroma_client = chromadb.PersistentClient(
        path=DB_DIR,
        settings=client_settings
    )

    try:
        collection = chroma_client.get_or_create_collection(name=collection_name)
    except:
        collection = chroma_client.create_collection(name=collection_name)

    return Chroma(
        client=chroma_client,
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=DB_DIR
    )

def store_chat_interaction(vectorstore, question: str, answer: str):
    timestamp = datetime.now().isoformat()
    doc = Document(page_content=f"Q: {question}\nA: {answer}",
                   metadata={"timestamp": timestamp})
    vectorstore.add_documents([doc])

def load_documents(files) -> List[Document]:
    docs = []
    for file in files:
        suffix = Path(file.name).suffix.lower()
        with open(f"temp_{file.name}", "wb") as f:
            f.write(file.read())
        path = f.name

        try:
            if suffix == ".pdf":
                loader = UnstructuredPDFLoader(path)
            elif suffix == ".txt":
                loader = TextLoader(path)
            elif suffix == ".docx":
                loader = Docx2txtLoader(path)
            else:
                continue
            docs.extend(loader.load())
        finally:
            os.remove(path)

    return docs

def process_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(docs)

def main():
    st.set_page_config(page_title="🇰🇿 Kazakhstan Constitution Assistant", layout="wide")
    st.title("🇰🇿 Constitution & Document AI Assistant")

    if "embeddings" not in st.session_state:
        st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if "constitution_vectorstore" not in st.session_state:
        st.session_state.constitution_vectorstore = initialize_vectorstore(st.session_state.embeddings, CONSTITUTION_COLLECTION)
    if "chat_vectorstore" not in st.session_state:
        st.session_state.chat_vectorstore = initialize_vectorstore(st.session_state.embeddings, CHAT_COLLECTION)
    if "uploaded_vectorstore" not in st.session_state:
        st.session_state.uploaded_vectorstore = initialize_vectorstore(st.session_state.embeddings, UPLOADS_COLLECTION)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Constitution Text Input
    st.sidebar.header("📜 Load Constitution")
    constitution_text = st.sidebar.text_area("Paste Constitution Text", height=300)
    if st.sidebar.button("Process Constitution"):
        if constitution_text:
            docs = process_documents([Document(page_content=constitution_text, metadata={"source": "Constitution"})])
            st.session_state.constitution_vectorstore.add_documents(docs)
            st.success("✅ Constitution loaded and embedded!")

    # File Upload Section
    st.sidebar.header("📎 Upload Documents")
    uploaded_files = st.sidebar.file_uploader("Upload files", accept_multiple_files=True, type=["pdf", "txt", "docx"])
    if st.sidebar.button("Process Files"):
        if uploaded_files:
            with st.spinner("Processing uploaded files..."):
                raw_docs = load_documents(uploaded_files)
                processed_docs = process_documents(raw_docs)
                st.session_state.uploaded_vectorstore.add_documents(processed_docs)
                st.success("✅ Files processed and embedded!")
        else:
            st.warning("Please upload at least one document.")

    # Select Document Source
    source_option = st.sidebar.radio("Answer questions using:", ["Constitution", "Uploaded Documents", "Both"])

    # Chat Section
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if question := st.chat_input("Ask a question..."):
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    llm = Ollama(model="mistral")
                    prompt = PromptTemplate(input_variables=["chat_history", "context", "question"], template=CUSTOM_PROMPT)

                    # Choose retriever
                    if source_option == "Constitution":
                        retriever = st.session_state.constitution_vectorstore.as_retriever(search_kwargs={"k": 3})
                    elif source_option == "Uploaded Documents":
                        retriever = st.session_state.uploaded_vectorstore.as_retriever(search_kwargs={"k": 3})
                    else:
                        # Merge both sources
                        retrievers = [
                            st.session_state.constitution_vectorstore.as_retriever(search_kwargs={"k": 2}),
                            st.session_state.uploaded_vectorstore.as_retriever(search_kwargs={"k": 2})
                        ]
                        from langchain.retrievers import MergerRetriever
                        retriever = MergerRetriever(retrievers=retrievers)

                    chain = ConversationalRetrievalChain.from_llm(
                        llm=llm,
                        retriever=retriever,
                        memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer"),
                        combine_docs_chain_kwargs={"prompt": prompt}
                    )

                    response = chain({"question": question})
                    answer = response["answer"]
                    st.write(answer)

                    # Store and append
                    store_chat_interaction(st.session_state.chat_vectorstore, question, answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    error = f"❌ Error: {e}"
                    st.error(error)
                    st.session_state.chat_history.append({"role": "assistant", "content": error})

if __name__ == "__main__":
    main()

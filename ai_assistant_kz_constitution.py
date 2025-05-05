import streamlit as st
import os
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# Set up directories
DATA_PATH = "data/"
DB_PATH = "vectorstores/db/"    

if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

# Initialize LLM
llm = Ollama(model="mistral")

# Initialize embeddings
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Streamlit app
st.title("AI Assistant: Constitution of Kazakhstan")
st.write("Ask questions about the Constitution or upload documents to query their content.")

# File upload
uploaded_files = st.file_uploader(
    "Upload Constitution-related documents (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True
)

# Process uploaded files
def process_files(uploaded_files):
    documents = []
    for uploaded_file in uploaded_files:
        file_path = os.path.join(DATA_PATH, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Load document based on file type
        if uploaded_file.name.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif uploaded_file.name.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif uploaded_file.name.endswith(".txt"):
            loader = TextLoader(file_path)
        else:
            st.error(f"Unsupported file type: {uploaded_file.name}")
            continue
        
        documents.extend(loader.load())
    
    return documents

# Create vector store
def create_vector_db(documents):
    if not documents:
        return None
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    vectorstore = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=DB_PATH
    )
    vectorstore.persist()
    return vectorstore

# Initialize vector store
vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
retriever = vectorstore.as_retriever()

# Create conversational chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory
)

# Handle file uploads
if uploaded_files:
    with st.spinner("Processing uploaded files..."):
        documents = process_files(uploaded_files)
        if documents:
            vectorstore = create_vector_db(documents)
            retriever = vectorstore.as_retriever()
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory
            )
            st.success(f"Processed {len(documents)} document(s). You can now ask questions about the content.")

# Chat interface
st.subheader("Chat with the Assistant")
user_input = st.text_input("Ask a question about the Constitution or uploaded documents:")

if user_input:
    with st.spinner("Generating response..."):
        response = qa_chain({"question": user_input})
        answer = response["answer"]
        st.write(f"**Assistant**: {answer}")
        
        # Store query and answer in ChromaDB
        vectorstore.add_texts(
            texts=[f"Query: {user_input}\nAnswer: {answer}"],
            metadatas=[{"type": "qa_pair"}]
        )
        vectorstore.persist()

# Display conversation history
if memory.chat_memory.messages:
    st.subheader("Conversation History")
    for msg in memory.chat_memory.messages:
        if msg.type == "human":
            st.write(f"**You**: {msg.content}")
        elif msg.type == "ai":
            st.write(f"**Assistant**: {msg.content}")
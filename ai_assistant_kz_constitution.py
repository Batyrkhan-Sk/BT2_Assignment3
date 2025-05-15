import streamlit as st
import os
import logging
import shutil
import requests
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from constitution_reader import fetch_constitution, search_constitution, format_response
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up directories
DATA_PATH = "data/"
DB_PATH = "vectorstores/db/"

def check_internet_connection():
    """Check if there is an active internet connection"""
    try:
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.RequestException:
        return False

def setup_directories():
    """Set up necessary directories"""
    try:
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH)
        if not os.path.exists(DB_PATH):
            os.makedirs(DB_PATH)
    except Exception as e:
        logger.error(f"Error setting up directories: {e}")
        raise

# Initialize directories first
setup_directories()

# Initialize embeddings first since it's needed for vector store
try:
    if not check_internet_connection():
        st.error("""
        No internet connection detected. The application requires an internet connection to download the embedding model.
        
        Please:
        1. Check your internet connection
        2. Make sure you can access https://huggingface.co
        3. Try running the application again
        
        If the problem persists, you can try:
        - Using a different network
        - Checking your firewall settings
        - Running the application with a VPN
        """)
        st.stop()
    
    # Try to initialize embeddings with a timeout
    embeddings = SentenceTransformerEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    # Test the embeddings
    test_embedding = embeddings.embed_query("test")
    if not test_embedding:
        raise Exception("Embedding test failed")
    
except Exception as e:
    logger.error(f"Error initializing embeddings: {e}")
    st.error(f"""
    Error initializing the embedding model: {str(e)}
    
    This could be due to:
    1. Slow or unstable internet connection
    2. Firewall blocking access to huggingface.co
    3. Insufficient disk space
    4. Permission issues
    
    Please try:
    1. Checking your internet connection
    2. Ensuring you have at least 500MB of free disk space
    3. Running the application with administrator privileges
    4. Using a different network or VPN
    
    If the problem persists, please check the logs for more details.
    """)
    st.stop()

# Initialize LLM
try:
    llm = Ollama(model="mistral")
except Exception as e:
    logger.error(f"Error initializing LLM: {e}")
    st.error("""
    Error initializing the language model. Please make sure:
    1. Ollama is installed and running
    2. The mistral model is downloaded (run 'ollama pull mistral')
    3. You have sufficient system resources
    
    To install Ollama:
    1. Visit https://ollama.ai
    2. Download and install for your operating system
    3. Run 'ollama pull mistral' in your terminal
    4. Restart the application
    """)
    st.stop()

# Initialize conversation memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Initialize vector store
try:
    vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=embeddings)
    retriever = vectorstore.as_retriever()
except Exception as e:
    logger.error(f"Error initializing vector store: {e}")
    vectorstore = None
    retriever = None

# Create conversational chain
if retriever:
    try:
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory
        )
    except Exception as e:
        logger.error(f"Error creating conversational chain: {e}")
        qa_chain = None
else:
    qa_chain = None

# Streamlit app
st.title("AI Assistant: Constitution of Kazakhstan")
st.write("Ask questions about the Constitution or upload documents to query their content.")

# File upload
st.subheader("Upload Documents")
uploaded_files = st.file_uploader(
    "Upload Constitution-related documents (PDF, DOCX, TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    help="You can upload multiple files at once or one by one. Supported formats: PDF, DOCX, TXT"
)

# Show uploaded files
if uploaded_files:
    st.write("Uploaded files:")
    for file in uploaded_files:
        st.write(f"- {file.name} ({file.size / 1024:.1f} KB)")

# Process uploaded files
def process_files(uploaded_files):
    documents = []
    processed_files = []
    failed_files = []
    
    for uploaded_file in uploaded_files:
        file_path = os.path.join(DATA_PATH, uploaded_file.name)
        
        # Log file information
        logger.info(f"Processing file: {uploaded_file.name}")
        logger.info(f"File size: {uploaded_file.size} bytes")
        
        try:
            # Save file
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
                failed_files.append((uploaded_file.name, "Unsupported file type"))
                continue
            
            # Load and validate document
            doc = loader.load()
            if not doc:
                logger.error(f"No content extracted from {uploaded_file.name}")
                failed_files.append((uploaded_file.name, "No content extracted"))
                continue
                
            documents.extend(doc)
            processed_files.append(uploaded_file.name)
            logger.info(f"Successfully processed {uploaded_file.name}")
            
        except Exception as e:
            logger.error(f"Error processing {uploaded_file.name}: {e}")
            failed_files.append((uploaded_file.name, str(e)))
    
    return documents, processed_files, failed_files

# Create vector store
def create_vector_db(documents):
    if not documents:
        logger.error("No documents provided to create vector store")
        return None
    
    try:
        # Log document information
        logger.info(f"Creating vector store with {len(documents)} documents")
        for doc in documents:
            logger.info(f"Document metadata: {doc.metadata}")
            logger.info(f"Document length: {len(doc.page_content)} characters")
        
        # Clean up existing vector store
        if os.path.exists(DB_PATH):
            logger.info("Cleaning up existing vector store")
            shutil.rmtree(DB_PATH)
            os.makedirs(DB_PATH)
        
        # Configure text splitter with more detailed settings
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Reduced chunk size for better handling
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            is_separator_regex=False
        )
        
        # Split documents and log information
        texts = text_splitter.split_documents(documents)
        logger.info(f"Split documents into {len(texts)} chunks")
        
        if not texts:
            logger.error("No text chunks generated from documents")
            st.error("""
            No text content could be extracted from the documents. This could be due to:
            1. Empty or corrupted files
            2. Unsupported file formats
            3. Files containing only images or non-text content
            
            Please try:
            1. Checking if the files contain actual text content
            2. Converting files to plain text format
            3. Using different documents
            """)
            return None
        
        # Log chunk information
        for i, chunk in enumerate(texts[:3]):  # Log first 3 chunks
            logger.info(f"Chunk {i} length: {len(chunk.page_content)} characters")
            logger.info(f"Chunk {i} metadata: {chunk.metadata}")
        
        # Create vector store with error handling
        try:
            vectorstore = Chroma.from_documents(
                documents=texts,
                embedding=embeddings,
                persist_directory=DB_PATH
            )
            vectorstore.persist()
            logger.info("Successfully created and persisted vector store")
            return vectorstore
        except Exception as e:
            logger.error(f"Error in Chroma.from_documents: {e}")
            raise
        
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        st.error(f"""
        Error creating vector store: {str(e)}
        
        This could be due to:
        1. Corrupted or unsupported file formats
        2. Files containing non-text content
        3. Memory limitations
        4. Permission issues with the vector store directory
        
        Please try:
        1. Using smaller files (less than 1MB each)
        2. Converting files to plain text format
        3. Ensuring files contain actual text content
        4. Checking file permissions in the vectorstores directory
        
        Technical details:
        - Number of documents: {len(documents)}
        - Vector store path: {DB_PATH}
        - Available disk space: {shutil.disk_usage(DB_PATH).free / (1024*1024):.2f} MB
        """)
        return None

# Handle file uploads
if uploaded_files:
    with st.spinner("Processing uploaded files..."):
        # Check total size of uploaded files
        total_size = sum(f.size for f in uploaded_files)
        if total_size > 10 * 1024 * 1024:  # 10MB limit
            st.error("""
            Total size of uploaded files exceeds 10MB limit.
            Please upload smaller files or fewer files at once.
            """)
        else:
            documents, processed_files, failed_files = process_files(uploaded_files)
            
            # Show processing results
            if processed_files:
                st.success(f"Successfully processed {len(processed_files)} file(s):")
                for file in processed_files:
                    st.write(f"✅ {file}")
            
            if failed_files:
                st.warning(f"Failed to process {len(failed_files)} file(s):")
                for file, error in failed_files:
                    st.write(f"❌ {file}: {error}")
            
            if documents:
                vectorstore = create_vector_db(documents)
                if vectorstore:
                    try:
                        retriever = vectorstore.as_retriever(
                            search_kwargs={"k": 3}  # Retrieve top 3 most relevant chunks
                        )
                        qa_chain = ConversationalRetrievalChain.from_llm(
                            llm=llm,
                            retriever=retriever,
                            memory=memory,
                            return_source_documents=True  # Return source documents for context
                        )
                        st.success("""
                        Documents processed successfully! You can now ask questions about the content.
                        
                        Tips:
                        - Be specific in your questions
                        - Reference specific parts of the documents
                        - Ask follow-up questions for more details
                        """)
                    except Exception as e:
                        logger.error(f"Error setting up document processing: {e}")
                        st.error("""
                        Error processing documents. Please try:
                        1. Using smaller files
                        2. Converting files to plain text format
                        3. Ensuring files contain actual text content
                        """)

# Chat interface
st.subheader("Chat with the Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message["sources"]:
                    st.write(f"Source: {source.metadata.get('source', 'Unknown')}")
                    st.write(f"Content: {source.page_content[:200]}...")

# Chat input
if prompt := st.chat_input("Ask a question about the Constitution or uploaded documents:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            try:
                if uploaded_files and qa_chain:
                    # If documents are uploaded, use the LLM chain
                    response = qa_chain({"question": prompt})
                    answer = response["answer"]
                    sources = response.get("source_documents", [])
                    
                    st.markdown(answer)
                    if sources:
                        with st.expander("View Sources"):
                            for source in sources:
                                st.write(f"Source: {source.metadata.get('source', 'Unknown')}")
                                st.write(f"Content: {source.page_content[:200]}...")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    # If no documents, use the constitution search
                    articles = search_constitution(prompt)
                    answer = format_response(articles, prompt)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                
                # Store query and answer in ChromaDB if vectorstore exists
                if vectorstore:
                    try:
                        vectorstore.add_texts(
                            texts=[f"Query: {prompt}\nAnswer: {answer}"],
                            metadatas=[{"type": "qa_pair", "timestamp": str(datetime.now())}]
                        )
                        vectorstore.persist()
                    except Exception as e:
                        logger.error(f"Error storing QA pair: {e}")
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                error_message = "I apologize, but I encountered an error while processing your request. Please try again."
                st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Add a sidebar with information
with st.sidebar:
    st.header("About")
    st.write("""
    This assistant provides information about the Constitution of Kazakhstan and can answer questions about uploaded documents.
    
    Features:
    - Chat with AI about the Constitution
    - Upload and query documents
    - Store conversation history
    - Context-aware responses
    - Enhanced search capabilities
    """)
    
    st.header("Source")
    st.write("""
    The Constitution data is sourced from the official website of the President of Kazakhstan:
    [Constitution of the Republic of Kazakhstan](https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912)
    """)
    
    st.header("Tips")
    st.write("""
    - Be specific in your questions
    - Use keywords related to your topic
    - For legal matters, refer to specific articles when possible
    - Upload relevant documents for more detailed analysis
    """)
    
    st.header("Troubleshooting")
    st.write("""
    If you encounter issues:
    1. Make sure your documents are in supported formats (PDF, DOCX, TXT)
    2. Check that the documents are not corrupted
    3. Try uploading smaller documents or fewer documents at once
    4. Ensure you have a stable internet connection
    """)
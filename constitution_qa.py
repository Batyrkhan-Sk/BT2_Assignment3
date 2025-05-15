import streamlit as st
import os
import shutil
from pathlib import Path
from datetime import datetime
import chromadb
from typing import List
import re

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
import torch

DB_DIR = "vectorstore/"
CHAT_COLLECTION = "chat_history"
CONSTITUTION_COLLECTION = "constitution"
UPLOADS_COLLECTION = "uploaded_docs"

CUSTOM_PROMPT = """You are a helpful AI assistant specializing in the Constitution of the Republic of Kazakhstan. Your task is to provide accurate and relevant information.

RULES:
1. Only answer based on the provided content
2. If the answer is not in the documents, say so clearly
3. Use bullet points for structured info
4. Cite article numbers if mentioned
5. Keep a formal and respectful tone
6. The Constitution of Kazakhstan has 99 articles. If asked about the number of articles, always answer 99.
7. If asked about a specific article number, look for content labeled with that article number.

Question: {question}
Context: {context}
Chat History: {chat_history}

Please answer:"""

def initialize_vectorstore(embeddings, collection_name):
    os.makedirs(DB_DIR, exist_ok=True)
    
    client_settings = chromadb.Settings(
        is_persistent=True,
        persist_directory=DB_DIR,
        anonymized_telemetry=False
    )
    
    try:
        chroma_client = chromadb.PersistentClient(
            path=DB_DIR,
            settings=client_settings
        )
        try:
            collection = chroma_client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
        except Exception:
            print(f"Creating new collection: {collection_name}")
            collection = chroma_client.create_collection(name=collection_name)

        return Chroma(
            client=chroma_client,
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=DB_DIR
        )
    except Exception as e:
        print(f"Error initializing vectorstore: {e}")
        try:
            print("Attempting to recreate collection...")
            try:
                chroma_client.delete_collection(name=collection_name)
            except:
                pass
            collection = chroma_client.create_collection(name=collection_name)
            return Chroma(
                client=chroma_client,
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=DB_DIR
            )
        except Exception as e2:
            print(f"Failed to recreate collection: {e2}")
            return Chroma(
                collection_name=collection_name,
                embedding_function=embeddings
            )

def store_chat_interaction(vectorstore, question: str, answer: str):
    try:
        timestamp = datetime.now().isoformat()
        doc = Document(page_content=f"Q: {question}\nA: {answer}",
                      metadata={"timestamp": timestamp})
        vectorstore.add_documents([doc])
    except Exception as e:
        print(f"Error storing chat interaction: {e}")

def load_documents(files) -> List[Document]:
    docs = []
    for file in files:
        suffix = Path(file.name).suffix.lower()
        with open(f"temp_{file.name}", "wb") as f:
            f.write(file.read())
        path = f.name

        try:
            if suffix == ".pdf":
                loader = PyMuPDFLoader(path)
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
    for doc in docs:
        if not hasattr(doc, "metadata") or doc.metadata is None:
            doc.metadata = {}
    return docs

def process_constitution_text(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{2,}', '\n\n', text)
    
    print(f"Normalized text (first 500 chars): {text[:500]}")

    patterns = [
        r'Article\s+(\d+)[.\s]*(.*?)(?=\s*Article\s+\d+|$)',
        r'Article\s+(\d+)[.\s]*\n*(.*?)(?=\n\n|$)',
        r'Article\s+(\d+)[.\s]*\n*([^\n]*)(?=\n|$)',
        r'Article\s*(\d+)\s*\.\s*(.*?)(?=\s*Article\s+\d+|$)',
        r'Article\s*(\d+)\s*[\n\s]*(.*?)(?=\s*Article\s+\d+|$)',
        r'Article\s+(\d+)\s*[:\s]*(.*?)(?=\s*Article\s+\d+|$)',
    ]

    processed_docs = []
    found_articles = set()
    
    for pattern in patterns:
        articles = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        for article_num, content in articles:
            if int(article_num) not in found_articles:
                cleaned_content = content.strip()
                cleaned_content = re.sub(r'Note\.\s+.*?(?=\n|$)', '', cleaned_content, flags=re.DOTALL)
                cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
                doc = Document(
                    page_content=f"Article {article_num}. {cleaned_content}",
                    metadata={"source": "Constitution", "article": int(article_num)}
                )
                processed_docs.append(doc)
                found_articles.add(int(article_num))
                if int(article_num) == 93:
                    print(f"Extracted content for Article 93: {cleaned_content[:200]}...")

    if len(found_articles) < 99:
        print(f"Regex found {len(found_articles)} articles, falling back to position-based extraction")
        article_markers = list(re.finditer(r'Article\s+(\d+)', text, re.IGNORECASE))
        if article_markers:
            positions = [(int(m.group(1)), m.start()) for m in article_markers]
            positions.sort(key=lambda x: x[0])
            
            for i, (article_num, start_pos) in enumerate(positions):
                if article_num in found_articles:
                    continue
                if i < len(positions) - 1:
                    end_pos = positions[i + 1][1]
                    content = text[start_pos:end_pos].strip()
                else:
                    content = text[start_pos:].strip()
                
                content = re.sub(r'Article\s+\d+\s*[\.\s:]*', '', content, 1, re.IGNORECASE)
                content = re.sub(r'Note\.\s+.*?(?=\n|$)', '', content, flags=re.DOTALL)
                content = re.sub(r'\s+', ' ', content).strip()
                
                if content:
                    doc = Document(
                        page_content=f"Article {article_num}. {content}",
                        metadata={"source": "Constitution", "article": article_num}
                    )
                    processed_docs.append(doc)
                    found_articles.add(article_num)
                    if article_num == 93:
                        print(f"Position-based extracted content for Article 93: {content[:200]}...")
                else:
                    print(f"Empty content for Article {article_num}, skipping")

    processed_docs.sort(key=lambda x: x.metadata["article"])

    found_nums = [doc.metadata["article"] for doc in processed_docs]
    missing = [i for i in range(1, 100) if i not in found_nums]
    print(f"Extracted {len(found_nums)} articles. Missing articles: {missing}")

    if missing:
        for missing_article in missing:
            snippet_start = text.find(f"Article {missing_article}")
            if snippet_start != -1:
                snippet = text[max(0, snippet_start-100):snippet_start+100]
                print(f"Raw text around missing Article {missing_article}: {snippet}")
            else:
                marker_positions = [m.start() for m in re.finditer(r'Article\s+\d+', text, re.IGNORECASE)]
                for pos in marker_positions:
                    if abs(pos - text.find(str(missing_article))) < 200:
                        snippet = text[max(0, pos-100):pos+100]
                        print(f"Raw text near Article {missing_article}: {snippet}")

    with open("extracted_articles.txt", "w", encoding="utf-8") as f:
        for doc in processed_docs:
            f.write(f"{doc.page_content}\n\n")

    return processed_docs

def load_constitution_from_file():
    constitution_path = "data/akorda.kz-Constitution of the Republic of Kazakhstan.pdf"
    if not os.path.exists(constitution_path):
        print(f"Constitution file not found at {constitution_path}")
        return []

    try:
        loader = PyMuPDFLoader(constitution_path)
        docs = loader.load()
        full_text = "\n".join(doc.page_content for doc in docs)
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = re.sub(r'-\n', '', full_text)
        full_text = re.sub(r'\n+', '\n', full_text)
        full_text = re.sub(r'\f', '\n', full_text)
        full_text = re.sub(r'Constitution of Kazakhstan\s*\d+', '', full_text)
        full_text = re.sub(r'^\d+\s*$', '', full_text, flags=re.MULTILINE)
        article_count = len(re.findall(r'Article\s+\d+', full_text, re.IGNORECASE))
        print(f"PyMuPDFLoader found {article_count} article mentions")
    except Exception as e:
        print(f"PyMuPDFLoader failed: {e}")
        full_text = ""
        article_count = 0

    if article_count < 90:
        print(f"PyMuPDFLoader only found {article_count} articles. Trying UnstructuredPDFLoader...")
        try:
            loader = UnstructuredPDFLoader(constitution_path, strategy="hi_res")
            docs = loader.load()
            full_text = "\n".join(doc.page_content for doc in docs)
            full_text = re.sub(r'\s+', ' ', full_text)
            full_text = re.sub(r'-\n', '', full_text)
            full_text = re.sub(r'\n+', '\n', full_text)
            full_text = re.sub(r'\f', '\n', full_text)
            full_text = re.sub(r'Constitution of Kazakhstan\s*\d+', '', full_text)
            full_text = re.sub(r'^\d+\s*$', '', full_text, flags=re.MULTILINE)
            article_count = len(re.findall(r'Article\s+\d+', full_text, re.IGNORECASE))
            print(f"UnstructuredPDFLoader found {article_count} article mentions")
            print(f"Text around Article 93: {full_text[full_text.find('Article 93')-100:full_text.find('Article 93')+100] if 'Article 93' in full_text else 'Article 93 not found'}")
        except Exception as e:
            print(f"UnstructuredPDFLoader failed: {e}")
            return []

    print(f"Full extracted text (first 2000 chars):\n{full_text[:2000]}")

    processed_docs = process_constitution_text(full_text)
    
    article_nums = [doc.metadata["article"] for doc in processed_docs]
    print(f"Found {len(article_nums)} articles with proper metadata")
    if len(article_nums) < 95:
        missing = [i for i in range(1, 100) if i not in article_nums]
        print(f"Missing articles: {missing}")

    return processed_docs

def main():
    st.set_page_config(page_title="Kazakhstan Constitution Assistant", layout="wide")
    st.title("Constitution & Document AI Assistant")

    if "embeddings" not in st.session_state:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        model = model.to("cpu")
        st.session_state.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"}
        )
        
    try:
        if os.path.exists(DB_DIR):
            try:
                client = chromadb.PersistentClient(path=DB_DIR)
                collections = client.list_collections()
                print(f"Found {len(collections)} existing collections")
            except Exception as e:
                print(f"Error accessing vectorstore, attempting cleanup: {e}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = f"{DB_DIR}_backup_{timestamp}"
                shutil.move(DB_DIR, backup_dir)
                print(f"Moved corrupted vectorstore to {backup_dir}")
                os.makedirs(DB_DIR, exist_ok=True)
    except Exception as e:
        print(f"Error during vectorstore cleanup: {e}")
        
    if "constitution_vectorstore" not in st.session_state:
        st.session_state.constitution_vectorstore = initialize_vectorstore(st.session_state.embeddings, CONSTITUTION_COLLECTION)
        
        try:
            docs = st.session_state.constitution_vectorstore.get()
            if isinstance(docs, dict) and "documents" in docs and len(docs["documents"]) > 0:
                print(f"Constitution vectorstore already has {len(docs['documents'])} documents")
            else:
                print("Loading constitution from file...")
                const_docs = load_constitution_from_file()
                if const_docs:
                    valid_docs = []
                    for doc in const_docs:
                        if isinstance(doc, Document):
                            valid_docs.append(doc)
                        else:
                            print(f"Converting non-Document object to Document")
                            valid_docs.append(Document(page_content=str(doc)))
                    
                    if valid_docs:
                        st.session_state.constitution_vectorstore.add_documents(valid_docs)
                        st.sidebar.success(f"Constitution loaded from PDF file: {len(valid_docs)} documents")
        except Exception as e:
            print(f"Error checking constitution documents: {e}")
            const_docs = load_constitution_from_file()
            if const_docs:
                try:
                    st.session_state.constitution_vectorstore.add_documents(const_docs)
                    st.sidebar.success("Constitution loaded from PDF file")
                except Exception as add_error:
                    print(f"Error adding constitution documents: {add_error}")
            
    if "chat_vectorstore" not in st.session_state:
        st.session_state.chat_vectorstore = initialize_vectorstore(st.session_state.embeddings, CHAT_COLLECTION)
    if "uploaded_vectorstore" not in st.session_state:
        st.session_state.uploaded_vectorstore = initialize_vectorstore(st.session_state.embeddings, UPLOADS_COLLECTION)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.sidebar.header("Load Constitution")
    constitution_text = st.sidebar.text_area("Paste Constitution Text", height=300)
    if st.sidebar.button("Process Constitution"):
        if constitution_text:
            docs = process_constitution_text(constitution_text)
            st.session_state.constitution_vectorstore.add_documents(docs)
            st.success(f"Constitution loaded and embedded! {len(docs)} articles processed.")

    st.sidebar.header("Upload Documents")
    uploaded_files = st.sidebar.file_uploader("Upload files", accept_multiple_files=True, type=["pdf", "txt", "docx"])
    if st.sidebar.button("Process Files"):
        if uploaded_files:
            with st.spinner("Processing uploaded files..."):
                raw_docs = load_documents(uploaded_files)
                processed_docs = process_documents(raw_docs)
                st.session_state.uploaded_vectorstore.add_documents(processed_docs)
                st.success("Files processed and embedded!")
        else:
            st.warning("Please upload at least one document.")

    source_option = st.sidebar.radio("Answer questions using:", ["Constitution", "Uploaded Documents", "Both"])

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

                    article_match = re.search(r'article\s+(\d+)', question.lower())
                    article_num = int(article_match.group(1)) if article_match else None

                    if source_option == "Constitution":
                        vectorstore = st.session_state.constitution_vectorstore
                    elif source_option == "Uploaded Documents":
                        vectorstore = st.session_state.uploaded_vectorstore
                    else:
                        const_retriever = st.session_state.constitution_vectorstore.as_retriever(search_kwargs={"k": 3})
                        uploaded_retriever = st.session_state.uploaded_vectorstore.as_retriever(search_kwargs={"k": 2})
                        from langchain.retrievers import MergerRetriever
                        vectorstore = None
                        retriever = MergerRetriever(retrievers=[const_retriever, uploaded_retriever])

                    if source_option in ["Constitution", "Both"]:
                        if article_num and vectorstore:
                            try:
                                retriever = vectorstore.as_retriever(
                                    search_type="similarity",
                                    search_kwargs={"k": 5, "filter": {"article": article_num}}
                                )
                                retrieved_docs = retriever.get_relevant_documents(question)
                                if not retrieved_docs:
                                    print(f"No documents found for Article {article_num} using metadata filter. Falling back to similarity search.")
                                    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
                                    retrieved_docs = retriever.get_relevant_documents(f"Article {article_num}")
                                    retrieved_docs = [doc for doc in retrieved_docs if f"Article {article_num}" in doc.page_content]
                                    if not retrieved_docs:
                                        print(f"No documents found for Article {article_num} even after content search.")
                            except Exception as e:
                                print(f"Error with metadata filter for Article {article_num}: {e}")
                                retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
                                retrieved_docs = retriever.get_relevant_documents(question)
                        else:
                            retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) if vectorstore else retriever
                    else:
                        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

                    if article_num:
                        retrieved_docs = retriever.get_relevant_documents(question)
                        print(f"Retrieved {len(retrieved_docs)} documents for Article {article_num} query")
                        for i, doc in enumerate(retrieved_docs):
                            print(f"Doc {i+1} - Article in metadata: {doc.metadata.get('article')}")
                            print(f"Doc {i+1} - Full content: {doc.page_content}")

                    chain = ConversationalRetrievalChain.from_llm(
                        llm=llm,
                        retriever=retriever,
                        memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer"),
                        combine_docs_chain_kwargs={"prompt": prompt}
                    )

                    response = chain({"question": question})
                    answer = response["answer"]
                    st.write(answer)

                    store_chat_interaction(st.session_state.chat_vectorstore, question, answer)
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                except Exception as e:
                    error = f"Error: {e}"
                    st.error(error)
                    st.session_state.chat_history.append({"role": "assistant", "content": error})

if __name__ == "__main__":
    main()
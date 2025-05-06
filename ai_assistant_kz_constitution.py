import streamlit as st
import os
from constitution_reader import fetch_constitution, search_constitution, format_response

# Set up directories
DATA_PATH = "data/"
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# Streamlit app
st.title("AI Assistant: Constitution of Kazakhstan")
st.write("Ask questions about the Constitution of Kazakhstan")

# Initialize constitution data
@st.cache_resource
def load_constitution():
    return fetch_constitution()

# Load constitution data
constitution_data = load_constitution()

# Chat interface
st.subheader("Chat with the Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the Constitution of Kazakhstan"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching the Constitution..."):
            articles = search_constitution(prompt)
            response = format_response(articles, prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Add a sidebar with information
with st.sidebar:
    st.header("About")
    st.write("""
    This assistant provides information about the Constitution of Kazakhstan.
    You can ask questions about:
    - Rights and freedoms
    - Government structure
    - State principles
    - Specific articles or provisions
    """)
    
    st.header("Source")
    st.write("""
    The Constitution data is sourced from the official website of the President of Kazakhstan:
    [Constitution of the Republic of Kazakhstan](https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912)
    """)
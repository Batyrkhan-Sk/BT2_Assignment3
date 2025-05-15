# Document Q&A Assistant

A powerful document question-answering system that allows users to upload documents and ask questions about their content. The system uses advanced language models and vector storage to provide accurate answers based on the document content.

## Features

- 📁 Support for multiple document formats (PDF, DOCX, TXT)
- 💬 Interactive chat interface using Streamlit
- 🤖 Powered by Ollama with the Mistral model
- 📚 Vector storage using ChromaDB for efficient document retrieval
- 🔄 Ability to upload multiple documents simultaneously
- 💾 Persistent storage of processed documents
- 📝 Maintains chat history for context

## Requirements

- Python 3.8+
- Ollama installed and running locally (with the Mistral model)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Ensure Ollama is installed and the Mistral model is available:
```bash
ollama pull mistral
```

## Usage

1. Start the application:
```bash
streamlit run document_qa.py
```

2. Upload your documents:
   - Click the "Upload your documents" button in the sidebar
   - Select one or multiple files (PDF, DOCX, or TXT)
   - Wait for the documents to be processed

3. Ask questions:
   - Type your question in the chat input at the bottom
   - The system will provide answers based on the content of your uploaded documents
   - The chat history will be maintained for context

## Supported File Types

- PDF documents (*.pdf)
- Word documents (*.docx)
- Text files (*.txt)

## Notes

- The system maintains a vector store of processed documents for efficient retrieval
- Documents are processed only once and stored for future use
- The chat interface maintains context through conversation history
- All answers are derived directly from the uploaded documents

## Error Handling

The application includes robust error handling for:
- File processing issues
- LLM initialization problems
- Vector store operations
- Invalid file types
- Network connectivity issues

## Directory Structure

- `uploads/`: Temporary storage for uploaded files
- `vectorstore/`: Persistent storage for processed documents
- `document_qa.py`: Main application file
- `requirements.txt`: Python dependencies

# Constitution Q&A Assistant 🇰🇿

An AI-powered application for querying the Constitution of the Republic of Kazakhstan and other documents using natural language questions.

## Features

- 📚 Load and query the Constitution of Kazakhstan
- 📄 Upload and process multiple document types (PDF, DOCX, TXT)
- 💬 Interactive chat interface
- 🔍 Smart document search and retrieval
- 💾 Persistent storage of processed documents
- 🤖 Powered by Mistral LLM through Ollama

## Prerequisites

- Python 3.9+
- Ollama installed with Mistral model
- macOS/Linux environment

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install and start Ollama with Mistral model:
```bash
# Install Ollama from: https://ollama.ai/
ollama pull mistral
```

## Usage

1. Start the application:
```bash
streamlit run constitution_qa_v2.py
```

2. Load the Constitution:
   - Copy the Constitution text from [official source](https://www.akorda.kz/en/constitution-of-the-republic-of-kazakhstan-50912)
   - Paste it into the sidebar text area
   - Click "Process Constitution"

3. Upload additional documents (optional):
   - Use the file uploader in the sidebar
   - Support for PDF, DOCX, and TXT files
   - Click "Process Files" after uploading

4. Ask questions:
   - Choose the source (Constitution/Uploaded Documents/Both)
   - Type your question in the chat input
   - View answers with relevant context

## Project Structure

```
.
├── constitution_qa_v2.py    # Main application file
├── requirements.txt         # Python dependencies
├── vectorstore/            # Persistent storage for embeddings
└── uploads/               # Temporary storage for uploaded files
```

## Technical Details

- **Frontend**: Streamlit
- **LLM**: Mistral (via Ollama)
- **Vector Store**: ChromaDB
- **Embeddings**: HuggingFace Sentence Transformers
- **Document Processing**: LangChain

## Error Handling

The application includes comprehensive error handling for:
- File uploads
- Document processing
- LLM interactions
- Vector store operations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

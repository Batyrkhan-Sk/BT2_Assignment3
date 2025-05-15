# BT2_Assignment3
📘 Project Overview
This project is an intelligent assistant designed to analyze and process the text of the Constitution of the Republic of Kazakhstan. By leveraging natural language processing (NLP) techniques and vector storage, the assistant can answer questions related to the constitution's content.

🧠 Key Features
Loading and preprocessing the constitution text.

Extracting and structuring data from the constitutional text.

Creating a vector store for efficient information retrieval.

Interactive interface for querying the assistant and obtaining answers.

🗂️ Project Structure
ai_assistant_kz_constitution.py — Main module of the assistant.

constitution_reader.py — Script for reading and processing the constitution text.

download_nltk_data.py — Script to download necessary NLTK data.

test_ollama.py and test_ollama_detailed.py — Test scripts to verify assistant functionality.

constitution.json — Structured file containing constitution data.

requirements.txt — List of project dependencies.

data/ and vectorstores/db/ — Directories for storing data and vector representations.

⚙️ Installation and Usage
Clone the repository:

bash
Copy
Edit
git clone https://github.com/Batyrkhan-Sk/BT2_Assignment3.git
cd BT2_Assignment3
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Download necessary NLTK data:

bash
Copy
Edit
python download_nltk_data.py
Run the assistant:

bash
Copy
Edit
python ai_assistant_kz_constitution.py
👥 Authors
Batyrkhan-Sk

GazizaTan

Rudswoods1


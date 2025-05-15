# BT2\_Assignment3

## 📘 Project Overview

**BT2\_Assignment3** is an AI assistant trained on the Constitution of the Republic of Kazakhstan. Built with Python, it leverages natural language processing libraries to analyze and interact with the constitutional text.

## 📁 Repository Structure

```plaintext
├── ai_assistant_kz_constitution.py       # Main AI assistant script
├── constitution_reader.py                # Module for reading and processing the Constitution text
├── download_nltk_data.py                 # Script to download necessary NLTK data
├── test_ollama.py                        # Test script for functionality
├── test_ollama_detailed.py               # Detailed test script
├── constitution.json                     # Constitution text in JSON format
├── constitution (1-я копия).txt          # Constitution text in TXT format
├── requirements.txt                      # List of project dependencies
├── data/                                 # Directory for storing data
└── vectorstores/db/                      # Directory for storing vector representations
```



## ⚙️ Installation and Execution

### 🔧 Prerequisites

* Python 3.8 or higher
* pip (Python package manager)




### 🪟 Windows

1. **Install Python**:

   * Download the installer from the [official website](https://www.python.org/downloads/windows/).
   * During installation, ensure you check the box "Add Python to PATH".

2. **Clone the repository**:

   ```bash
   git clone https://github.com/Batyrkhan-Sk/BT2_Assignment3.git
   cd BT2_Assignment3
   ```



3. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```



4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```



5. **Run the script**:

   ```bash
   python ai_assistant_kz_constitution.py
   ```





### 🐧 Arch Linux with Hyprland

1. **Install Python and pip** (if not already installed):

   ```bash
   sudo pacman -S python python-pip
   ```



2. **Clone the repository**:

   ```bash
   git clone https://github.com/Batyrkhan-Sk/BT2_Assignment3.git
   cd BT2_Assignment3
   ```


3. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```


4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```


5. **Run the script**:

   ```bash
   python ai_assistant_kz_constitution.py
   ```




### 🍎 macOS

1. **Install Homebrew** (if not already installed):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```



2. **Install Python**:

   ```bash
   brew install python
   ```



3. **Clone the repository**:

   ```bash
   git clone https://github.com/Batyrkhan-Sk/BT2_Assignment3.git
   cd BT2_Assignment3
   ```



4. **Create a virtual environment** (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```



6. **Run the script**:

   ```bash
   python ai_assistant_kz_constitution.py
   ```



## 🧪 Testing

To run the test scripts, execute the following commands:

```bash
python test_ollama.py
python test_ollama_detailed.py
```



## 📄 License

This project is licensed under the MIT License.

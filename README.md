# 🤖 Local RAG Assistant

A local Retrieval-Augmented Generation (RAG) application built with Python, Flask, SQLite, and Microsoft Foundry Local.


## Features

* 📄 Upload and manage multiple PDF documents 
* ✂️ Page-aware, sentence-based text chunking
* 🔍 Semantic retrieval using Qwen3-embedding and cosine similarity
* 🤖 Local AI answers using Phi-3.5-mini
* 📌 Source file and page number shown for every answer
* 🚫 Automatically rejects questions unrelated to the uploaded documents
* 🖥️ Custom web interface built with HTML, CSS, and JavaScript


## Technologies

* Python
* Flask
* SQLite
* PyPDF
* Microsoft Foundry Local
* HTML / CSS / JavaScript


## Installation
```
git clone https://github.com/peri-ctly/LOCALRAG.git
cd LOCALRAG
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

python app.py

Then open http://127.0.0.1:5001 in your browser.


## Example

1. Upload one or more PDF documents.
2. Ask questions about the uploaded documents.
3. The assistant retrieves the most relevant chunks using cosine similarity.
4. Phi-3.5-mini generates an answer using only the retrieved context, and cites the source file and page number.
5. If the answer is not found in the documents, it responds: "The answer is not available in the provided context."


## How It Works

```
[User Question]
      │
      ▼
[Embedding Model: qwen3-embedding-0.6b] ────► [SQLite: localDB.db]
                                                      │
                                                      ▼ (Top Relevant Chunks,
                                                          via cosine similarity)
                                                      │
                                                      ▼
                                        [Local LLM: phi-3.5-mini]
                                                      │
                                                      ▼
                                      [Grounded Answer + Source + Page]
```

## Project Structure
```
LocalRAG/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── chunker.py
│   ├── database.py
│   ├── embedding.py
│   ├── foundry.py
│   ├── pdf_loader.py
│   ├── retriever.py
│   └── chat.py
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    └── index.html
```

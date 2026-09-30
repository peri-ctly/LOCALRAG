
"""
Flask server for the Local RAG Assistant.
"""

import os
import time

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from src.pdf_loader import load_pdf_pages
from src.chunker import create_chunks
from src.embedding import create_embeddings

from src.database import (
    create_database,
    save_documents,
    delete_document,
    get_document_names
)

from src.retriever import (
    retrieve_best_chunk,
    set_cached_documents,
    refresh_cache_from_database,
    get_documents
)

from src.chat import generate_answer


app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024 

UNAVAILABLE_MESSAGE = "The answer is not available in the provided context."
RETRIEVAL_THRESHOLD = 0.45
MAX_DOCUMENTS = 5
MAX_TOTAL_CHUNKS = 500

create_database()

try:
    refresh_cache_from_database()
except Exception as error:
    print("Initial cache refresh failed:", error)


def get_answer_sources(answer, selected_sources):
    
    if not answer or UNAVAILABLE_MESSAGE.lower() in answer.lower():
        return []

    unique_sources, seen = [], set()

    for source in selected_sources:
        key = (source.get("document_name"), source.get("page_number"))
        if key in seen:
            continue
        seen.add(key)
        unique_sources.append(source)

    return unique_sources


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/documents", methods=["GET"])
def documents():
    try:
        return jsonify({"documents": get_document_names()})
    except Exception as error:
        print("Document list error:", error)
        return jsonify({"documents": []}), 500


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()

    if not question:
        return jsonify({"answer": "Please enter a question."}), 400

    if not get_document_names():
        return jsonify({"answer": "⚠ Please upload a PDF before asking a question."}), 400

    print("\nQuestion:", question)
    retrieval_start = time.time()

    context, context_embeddings, retrieval_score, selected_sources = retrieve_best_chunk(question)

    print(f"Retrieve Time: {time.time() - retrieval_start:.2f} seconds")
    print(f"Best Retrieval Score: {retrieval_score:.4f}")

    if context is None or retrieval_score < RETRIEVAL_THRESHOLD:
        return jsonify({"answer": UNAVAILABLE_MESSAGE, "sources": []})

    generation_start = time.time()
    answer = generate_answer(question, context)
    print(f"Generate Time: {time.time() - generation_start:.2f} seconds")

    return jsonify({"answer": answer, "sources": get_answer_sources(answer, selected_sources)})


@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"message": "No PDF file selected."}), 400

    file = request.files["file"]

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"message": "No PDF file selected."}), 400

    filename = secure_filename(file.filename)
    upload_folder = "docs"
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)

    try:
        file.save(file_path)
        load_start = time.time()
        pages = load_pdf_pages(file_path)
        print(f"PDF load time: {time.time() - load_start:.2f}s ({len(pages)} pages)")

        if not pages:
            return jsonify({"message": "No readable text was found in the PDF."}), 400

        chunk_start = time.time()
        chunks = create_chunks(pages)
        print(f"Chunking time: {time.time() - chunk_start:.2f}s ({len(chunks)} chunks)")

        if not chunks:
            return jsonify({"message": "No usable text was found in the PDF."}), 400
        
        if len(get_document_names()) >= MAX_DOCUMENTS:
            return jsonify({
                "message": f"Maximum of {MAX_DOCUMENTS} PDFs reached. Remove one before adding another."
            }), 400

        existing_chunk_count = len(get_documents())

        if existing_chunk_count + len(chunks) > MAX_TOTAL_CHUNKS:
            return jsonify({
                "message": f"This PDF would exceed the system's total capacity ({MAX_TOTAL_CHUNKS} chunks). Remove some documents first or upload a smaller PDF."
            }), 400


        chunk_texts = [chunk["text"] for chunk in chunks]
        embed_start = time.time()
        embeddings = create_embeddings(chunk_texts)
        print(f"Embedding time: {time.time() - embed_start:.2f}s ({len(embeddings)} embeddings)")

        create_database()
        save_documents(chunks, embeddings, document_name=filename)
        set_cached_documents(chunks, embeddings, document_name=filename)

        return jsonify({
            "message": f"{filename} uploaded and indexed successfully.",
            "documents": get_document_names()
        })

    except Exception as error:
        print("Upload error:", error)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        return jsonify({"message": "An error occurred while processing the PDF."}), 500


@app.route("/delete/<path:document_name>", methods=["DELETE"])
def delete_pdf(document_name):
    document_name = secure_filename(document_name)

    if not document_name:
        return jsonify({"message": "Invalid document name."}), 400

    try:
        deleted_count = delete_document(document_name)

        if deleted_count == 0:
            return jsonify({"message": "Document not found."}), 404

        file_path = os.path.join("docs", document_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as error:
                print("File delete warning:", error)

        refresh_cache_from_database()

        return jsonify({
            "message": f"{document_name} removed successfully.",
            "documents": get_document_names()
        })

    except Exception as error:
        print("Delete error:", error)
        return jsonify({"message": "An error occurred while removing the PDF."}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)

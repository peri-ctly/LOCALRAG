
"""
Stores and retrieves PDF chunks, metadata, and embeddings using SQLite.
"""

import json
import sqlite3


DATABASE_NAME = "localDB.db"


# Database connection

def get_connection():
    """
    Creates a SQLite connection.

    A small helper keeps connection creation consistent.
    """

    return sqlite3.connect(
        DATABASE_NAME
    )


# Database creation / migration

def create_database():
    """
    Creates the documents table if it does not exist.

    The database supports multiple PDF documents.

    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_name TEXT NOT NULL DEFAULT '',
            page_number INTEGER NOT NULL DEFAULT 1,
            chunk_index INTEGER NOT NULL,
            chunk TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
        """
    )

    # Existing database migration
   
    cursor.execute( "PRAGMA table_info(documents)")

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    if "document_name" not in existing_columns:

        cursor.execute(
            """
            ALTER TABLE documents
            ADD COLUMN document_name TEXT
            NOT NULL DEFAULT ''
            """
        )

    if "page_number" not in existing_columns:

        cursor.execute(
            """
            ALTER TABLE documents
            ADD COLUMN page_number INTEGER
            NOT NULL DEFAULT 1
            """
        )

    connection.commit()

    connection.close()


# Save / update one PDF
def save_documents( chunks, embeddings, document_name="" ):
    """
    Saves one PDF's chunks and embeddings.

    IMPORTANT:
    Existing data belonging to the same document name is
    replaced, but other PDF documents remain untouched.

    This enables multiple PDFs to coexist in the database.
    """

    create_database()

    connection = get_connection()

    cursor = connection.cursor()


    # Replace only this document

    cursor.execute(
        """
        DELETE FROM documents
        WHERE document_name = ?
        """,
        (
            document_name,
        )
    )


    # Insert new chunks

    for chunk_data, embedding in zip( chunks,embeddings ):

        cursor.execute(
            """
            INSERT INTO documents(
                document_name,
                page_number,
                chunk_index,
                chunk,
                embedding
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                document_name,
                chunk_data["page_number"],
                chunk_data["chunk_index"],
                chunk_data["text"],
                json.dumps(
                    embedding
                )
            )
        )

    connection.commit()

    connection.close()


# Delete one PDF

def delete_document( document_name ):
    """
    Deletes only one PDF document and its chunks.

    Returns:
        number of deleted rows
    """

    create_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM documents
        WHERE document_name = ?
        """,
        (
            document_name,
        )
    )

    deleted_count = (
        cursor.rowcount
    )

    connection.commit()

    connection.close()

    return deleted_count



# Delete all PDFs

def delete_documents():
    """
    Deletes all indexed PDF documents.

    Kept for compatibility and full database reset.
    """

    create_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM documents"
    )

    connection.commit()

    connection.close()


# List indexed PDFs
def get_document_names():
    """
    Returns the names of all indexed PDF documents.
    """

    create_database()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT document_name
        FROM documents
        WHERE document_name != ''
        ORDER BY document_name
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


    
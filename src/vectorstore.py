import os
import shutil
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "chroma_db"
DOC_PATH = os.path.join("data", "help_docs.md")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_embeddings() -> HuggingFaceEmbeddings:
    """Initializes the local HuggingFace embedding model."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def build_vectorstore() -> Chroma:
    """
    Parses Markdown policy documents by header levels, builds a 
    persistent Chroma vectorstore, and stores embeddings locally.
    """
    if not os.path.exists(DOC_PATH):
        raise FileNotFoundError(f"Documentation file not found: {DOC_PATH}")

    with open(DOC_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Split document cleanly on Markdown header levels
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        strip_headers=False
    )
    docs = markdown_splitter.split_text(md_text)

    # Clean existing database to prevent duplicate stale embeddings
    if os.path.exists(CHROMA_PATH):
        try:
            shutil.rmtree(CHROMA_PATH)
        except PermissionError:
            pass

    embeddings = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    print(f"Indexed {len(docs)} policy chunks into ChromaDB at '{CHROMA_PATH}'.")
    return vectorstore

def get_vectorstore() -> Chroma:
    """Returns the existing Chroma vectorstore or builds it if not present."""
    if not os.path.exists(CHROMA_PATH):
        return build_vectorstore()
    return Chroma(
        persist_directory=CHROMA_PATH, 
        embedding_function=get_embeddings()
    )

def get_retriever(k: int = 3):
    """Returns a retriever instance for similarity search."""
    return get_vectorstore().as_retriever(search_kwargs={"k": k})

# Aliases for backward compatibility across test files and scripts
get_vector_store = get_vectorstore
build_vector_store = build_vectorstore

if __name__ == "__main__":
    build_vectorstore()
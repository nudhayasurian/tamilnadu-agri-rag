
from pathlib import Path

from langchain_community.vectorstores import FAISS

from src.embeddings import get_embeddings
from src.pdf_loader import extract_pdf
from src.splitter import split_documents


INDEX_DIR = Path("indexes/faiss")


def build_index():
    '''documents = []'''
    documents = extract_pdf(pdf_path)  # Now includes OCR

    for pdf_path in Path("data/raw").glob("*.pdf"):
        try:
            documents.extend(
                extract_pdf(str(pdf_path))
            )
            print("Loaded:", pdf_path.name)
        except Exception as exc:
            print("Failed:", pdf_path.name, exc)

    if not documents:
        raise ValueError(
            "No extractable PDF content found."
        )

    chunks = split_documents(documents)
    print("Total chunks:", len(chunks))

    embeddings = get_embeddings()

    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store.save_local(str(INDEX_DIR))

    print("FAISS index saved to:", INDEX_DIR)


def search_index(query: str, k: int = 5):
    embeddings = get_embeddings()

    if not INDEX_DIR.exists():
        raise FileNotFoundError(
            "Run the index command first."
        )

    # Only load locally generated indexes you trust.
    vector_store = FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )

    results = vector_store.similarity_search_with_score(
        query,
        k=k,
    )

    for document, distance in results:
        print("\n--- RESULT ---")
        print("Distance:", distance)
        print("Source:", document.metadata["source"])
        print("Page:", document.metadata["page"])
        print("Text:", document.page_content[:700])


if __name__ == "__main__":
    build_index()

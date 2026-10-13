
from pathlib import Path

import fitz
from langchain_core.documents import Document


def extract_pdf(pdf_path: str) -> list[Document]:
    documents = []
    path = Path(pdf_path)

    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": str(path),
                        "title": path.name,
                        "page": page_number,
                        "modality": "pdf",
                    },
                )
            )

    return documents


if __name__ == "__main__":
    docs = extract_pdf("data/raw/TNSchemes.pdf")

    print("Extracted pages:", len(docs))

    for doc in docs:
        print("Page:", doc.metadata["page"])
        print(doc.page_content[:500])

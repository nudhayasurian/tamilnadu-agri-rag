
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            "।",
            "। ",
            ". ",
            "? ",
            "! ",
            " ",
            "",
        ],
        add_start_index=True,
    )

    return splitter.split_documents(documents)


if __name__ == "__main__":
    from src.pdf_loader import extract_pdf

    documents = extract_pdf("data/raw/TNSchemes.pdf")
    chunks = split_documents(documents)

    print("Total chunks:", len(chunks))

    for i, chunk in enumerate(chunks):
        print(f"\nCHUNK {i + 1}")
        print("Page:", chunk.metadata["page"])
        print("Characters:", len(chunk.page_content))
        print(chunk.page_content[:250])

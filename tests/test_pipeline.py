
import fitz

from src.pdf_loader import extract_pdf
from src.splitter import split_documents


def test_pdf_extraction(tmp_path):
    path = tmp_path / "test.pdf"

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text(
        (72, 72),
        "Agriculture irrigation subsidy",
    )
    pdf.save(path)
    pdf.close()

    documents = extract_pdf(str(path))

    assert len(documents) == 1
    assert "irrigation" in documents[0].page_content
    assert documents[0].metadata["page"] == 1


def test_text_splitting():
    from langchain_core.documents import Document

    document = Document(
        page_content=(
            "Agriculture subsidy and irrigation. " * 100
        ),
        metadata={"source": "fixture"},
    )

    chunks = split_documents([document])

    assert len(chunks) > 1
    assert all(len(c.page_content) <= 1000 for c in chunks)
    assert all(c.metadata["source"] == "fixture" for c in chunks)


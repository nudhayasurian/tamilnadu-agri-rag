
import os
from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image


# Configure Tesseract executable location
TESSERACT_PATH = os.getenv(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def ocr_pdf_page(
    page,
    dpi=300,
    language="tam+eng"
):
    """
    Perform Tamil and English OCR on a PDF page.

    Args:
        page: PyMuPDF page object
        dpi: Image resolution
        language: Tesseract language configuration

    Returns:
        Extracted text as a string
    """

    # Step 1: Convert PDF page into an image
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(dpi / 72, dpi / 72),
        alpha=False
    )

    # Step 2: Convert image bytes to PIL Image
    image = Image.open(
        BytesIO(pix.tobytes("png"))
    )

    # Step 3: Perform OCR
    text = pytesseract.image_to_string(
        image,
        lang=language,
        config="--psm 3",
        timeout=120
    )

    return text.strip()


if __name__ == "__main__":
    print("Tesseract executable:", TESSERACT_PATH)

    print(
        "Available OCR languages:",
        pytesseract.get_languages(config="")
    )

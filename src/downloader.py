
import asyncio
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import fitz
import httpx


OUTPUT_DIR = Path("data/raw")
MAX_PDFS = 100
MAX_BYTES = 50 * 1024 * 1024


async def download_pdfs(urls):
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    hashes = set()
    downloaded = 0

    # Identify PDFs that were already downloaded.
    for existing in OUTPUT_DIR.glob("*.pdf"):
        data = existing.read_bytes()
        hashes.add(hashlib.sha256(data).hexdigest())

    async with httpx.AsyncClient(
        follow_redirects=False,
        timeout=60,
    ) as client:
        for url in urls:
            if downloaded >= MAX_PDFS:
                break

            try:
                parsed = urlparse(url)

                if parsed.scheme != "https":
                    continue

                # Limit downloads to the approved host.
                # Replace with the actual reviewed hostname.
                approved_hosts = {
                    "agritech.tnau.ac.in"
                }
                parsed = urlparse(url)

                if parsed.scheme != "https":
                    print(f"SKIPPED - Non-HTTPS URL: {url}")
                    continue

                if parsed.hostname not in approved_hosts:
                    print(f"SKIPPED - Host not approved: {url}")
                    continue

                response = await client.get(url)
                response.raise_for_status()

                data = response.content

                if len(data) > MAX_BYTES:
                    print("File too large:", url)
                    continue

                if not data.startswith(b"%PDF-"):
                    print("Not a PDF:", url)
                    continue

                try:
                    with fitz.open(
                        stream=data,
                        filetype="pdf",
                    ) as pdf:
                        if pdf.page_count < 1:
                            raise ValueError("Empty PDF")
                except Exception:
                    print("Invalid or corrupt PDF:", url)
                    continue

                content_hash = hashlib.sha256(
                    data
                ).hexdigest()

                if content_hash in hashes:
                    print("Duplicate:", url)
                    continue

                filename = f"{content_hash[:20]}.pdf"
                destination = OUTPUT_DIR / filename

                destination.write_bytes(data)

                hashes.add(content_hash)
                downloaded += 1

                print(f"Downloaded {downloaded}: {filename}")

                await asyncio.sleep(1.5)

            except Exception as exc:
                print("Download failed:", url, exc)

    print("New PDFs downloaded:", downloaded)


async def main():
    path = Path("data/processed/pdf_urls.txt")

    urls = [
        line.strip()
        for line in path.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]
    print(f"PDF URLs found in input file: {len(urls)}")
    await download_pdfs(urls)


if __name__ == "__main__":
    asyncio.run(main())

# Tamil Nadu Agriculture PDF Search

A Python project for semantic search over Tamil Nadu agriculture scheme PDFs. It extracts document passages, creates OpenAI embeddings, stores them in a local FAISS index, and exposes search through a CLI, FastAPI API, and Streamlit interface.

The current application retrieves matching passages with document metadata; it does not generate answers with a language model.

## Features

- PDF text extraction with PyMuPDF and one-based page references.
- Text chunks of up to 1,000 characters with 150-character overlap.
- OpenAI embeddings, defaulting to `text-embedding-3-small`.
- Local FAISS similarity search using squared L2 distance (lower is closer).
- API results containing passage text, title, document ID, page, and available source metadata.
- Streamlit search interface with result counts, distance filtering, and session search history.
- Optional PDF discovery and downloading utilities.
- A standalone Tamil/English OCR helper.

## Requirements

- Python 3.10 or newer (the code uses Python 3.10 type syntax).
- An OpenAI API key and network access for embedding requests. Index building, API startup validation, and searches make embedding API calls.
- Text-based PDFs in `data/raw/`, or an existing compatible LangChain FAISS index.
- Chromium through Playwright if using the crawler.
- Tesseract with Tamil (`tam`) and English (`eng`) language data if using the standalone OCR helper.

## Installation

Run commands from the project root. Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

## Configuration

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-small
FAISS_INDEX_PATH=indexes/faiss
TRUST_LOCAL_INDEX=false
EMBEDDING_CONFIG_VERIFIED=false
API_BASE_URL=http://127.0.0.1:8000
# Optional, for the standalone OCR helper:
# TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
```

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | Required for OpenAI embeddings. |
| `EMBEDDING_MODEL` | Model used for indexing and queries; defaults to `text-embedding-3-small`. |
| `FAISS_INDEX_PATH` | Backend index directory; relative paths resolve from the project root. Defaults to `indexes/faiss`. |
| `TRUST_LOCAL_INDEX` | Set to `true` only for an index you created or otherwise trust. Required by the backend. |
| `EMBEDDING_CONFIG_VERIFIED` | Set to `true` after confirming that query embeddings use the same model and configuration as the saved index. Required by the backend. |
| `API_BASE_URL` | Backend address used by Streamlit; defaults to `http://127.0.0.1:8000`. |
| `TESSERACT_PATH` | OCR executable path; defaults to the Windows path shown above. |

FAISS document metadata is loaded from a pickle file, which can execute code during deserialization. Load only trusted indexes. The CLI enables deserialization directly and does not enforce the backend trust flags.

Keep your API key out of version control.

## Prepare documents and an index

### Use local PDFs

Place PDFs directly in `data/raw/`. The indexer does not scan subdirectories.

**Current blocker:** `build_index()` in `src/vector_store.py` calls `extract_pdf(pdf_path)` before `pdf_path` is assigned. Before building an index, replace these initialization lines:

```python
'''documents = []'''
documents = extract_pdf(pdf_path)  # Now includes OCR
```

with:

```python
documents = []
```

Then run:

```powershell
python main.py index
```

The intended pipeline is:

```text
data/raw/*.pdf
  -> PDF text extraction
  -> overlapping text chunks
  -> OpenAI embeddings
  -> indexes/faiss/index.faiss + index.pkl
```

Index building saves to the hardcoded `indexes/faiss` directory and replaces the saved index. The CLI also uses that directory; `FAISS_INDEX_PATH` applies to the backend only.

If you already have a trusted compatible index, you can skip index building. Confirm its original embedding model and configuration, then set `TRUST_LOCAL_INDEX=true` and `EMBEDDING_CONFIG_VERIFIED=true` in `.env`.

### Optional: discover and download PDFs

Install Chromium and create the output directories:

```powershell
python -m playwright install chromium
New-Item -ItemType Directory -Force -Path data/raw, data/processed
python -m src.crawler --url https://agritech.tnau.ac.in/
python -m src.downloader
```

The crawler reads `robots.txt`, visits up to 20 pages on the starting hostname, and writes PDF links to `data/processed/pdf_urls.txt`. A failed robots.txt request stops the crawl.

The downloader reads that file and accepts only HTTPS URLs on `agritech.tnau.ac.in`. It does not follow redirects, checks PDF validity, skips duplicate content by SHA-256 hash, and limits each run to 100 new PDFs. Files over 50 MiB are rejected after downloading. Downloaded filenames are content hashes; original URLs are not persisted in PDF metadata.

## Run the application

### Backend

After configuring a trusted index and matching embeddings:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- Interactive API documentation: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/v1/health
- Diagnostics: http://127.0.0.1:8000/api/v1/diagnostics

The backend loads the index at startup and validates its distance metric and embedding dimensions. Restart it after replacing the index or changing configuration.

### Frontend

In a second terminal, activate the virtual environment and run from the project root:

```powershell
python -m streamlit run frontend/app.py
```

Open http://localhost:8501. Enter a question, select 5, 10, or 20 results, and optionally set a maximum distance.

### CLI search

With an existing index:

```powershell
python main.py search --query "What irrigation subsidies are available to farmers?"
```

The CLI prints the five nearest passages, including their distance, local source path, page number, and a text preview.

## API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/v1/health` | Service status, index availability, embedding model, and vector count. |
| GET | `/api/v1/stats` | Index readiness and vector count; unique document count is currently `null`. |
| GET | `/api/v1/diagnostics` | Index readiness and initialization error summary. |
| POST | `/api/v1/search` | Retrieve matching document chunks. |

Example search in PowerShell:

```powershell
$searchBody = @{
    query = "What irrigation subsidies are available?"
    top_k = 5
    language = "all"
    max_distance = $null
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/search" -ContentType "application/json" -Body $searchBody
```

Request fields:

- `query`: required, 1–1,000 characters; whitespace-only queries are rejected.
- `top_k`: one of `5`, `10`, or `20`; default `5`.
- `language`: `all`, `en`, or `ta`; default `all`. Currently accepted but not applied.
- `max_distance`: optional nonnegative squared L2 cutoff; default `null`.

Responses include `query`, `total_results`, `execution_time_ms`, and `results`. Each result includes `document_id`, `title`, `content`, `source_url`, `page`, `language`, `modality`, `distance`, and `score_type`.

Search returns HTTP 422 for invalid input, 503 when the index is unavailable, and 500 when the search operation fails. A health request can return HTTP 200 with a `degraded` status; check the response body for readiness.

## Project structure

```text
backend/
  main.py                    FastAPI routes and startup
  config.py                  Environment configuration
  schemas.py                 Request and response models
  services/faiss_service.py   Index loading and search
frontend/
  app.py                     Streamlit interface
  services/api_client.py     HTTP client for the backend
src/
  crawler.py                 PDF link discovery
  downloader.py              PDF downloads and deduplication
  pdf_loader.py              PDF text extraction
  ocr_service.py             Standalone Tamil/English OCR helper
  splitter.py                Document chunking
  embeddings.py              OpenAI embedding setup
  vector_store.py            CLI index building and search
tests/
  test_pipeline.py           PDF extraction and chunking tests
data/raw/                    Input PDFs
data/processed/              Discovered PDF URL list
indexes/faiss/               Saved FAISS index and document store
main.py                      CLI entry point
check_index.py               Index dimensions, count, and metric
inspect_faiss.py             Additional index inspection
test_input.py                Standalone Streamlit input diagnostic
requirements.txt             Dependency list
requirements.lock.txt        Additional dependency snapshot
```

## Validation and diagnostics

Run the existing extraction and splitting tests:

```powershell
python -m pytest tests/test_pipeline.py
```

These tests create a temporary PDF and check extraction, page metadata, chunk size, and metadata preservation. They do not exercise API requests, embeddings, or index building.

Inspect an existing index without making embedding requests:

```powershell
python check_index.py
python inspect_faiss.py
```

Check the standalone OCR installation:

```powershell
python -m src.ocr_service
```

## Current limitations and troubleshooting

- **Index build fails immediately:** correct the document initialization described above.
- **Scanned PDFs produce no content:** `pdf_loader.py` currently extracts embedded text only and skips blank pages. The OCR helper exists but is not connected to extraction.
- **Language selection does not change results:** backend language filtering is commented out, and extraction does not record language metadata.
- **Original source links are missing:** extraction records local file paths. Public links appear only when an index contains valid URL metadata.
- **Backend reports a degraded status:** check `/api/v1/diagnostics`, both index files, trust flags, API credentials, and server logs.
- **Embedding dimension mismatch:** use the original embedding model/configuration or rebuild the index. Matching dimensions alone does not establish model compatibility.
- **Frontend cannot reach the API:** start the backend and check `API_BASE_URL`.
- **No results after distance filtering:** remove or increase the cutoff. Distance is not a probability or confidence percentage.

Scheme information reflects the indexed PDFs. Check official sources for current eligibility, benefits, and application requirements.


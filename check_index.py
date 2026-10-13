from pathlib import Path
import faiss

index_dir = Path("indexes/faiss")
files = list(index_dir.glob("*.faiss"))

if not files:
    print("ERROR: No FAISS index files found.")
else:
    for file in files:
        index = faiss.read_index(str(file))

        print("Index filename:", file.name)
        print("Vector dimensions:", index.d)
        print("Indexed vectors:", index.ntotal)
        print("Distance metric:", index.metric_type)

from pathlib import Path
import faiss

index_dir = Path("indexes/faiss")

files = list(index_dir.glob("*.faiss"))

if not files:
    print("No FAISS index file found.")
    raise SystemExit(1)

for path in files:
    index = faiss.read_index(str(path))

    print("\nIndex file:", path)
    print("Vector dimensions:", index.d)
    print("Total indexed vectors:", index.ntotal)
    print("FAISS metric type:", index.metric_type)

    if index.metric_type == faiss.METRIC_L2:
        print("Metric: L2 / squared Euclidean distance")
    elif index.metric_type == faiss.METRIC_INNER_PRODUCT:
        print("Metric: Inner product")
    else:
        print("Metric: Other FAISS metric")

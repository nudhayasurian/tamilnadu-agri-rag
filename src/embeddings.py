
import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def get_embeddings():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing from .env"
        )

    return OpenAIEmbeddings(
        model=os.getenv(
            "EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
        api_key=api_key,
        max_retries=5,
        request_timeout=60,
    )


if __name__ == "__main__":
    embeddings = get_embeddings()

    vector = embeddings.embed_query(
        "தமிழ்நாட்டில் விவசாய மானியம்"
    )

    print("Embedding dimensions:", len(vector))
    print("First five values:", vector[:5])

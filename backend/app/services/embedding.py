"""
Embedding service — generates vector embeddings using OpenAI.
"""

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using OpenAI.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each is a list of floats).
    """
    if not texts:
        return []

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # OpenAI supports batch embedding (up to ~8k tokens per text)
    response = await client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
    )

    return [item.embedding for item in response.data]


async def generate_single_embedding(text: str) -> list[float]:
    """Generate embedding for a single text string."""
    embeddings = await generate_embeddings([text])
    return embeddings[0]

"""
Tests for embedding service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.embedding import generate_embeddings, generate_single_embedding


@pytest.mark.asyncio
async def test_generate_embeddings(mock_openai):
    # Setup mock response
    mock_response = MagicMock()
    mock_item_1 = MagicMock()
    mock_item_1.embedding = [0.1, 0.2, 0.3]
    mock_item_2 = MagicMock()
    mock_item_2.embedding = [0.4, 0.5, 0.6]
    mock_response.data = [mock_item_1, mock_item_2]

    mock_openai.embeddings.create = AsyncMock(return_value=mock_response)

    texts = ["hello", "world"]
    embeddings = await generate_embeddings(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2, 0.3]
    assert embeddings[1] == [0.4, 0.5, 0.6]
    mock_openai.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_empty():
    embeddings = await generate_embeddings([])
    assert embeddings == []


@pytest.mark.asyncio
async def test_generate_single_embedding(mock_openai):
    mock_response = MagicMock()
    mock_item = MagicMock()
    mock_item.embedding = [0.1, 0.2, 0.3]
    mock_response.data = [mock_item]

    mock_openai.embeddings.create = AsyncMock(return_value=mock_response)

    embedding = await generate_single_embedding("test")

    assert embedding == [0.1, 0.2, 0.3]
    mock_openai.embeddings.create.assert_called_once()

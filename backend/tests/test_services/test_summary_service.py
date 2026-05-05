"""
Tests for summary service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.summary_service import summarize_text, summarize_chunks


@pytest.fixture
def mock_summary_openai():
    with patch("app.services.summary_service.AsyncOpenAI") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_direct_summarize(mock_summary_openai):
    # Setup mock response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "This is a summary."
    mock_response.choices = [mock_choice]
    
    mock_summary_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Text shorter than 16000 chars
    text = "Short text to summarize"
    summary = await summarize_text(text)
    
    assert summary == "This is a summary."
    mock_summary_openai.chat.completions.create.assert_called_once()
    
    # Verify the parameters passed to API
    kwargs = mock_summary_openai.chat.completions.create.call_args[1]
    assert len(kwargs["messages"]) == 2
    assert kwargs["temperature"] == 0.3


@pytest.mark.asyncio
async def test_map_reduce_summarize(mock_summary_openai):
    # Setup mock response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Section summary."
    mock_response.choices = [mock_choice]
    
    mock_summary_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Text longer than 16000 chars
    text = "A" * 17000 
    summary = await summarize_text(text)
    
    assert summary == "Section summary."
    # Should be called once for map (chunk 1), once for map (chunk 2), once for reduce = 3 times total
    assert mock_summary_openai.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_summarize_chunks(mock_summary_openai):
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Chunk summary."
    mock_response.choices = [mock_choice]
    
    mock_summary_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    chunks = [
        {"text": "chunk 1", "metadata": {}},
        {"text": "chunk 2", "metadata": {}},
    ]
    summary = await summarize_chunks(chunks)
    
    assert summary == "Chunk summary."
    mock_summary_openai.chat.completions.create.assert_called_once()

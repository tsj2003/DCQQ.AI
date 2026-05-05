"""
Tests for LLM service.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm_service import (
    chat_with_document,
    chat_with_document_stream,
    _format_context,
    _format_timestamp,
    _extract_timestamps_from_results,
    _extract_sources_from_results,
)


@pytest.fixture
def mock_llm_openai():
    with patch("app.services.llm_service.AsyncOpenAI") as _mock:
        client = AsyncMock()
        yield client


@pytest.fixture
def mock_vector_store():
    with patch("app.services.llm_service.get_vector_store") as mock:
        store = MagicMock()
        mock.return_value = store
        yield store


def test_format_timestamp():
    assert _format_timestamp(0) == "00:00"
    assert _format_timestamp(65) == "01:05"
    assert _format_timestamp(3600) == "60:00"


def test_format_context():
    results = [
        {"text": "Text 1", "metadata": {"source_type": "pdf", "page": 1}},
        {"text": "Text 2", "metadata": {"source_type": "media", "start_time": 10, "end_time": 20}},
        {"text": "Text 3", "metadata": {}},
    ]
    context = _format_context(results)
    
    assert "[Page 1]" in context
    assert "[00:10 - 00:20]" in context
    assert "[Unknown source]" in context
    assert "Text 1" in context


def test_extract_timestamps():
    results = [
        {"text": "Text 1", "metadata": {"source_type": "pdf", "page": 1}},
        {"text": "Text 2", "metadata": {"source_type": "media", "start_time": 10, "end_time": 20}},
    ]
    timestamps = _extract_timestamps_from_results(results)
    
    assert len(timestamps) == 1
    assert timestamps[0]["start"] == 10
    assert timestamps[0]["end"] == 20
    assert timestamps[0]["text"] == "Text 2"


def test_extract_sources():
    results = [
        {"text": "Text 1", "metadata": {"source_type": "pdf", "page": 1}},
        {"text": "Text 2", "metadata": {"source_type": "pdf", "page": 1}},  # Duplicate page
        {"text": "Text 3", "metadata": {"source_type": "pdf", "page": 2}},
    ]
    sources = _extract_sources_from_results(results)
    
    assert len(sources) == 2
    assert sources[0]["page"] == 1
    assert sources[1]["page"] == 2


@pytest.mark.asyncio
async def test_chat_with_document(mock_llm_openai, mock_vector_store):
    # Setup vector store mock
    mock_vector_store.search = AsyncMock(return_value=[
        {"text": "Result text", "metadata": {"source_type": "pdf", "page": 1}}
    ])
    
    # Setup OpenAI mock
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "This is the answer."
    mock_response.choices = [mock_choice]
    mock_llm_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch("app.services.llm_service.AsyncOpenAI", return_value=mock_llm_openai):
        result = await chat_with_document(
            document_id="doc1",
            question="What is this?",
            chat_history=[{"role": "user", "content": "Hello"}],
        )
    
    assert result["content"] == "This is the answer."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["page"] == 1
    assert len(result["timestamps"]) == 0
    mock_vector_store.search.assert_called_once_with("What is this?", top_k=5)


@pytest.mark.asyncio
async def test_chat_with_document_stream(mock_llm_openai, mock_vector_store):
    # Setup vector store mock
    mock_vector_store.search = AsyncMock(return_value=[
        {"text": "Result text", "metadata": {"source_type": "media", "start_time": 0, "end_time": 10}}
    ])
    
    # Setup OpenAI mock for streaming
    async def mock_stream():
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = "Stream "
        yield chunk1
        
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "answer."
        yield chunk2
        
    mock_llm_openai.chat.completions.create = AsyncMock(return_value=mock_stream())
    
    with patch("app.services.llm_service.AsyncOpenAI", return_value=mock_llm_openai):
        generator = chat_with_document_stream(
            document_id="doc2",
            question="What happens at start?",
        )
        
        events = [event async for event in generator]
    
    assert len(events) == 4
    
    # Event 1: token
    assert "event: token" in events[0]
    data1 = json.loads(events[0].split("data: ")[1])
    assert data1["content"] == "Stream "
    
    # Event 2: token
    assert "event: token" in events[1]
    data2 = json.loads(events[1].split("data: ")[1])
    assert data2["content"] == "answer."
    
    # Event 3: metadata
    assert "event: metadata" in events[2]
    data3 = json.loads(events[2].split("data: ")[1])
    assert len(data3["timestamps"]) == 1
    assert data3["timestamps"][0]["start"] == 0
    
    # Event 4: done
    assert "event: done" in events[3]
    data4 = json.loads(events[3].split("data: ")[1])
    assert data4["content"] == "Stream answer."
    assert data4["done"] is True

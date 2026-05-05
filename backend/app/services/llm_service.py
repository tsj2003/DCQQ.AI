"""
LLM service — RAG pipeline with LangChain and OpenAI for Q&A.
"""

import json
from typing import AsyncGenerator

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.vector_store import get_vector_store

settings = get_settings()

SYSTEM_PROMPT = """You are DocQA AI, a helpful assistant that answers questions based on uploaded document content.

RULES:
1. Only answer based on the provided context. If the answer is not in the context, say "I couldn't find information about that in the uploaded document."
2. For audio/video content, always reference the timestamp range using the format [MM:SS - MM:SS] when relevant.
3. For PDF content, reference the page number using the format [Page X] when relevant.
4. Be concise but thorough.
5. When providing timestamps, format your response so they can be extracted as structured data.

CONTEXT FROM DOCUMENT:
{context}

CHAT HISTORY:
{chat_history}
"""


def _format_context(search_results: list[dict]) -> str:
    """Format search results into context string for the LLM."""
    context_parts = []
    for i, result in enumerate(search_results, 1):
        meta = result.get("metadata", {})
        source_type = meta.get("source_type", "unknown")

        if source_type == "pdf":
            source_info = f"[Page {meta.get('page', '?')}]"
        elif source_type == "media":
            start = meta.get("start_time", 0)
            end = meta.get("end_time", 0)
            source_info = f"[{_format_timestamp(start)} - {_format_timestamp(end)}]"
        else:
            source_info = "[Unknown source]"

        context_parts.append(f"--- Source {i} {source_info} ---\n{result['text']}")

    return "\n\n".join(context_parts)


def _format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def _format_chat_history(messages: list[dict]) -> str:
    """Format previous messages into chat history string."""
    if not messages:
        return "No previous messages."

    parts = []
    for msg in messages[-10:]:  # Last 10 messages for context
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")

    return "\n".join(parts)


def _extract_timestamps_from_results(search_results: list[dict]) -> list[dict]:
    """Extract timestamp references from search results."""
    timestamps = []
    for result in search_results:
        meta = result.get("metadata", {})
        if meta.get("source_type") == "media":
            timestamps.append({
                "start": meta.get("start_time", 0),
                "end": meta.get("end_time", 0),
                "text": result["text"][:200],  # First 200 chars as preview
            })
    return timestamps


def _extract_sources_from_results(search_results: list[dict]) -> list[dict]:
    """Extract page references from search results."""
    sources = []
    seen_pages = set()
    for result in search_results:
        meta = result.get("metadata", {})
        if meta.get("source_type") == "pdf":
            page = meta.get("page")
            if page and page not in seen_pages:
                sources.append({
                    "page": page,
                    "text": result["text"][:200],
                })
                seen_pages.add(page)
    return sources


async def chat_with_document(
    document_id: str,
    question: str,
    chat_history: list[dict] | None = None,
) -> dict:
    """Answer a question based on document content (non-streaming).

    Args:
        document_id: UUID of the document.
        question: User's question.
        chat_history: Previous messages in the conversation.

    Returns:
        Dict with 'content', 'timestamps', and 'sources'.
    """
    # Retrieve relevant chunks
    vector_store = get_vector_store(document_id)
    search_results = await vector_store.search(question, top_k=5)

    # Build prompt
    context = _format_context(search_results)
    history = _format_chat_history(chat_history or [])

    system_message = SYSTEM_PROMPT.format(context=context, chat_history=history)

    # Call OpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=2000,
    )

    answer = response.choices[0].message.content

    return {
        "content": answer,
        "timestamps": _extract_timestamps_from_results(search_results),
        "sources": _extract_sources_from_results(search_results),
    }


async def chat_with_document_stream(
    document_id: str,
    question: str,
    chat_history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream answer to a question based on document content via SSE.

    Yields SSE-formatted event strings.
    """
    # Retrieve relevant chunks
    vector_store = get_vector_store(document_id)
    search_results = await vector_store.search(question, top_k=5)

    # Build prompt
    context = _format_context(search_results)
    history = _format_chat_history(chat_history or [])

    system_message = SYSTEM_PROMPT.format(context=context, chat_history=history)

    # Stream from OpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    stream = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
        max_tokens=2000,
        stream=True,
    )

    full_content = ""
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            full_content += token
            yield f"event: token\ndata: {json.dumps({'content': token, 'done': False})}\n\n"

    # Send metadata at the end
    metadata = {
        "timestamps": _extract_timestamps_from_results(search_results),
        "sources": _extract_sources_from_results(search_results),
    }
    yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"
    yield f"event: done\ndata: {json.dumps({'content': full_content, 'done': True})}\n\n"

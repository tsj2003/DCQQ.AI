"""
Summary service — generates content summaries using LLM.
"""

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()

SUMMARY_PROMPT = """You are a document summarization expert. Provide a comprehensive yet concise summary of the following content.

GUIDELINES:
- Capture all key topics, arguments, and conclusions.
- Use bullet points for main ideas.
- Keep the summary between 200-500 words.
- For audio/video transcripts, note the main topics discussed and approximate time ranges.

CONTENT:
{content}

Provide a well-structured summary:"""

MAP_PROMPT = """Summarize the following section of a document in 2-3 sentences, capturing the key points:

{text}

Summary:"""

REDUCE_PROMPT = """The following are summaries of different sections of a document. Combine them into a single comprehensive summary.

GUIDELINES:
- Capture all key topics across sections.
- Use bullet points for main ideas.
- Keep the final summary between 200-500 words.
- Remove redundancies.

SECTION SUMMARIES:
{summaries}

Final comprehensive summary:"""


async def summarize_text(text: str) -> str:
    """Generate a summary for a given text.

    Uses direct summarization for short texts and map-reduce for long texts.

    Args:
        text: The content to summarize.

    Returns:
        Summary string.
    """
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Check if text fits in a single prompt (~4000 tokens ≈ 16000 chars)
    if len(text) < 16000:
        return await _direct_summarize(client, text)
    else:
        return await _map_reduce_summarize(client, text)


async def _direct_summarize(client: AsyncOpenAI, text: str) -> str:
    """Summarize short text directly."""
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a document summarization expert."},
            {"role": "user", "content": SUMMARY_PROMPT.format(content=text)},
        ],
        temperature=0.3,
        max_tokens=1000,
    )
    return response.choices[0].message.content


async def _map_reduce_summarize(client: AsyncOpenAI, text: str) -> str:
    """Summarize long text using map-reduce approach."""
    # Split text into chunks
    chunk_size = 12000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Map: summarize each chunk
    chunk_summaries = []
    for chunk in chunks:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "user", "content": MAP_PROMPT.format(text=chunk)},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        chunk_summaries.append(response.choices[0].message.content)

    # Reduce: combine summaries
    combined = "\n\n".join(
        f"Section {i + 1}: {s}" for i, s in enumerate(chunk_summaries)
    )

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a document summarization expert."},
            {"role": "user", "content": REDUCE_PROMPT.format(summaries=combined)},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    return response.choices[0].message.content


async def summarize_chunks(chunks: list[dict]) -> str:
    """Summarize a list of text chunks (from PDF or transcript).

    Args:
        chunks: List of chunk dicts with 'text' key.

    Returns:
        Summary string.
    """
    full_text = "\n\n".join(chunk["text"] for chunk in chunks)
    return await summarize_text(full_text)

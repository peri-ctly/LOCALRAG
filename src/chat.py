

"""
LLM answer generation for the Local RAG Assistant.

Pipeline: Retriever -> Context -> Foundry Local  -> Answer
"""

import re
from threading import Lock

from src.foundry import manager

UNAVAILABLE_MESSAGE = (
    "The answer is not available in the provided context."
)

CHAT_MODEL_ALIAS = "phi-3.5-mini"

print("Loading chat model...")

chat_model = manager.catalog.get_model(CHAT_MODEL_ALIAS)
chat_model.download()
chat_model.load()

chat_client = chat_model.get_chat_client()

model_lock = Lock()

print("Chat model ready!")


def remove_thinking_text(text):
    """
    Removes optional <think>...</think> reasoning blocks that
    some Qwen models include in their output.
    """

    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return cleaned.strip()



def remove_repetition_loop(text):
    """
    Cuts the answer at the point where a sentence starts repeating,
    which happens when a small model gets stuck in a loop. Handles
    numbered-list repeats (e.g. "1. ...", "2. ...") by ignoring the
    leading number when comparing sentences.
    """

    sentences = re.split(r"(?<=[.!?])\s+", text)

    seen = set()
    kept = []

    for sentence in sentences:
        normalized = re.sub(r"^\d+[\.\)]\s*", "", sentence.strip().lower())

        if normalized and normalized in seen:
            break

        if normalized:
            seen.add(normalized)

        kept.append(sentence)

    return " ".join(kept).strip()


def generate_answer(question, context):
    """
    Generates an answer using only the retrieved context.

    """

    question = question.strip()

    if not question or not context:
        return UNAVAILABLE_MESSAGE

    messages = [
        {
            "role": "system",
            "content": (
                "You are a document question-answering assistant.\n"
                "Answer the user's question using ONLY the provided "
                "context.\n"
                "Never invent facts, numbers, or details that are not "
                "explicitly stated in the context.\n"
                "If the context contains multiple unrelated pieces of "
                "information, use only the part that directly answers "
                "the question and ignore the rest.\n"
                "If the context does not contain everything the question asks "
                "for, state only what is present and say the rest is missing.\n"
                "If the context does not contain the answer, respond "
                "exactly with:\n"
                f"\"{UNAVAILABLE_MESSAGE}\"\n"
                "Keep the answer clear and directly relevant to the "
                "question. When the answer is a list of items, briefly "
                "explain each item using the context.\n\n"
                f"Context:\n{context}"
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    response_parts = []
    seen_sentences = set()
    buffer = ""
    thinking_closed = False

    with model_lock:
        for chunk in chat_client.complete_streaming_chat(messages):
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if not content:
                continue

            response_parts.append(content)
            buffer += content

            full_so_far = "".join(response_parts)

            if not thinking_closed:
                if "<think>" in full_so_far and "</think>" not in full_so_far:
                    continue
                elif "</think>" in full_so_far:
                    thinking_closed = True
                    buffer = ""
                    continue
                elif "<think>" not in full_so_far:
                    thinking_closed = True

            sentences = re.split(r"(?<=[.!?])\s+", buffer)
            buffer = sentences.pop() if sentences else ""

            for sentence in sentences:
                normalized = re.sub(
                    r"^\d+[\.\)]\s*", "", sentence.strip().lower()
                )

                if normalized and normalized in seen_sentences:
                    response_parts = response_parts[:-1]
                    buffer = ""
                    break

                if normalized:
                    seen_sentences.add(normalized)
            else:
                continue

            break

    answer = remove_thinking_text("".join(response_parts))
    answer = remove_repetition_loop(answer)

    if UNAVAILABLE_MESSAGE.lower() in answer.lower():
        return UNAVAILABLE_MESSAGE

    for snippet in re.findall(r"`([^`]+)`", answer):
        if snippet.strip().lower() not in context.lower():
            return UNAVAILABLE_MESSAGE

    return answer if answer else UNAVAILABLE_MESSAGE


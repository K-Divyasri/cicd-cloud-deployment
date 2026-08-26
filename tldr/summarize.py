"""
summarize.py - the tiny bit of "AI" the service does.

By default it runs an OFFLINE, deterministic extractive summariser (no API key,
no network) so the whole project builds, tests, and containers without secrets.
If you set TLDR_MODEL=gemini and provide a key, it calls a real LLM instead.

Keeping a deterministic default is what makes the tests reliable and the CI
pipeline runnable by anyone - a theme you'll see throughout this track.
"""
import re
from collections import Counter

_WORD = re.compile(r"[A-Za-z']+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_STOP = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "is",
    "are", "was", "were", "be", "been", "it", "this", "that", "with", "as", "at",
    "by", "from", "we", "you", "they", "he", "she", "i", "our", "your", "their",
}
WORDS_PER_MINUTE = 200


def _sentences(text: str):
    return [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def extractive_summary(text: str, max_sentences: int = 2) -> str:
    """Pick the most 'central' sentences by word-frequency scoring, and return
    them in their original order. Deterministic: same text -> same summary."""
    sents = _sentences(text)
    if len(sents) <= max_sentences:
        return " ".join(sents)
    freq = Counter(w.lower() for w in _WORD.findall(text) if w.lower() not in _STOP)
    scored = []
    for i, s in enumerate(sents):
        words = [w.lower() for w in _WORD.findall(s)]
        score = sum(freq[w] for w in words) / (len(words) or 1)
        scored.append((score, i, s))
    top = sorted(scored, reverse=True)[:max_sentences]
    return " ".join(s for _, _, s in sorted(top, key=lambda t: t[1]))


def word_count(text: str) -> int:
    return len(_WORD.findall(text))


def reading_seconds(text: str) -> int:
    return round(word_count(text) / WORDS_PER_MINUTE * 60)


def _gemini_summary(text: str, api_key: str, model: str = "gemini/gemini-1.5-flash") -> str:
    """Optional real-LLM path. Imported lazily so the offline app never needs it."""
    from litellm import completion  # noqa: WPS433 (lazy import on purpose)
    resp = completion(
        model=model,
        api_key=api_key,
        messages=[
            {"role": "system", "content": "Summarise the user's text in one or two sentences."},
            {"role": "user", "content": text},
        ],
        max_tokens=120,
    )
    return resp["choices"][0]["message"]["content"].strip()


def summarize(text: str, settings) -> dict:
    """Return a summary payload. Uses the offline summariser unless a real model
    is configured AND a key is present (so a misconfigured 'gemini' safely falls
    back instead of crashing in production)."""
    text = (text or "").strip()
    if not text:
        return {"summary": "", "words": 0, "reading_seconds": 0, "model": "offline"}
    if settings.model == "gemini" and settings.has_gemini_key:
        try:
            return {
                "summary": _gemini_summary(text, settings.gemini_api_key),
                "words": word_count(text),
                "reading_seconds": reading_seconds(text),
                "model": "gemini",
            }
        except Exception:
            pass  # never let the model take the endpoint down - degrade to offline
    return {
        "summary": extractive_summary(text),
        "words": word_count(text),
        "reading_seconds": reading_seconds(text),
        "model": "offline",
    }

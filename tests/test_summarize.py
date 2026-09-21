"""Tests for the offline summariser. These run with no key and no network -
the reason CI can run them on anyone's push."""
from tldr.config import Settings
from tldr.summarize import extractive_summary, reading_seconds, summarize, word_count

TEXT = (
    "Docker packages an app with everything it needs to run. "
    "The same image runs the same way on your laptop and in the cloud. "
    "That reproducibility is why containers took over deployment. "
    "A container is just a running instance of an image."
)


def _offline_settings():
    return Settings(app_env="test", git_sha="abc123", model="offline",
                    gemini_api_key="", port=8000)


def test_summary_is_deterministic():
    assert extractive_summary(TEXT) == extractive_summary(TEXT)


def test_summary_picks_real_sentences():
    summary = extractive_summary(TEXT)
    # Every sentence in the summary must be a sentence from the source.
    for piece in summary.split(". "):
        assert piece.strip(". ") in TEXT


def test_short_text_returned_whole():
    assert extractive_summary("Just one sentence.") == "Just one sentence."


def test_word_count_and_reading_time():
    assert word_count("one two three") == 3
    assert reading_seconds("word " * 200) == 60  # 200 wpm -> 60s


def test_summarize_payload_shape():
    out = summarize(TEXT, _offline_settings())
    assert set(out) == {"summary", "words", "reading_seconds", "model"}
    assert out["model"] == "offline"
    assert out["words"] == word_count(TEXT)


def test_empty_text_is_safe():
    out = summarize("   ", _offline_settings())
    assert out["summary"] == "" and out["words"] == 0

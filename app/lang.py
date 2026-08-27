"""
Lightweight language and message detection.

Supports Arabic and English routing without external dependencies.
"""

import re

_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")

_ARABIC_GREETINGS = {
    "السلام عليكم",
    "السلام عليكم ورحمة الله وبركاته",
    "سلام عليكم",
    "أهلا",
    "أهلاً",
    "اهلا",
    "اهلاً",
    "مرحبا",
    "مرحباً",
    "هاي",
}

_ENGLISH_GREETINGS = {
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
}


def detect_language(text: str) -> str:
    """Returns 'ar' if the text contains Arabic script, otherwise 'en'."""
    return "ar" if _ARABIC_RE.search(text) else "en"


def is_greeting(text: str) -> bool:
    """Returns True when the message is a simple Arabic or English greeting."""
    normalized = " ".join(text.strip().lower().split())

    return (
        normalized in {item.lower() for item in _ARABIC_GREETINGS}
        or normalized in _ENGLISH_GREETINGS
    )
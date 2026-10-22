from functools import lru_cache

from lingua import Language, LanguageDetectorBuilder


@lru_cache(maxsize=1)
def detector():
    return LanguageDetectorBuilder.from_languages(
        Language.ITALIAN, Language.ENGLISH
    ).with_minimum_relative_distance(0.25).build()


def matches_language(text: str, language: str) -> bool:
    detected = detector().detect_language_of(text)
    # Shared short phrases can be ambiguous; don't reject them as certain language errors.
    return detected is None or detected == {"it": Language.ITALIAN, "en": Language.ENGLISH}[language]

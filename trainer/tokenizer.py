import unicodedata
from functools import lru_cache

from sudachipy import dictionary, tokenizer


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip()


@lru_cache(maxsize=1)
def analyzer():
    return dictionary.Dictionary().create()


def tokenize(text: str) -> list[dict]:
    return [
        {"surface": m.surface(), "lemma": m.dictionary_form(), "normalized": m.normalized_form(),
         "reading": m.reading_form(), "pos": list(m.part_of_speech()), "oov": m.is_oov()}
        for m in analyzer().tokenize(normalize(text), tokenizer.Tokenizer.SplitMode.A)
    ]

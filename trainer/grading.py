import math
import re

from trainer.tokenizer import normalize, tokenize


def lemmas(tokens):
    return {t["normalized"] for t in tokens if t["pos"][0] not in {"助詞", "助動詞", "補助記号", "空白"}}


def deterministic(answer: str, references: list[str], vocab: set[str], kanji: set[str], pattern: str):
    tokens = tokenize(answer)
    reference_tokens = [tokenize(r) for r in references]
    actual = lemmas(tokens)
    similarities = [len(actual & lemmas(ref)) / max(1, len(actual | lemmas(ref))) for ref in reference_tokens]
    findings = []
    for char in sorted(set(re.findall(r"[\u3400-\u9fff]", normalize(answer))) - kanji):
        findings.append({"code": "kanji_not_listed", "value": char, "severity": "scope",
                         "certainty": "deterministic"})
    unknown = set()
    for t in tokens:
        if t["pos"][0] in {"名詞", "動詞", "形容詞", "副詞"} and not (
            {t["lemma"], t["normalized"], t["surface"]} & vocab
        ):
            unknown.add(t["lemma"])
    for term in sorted(unknown):
        findings.append({"code": "vocabulary_not_listed", "value": term, "severity": "scope",
                         "certainty": "deterministic"})
    # shortcut: only adjacent duplicate case particles are certain, expand with reviewed pattern rules.
    for left, right in zip(tokens, tokens[1:]):
        if left["surface"] == right["surface"] and left["surface"] in {"を", "が", "に", "で", "へ"}:
            findings.append({"code": "duplicate_particle", "value": left["surface"] * 2,
                             "severity": "error", "certainty": "deterministic"})
    forms = [{"surface": t["surface"], "type": t["pos"][4], "form": t["pos"][5]}
             for t in tokens if t["pos"][4] != "*"]
    return {"tokens": tokens, "findings": findings, "forms": forms,
            "lemma_similarity": round(max(similarities, default=0), 3), "target_pattern": pattern,
            "pattern_check": "requires_contextual_judgment"}


def render_n5_reference(text: str, vocabulary: set[str], kanji: set[str]) -> str:
    result = []
    for token in tokenize(text):
        surface = token["surface"]
        outside = set(re.findall(r"[\u3400-\u9fff]", surface)) - kanji
        known_word = bool({token["lemma"], token["normalized"], surface} & vocabulary)
        reading = token["reading"]
        if outside and known_word and not token["oov"] and re.fullmatch(r"[ァ-ヶー]+", reading):
            if re.fullmatch(r"[ァ-ヶー]+", token["normalized"]):
                surface = reading
            else:
                surface = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in reading)
        result.append(surface)
    return "".join(result)


def sm2(quality: int, repetitions=0, interval_days=0, ease=2.5):
    if not 0 <= quality <= 5:
        raise ValueError("quality must be in 0..5")
    if quality < 3:
        repetitions, interval_days = 0, 1
    else:
        interval_days = 1 if repetitions == 0 else 6 if repetitions == 1 else math.ceil(interval_days * ease)
        repetitions += 1
    ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return {"repetitions": repetitions, "interval_days": interval_days, "ease": round(ease, 3)}

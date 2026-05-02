from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer

from app.lang import Language, detect_language, tokenize, split_sentences, FILLERS


@dataclass
class NLPFeatures:
    type_token_ratio: float
    filler_rate: float
    mean_utterance_length: float
    topic_coherence: float
    topic_drift: float
    word_count: int
    sentence_count: int
    embedding: list[float]
    language: Language = "en"


class NLPExtractor:
    def __init__(self) -> None:
        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def extract(self, text: str, prev_embedding: list[float] | None = None,
                lang: Language | None = None) -> NLPFeatures:
        language: Language = lang or detect_language(text)
        words = tokenize(text, language)
        total = len(words)

        if not total:
            return NLPFeatures(0.0, 0.0, 0.0, 1.0, 0.0, 0, 0, [], language)

        ttr = len(set(words)) / total

        fillers = FILLERS[language]
        filler_count = sum(words.count(f) for f in fillers)
        filler_rate = filler_count / total * 100

        sentences = split_sentences(text, language)
        sentence_count = len(sentences)
        mean_len = (
            sum(len(tokenize(s, language)) for s in sentences) / sentence_count
            if sentence_count else float(total)
        )

        embedding: list[float] = self._model.encode(text).tolist()

        if prev_embedding:
            a, b = np.array(embedding), np.array(prev_embedding)
            coherence = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
            coherence = max(0.0, min(1.0, coherence))
        else:
            coherence = 1.0

        return NLPFeatures(
            type_token_ratio=ttr,
            filler_rate=filler_rate,
            mean_utterance_length=mean_len,
            topic_coherence=coherence,
            topic_drift=1.0 - coherence,
            word_count=total,
            sentence_count=sentence_count,
            embedding=embedding,
            language=language,
        )


_extractor = NLPExtractor()


def extract_nlp(text: str, prev_embedding: list[float] | None = None,
                lang: Language | None = None) -> NLPFeatures:
    return _extractor.extract(text, prev_embedding, lang)

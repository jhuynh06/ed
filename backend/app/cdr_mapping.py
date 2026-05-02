from dataclasses import dataclass, field

from app.acoustic_features import AcousticFeatures
from app.nlp_features import NLPFeatures


@dataclass
class CDRScores:
    commun: float
    orient: float
    memory: float
    judgment: float
    total: float
    flags: list[str]


def map_to_cdr(
    acoustic: AcousticFeatures,
    nlp: NLPFeatures,
    prev_nlp: NLPFeatures | None = None,
) -> CDRScores:
    flags: list[str] = []

    # COMMUN
    commun = 0.0
    if nlp.type_token_ratio < 0.3:
        commun += 1.0; flags.append("low vocabulary diversity")
    elif nlp.type_token_ratio < 0.5:
        commun += 0.5; flags.append("reduced vocabulary diversity")
    if nlp.filler_rate > 15:
        commun += 1.0; flags.append("high filler rate")
    elif nlp.filler_rate > 8:
        commun += 0.5; flags.append("elevated filler rate")
    if nlp.mean_utterance_length < 3:
        commun += 0.5; flags.append("very short utterances")

    # ORIENT
    orient = 0.0
    if nlp.topic_coherence < 0.3:
        orient += 1.5; flags.append("severe topic drift")
    elif nlp.topic_coherence < 0.5:
        orient += 1.0; flags.append("moderate topic drift")
    elif nlp.topic_coherence < 0.7:
        orient += 0.5; flags.append("mild topic drift")
    if acoustic.speaking_rate < 1.0:
        orient += 0.5; flags.append("very slow speech")

    # MEMORY
    memory = 0.0
    if prev_nlp is not None:
        topic_drift = 1.0 - nlp.topic_coherence  # proxy: low coherence vs prev context
        if abs(nlp.topic_coherence - prev_nlp.topic_coherence) > 0.7:
            memory += 1.0; flags.append("topic jumped between sessions")
        if (prev_nlp.type_token_ratio - nlp.type_token_ratio) > 0.2:
            memory += 1.0; flags.append("vocabulary shrinking vs prior session")
    if acoustic.pause_rate > 2.0:
        memory += 0.5; flags.append("frequent pausing (word-finding difficulty)")

    # JUDGMENT
    judgment = 0.0
    if acoustic.hnr < 5.0:
        judgment += 0.5; flags.append("poor voice quality (dysarthria risk)")
    if acoustic.jitter > 0.05:
        judgment += 0.5; flags.append("elevated jitter")
    if acoustic.shimmer > 0.15:
        judgment += 0.5; flags.append("elevated shimmer")
    if nlp.word_count < 10:
        judgment += 0.5; flags.append("very brief response")

    commun = min(commun, 3.0)
    orient = min(orient, 3.0)
    memory = min(memory, 3.0)
    judgment = min(judgment, 3.0)

    return CDRScores(
        commun=commun,
        orient=orient,
        memory=memory,
        judgment=judgment,
        total=(commun + orient + memory + judgment) / 4,
        flags=flags,
    )

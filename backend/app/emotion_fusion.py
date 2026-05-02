import os
from dataclasses import dataclass

from dotenv import load_dotenv
from transformers import pipeline

from app.audio_pipeline import AudioResult

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))


@dataclass
class FusedEmotion:
    audio_valence: float
    audio_arousal: float
    text_sentiment: float    # -1 to +1 (NEGATIVE=-1, POSITIVE=+1)
    text_confidence: float   # 0-1
    fused_valence: float     # 0.4*audio + 0.6*text
    fused_arousal: float     # audio arousal unchanged
    disagreement: float      # abs(audio_valence - text_sentiment), 0-1
    dominant_emotion: str


class EmotionFuser:
    def __init__(self) -> None:
        self._sentiment = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device="cpu",
        )

    def fuse(self, audio_result: AudioResult) -> FusedEmotion:
        if audio_result.transcription:
            result = self._sentiment(audio_result.transcription)[0]
            score = result["score"]
            text_sentiment = score if result["label"] == "POSITIVE" else -score
            text_confidence = score
        else:
            text_sentiment = audio_result.valence
            text_confidence = 0.0

        fused_valence = 0.4 * audio_result.valence + 0.6 * text_sentiment
        disagreement = abs(audio_result.valence - text_sentiment)

        return FusedEmotion(
            audio_valence=audio_result.valence,
            audio_arousal=audio_result.arousal,
            text_sentiment=text_sentiment,
            text_confidence=text_confidence,
            fused_valence=fused_valence,
            fused_arousal=audio_result.arousal,
            disagreement=disagreement,
            dominant_emotion=audio_result.dominant_emotion,
        )

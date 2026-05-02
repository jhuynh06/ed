"""Unit tests for emotion_fusion.py — mocks DistilBERT, no model downloads."""

from __future__ import annotations

import sys
import os
import types
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub heavy deps before any app import
for mod, attrs in [
    ("transformers", {"pipeline": MagicMock()}),
    ("silero_vad", {"load_silero_vad": MagicMock(return_value=MagicMock()), "get_speech_timestamps": MagicMock(return_value=[])}),
    ("groq", {"Groq": MagicMock()}),
]:
    if mod not in sys.modules:
        stub = types.ModuleType(mod)
        for k, v in attrs.items():
            setattr(stub, k, v)
        sys.modules[mod] = stub

# torch — only stub if real torch not loaded (real torch needed by sentence_transformers)
if "torch" not in sys.modules or not hasattr(sys.modules["torch"], "Tensor"):
    torch_stub = types.ModuleType("torch")
    torch_stub.from_numpy = lambda x: x
    sys.modules["torch"] = torch_stub

# sentence_transformers stub
st_stub2 = types.ModuleType("sentence_transformers")
st_stub2.SentenceTransformer = MagicMock(return_value=MagicMock())
sys.modules.setdefault("sentence_transformers", st_stub2)

# librosa stub
import numpy as _np
librosa_stub2 = types.ModuleType("librosa")
librosa_stub2.yin = MagicMock(return_value=_np.array([220.0] * 100))
librosa_stub2.feature = MagicMock()
librosa_stub2.feature.rms = MagicMock(return_value=_np.array([[0.1] * 100]))
librosa_stub2.util = MagicMock()
sys.modules.setdefault("librosa", librosa_stub2)

from app.audio_pipeline import AudioResult  # noqa: E402
from app.emotion_fusion import EmotionFuser, FusedEmotion  # noqa: E402


def make_fuser(label: str = "POSITIVE", score: float = 0.9) -> EmotionFuser:
    fuser = EmotionFuser.__new__(EmotionFuser)
    fuser._sentiment = MagicMock(return_value=[{"label": label, "score": score}])
    return fuser


def audio(valence: float = 0.0, arousal: float = 0.1,
          text: str | None = "hello", emotion: str = "neutral") -> AudioResult:
    return AudioResult(speech_detected=True, transcription=text,
                       valence=valence, arousal=arousal, dominant_emotion=emotion)


# ── basic fusion ─────────────────────────────────────────────────────

def test_positive_text_positive_audio_low_disagreement():
    result = make_fuser("POSITIVE", 0.9).fuse(audio(valence=0.7))
    assert result.text_sentiment == pytest.approx(0.9)
    assert result.fused_valence == pytest.approx(0.4 * 0.7 + 0.6 * 0.9)
    assert result.disagreement < 0.3


def test_negative_label_negates_score():
    result = make_fuser("NEGATIVE", 0.75).fuse(audio(valence=0.0))
    assert result.text_sentiment == pytest.approx(-0.75)


def test_fused_valence_weights():
    result = make_fuser("POSITIVE", 0.6).fuse(audio(valence=0.2))
    assert result.fused_valence == pytest.approx(0.4 * 0.2 + 0.6 * 0.6)


def test_fused_arousal_unchanged():
    result = make_fuser("NEGATIVE", 0.9).fuse(audio(valence=-0.5, arousal=0.8))
    assert result.fused_arousal == pytest.approx(0.8)


# ── disagreement signal ───────────────────────────────────────────────

def test_neutral_audio_negative_text_high_disagreement():
    """Classic dementia masking: sounds calm, words are distressed."""
    result = make_fuser("NEGATIVE", 0.85).fuse(audio(valence=0.1, text="I'm fine"))
    assert result.disagreement == pytest.approx(abs(0.1 - (-0.85)))
    assert result.disagreement > 0.4


def test_disagreement_range():
    """disagreement is always in [0, 2] (valence in [-1,1], text in [-1,1])."""
    result = make_fuser("NEGATIVE", 1.0).fuse(audio(valence=1.0))
    assert 0.0 <= result.disagreement <= 2.0


# ── no transcription fallback ─────────────────────────────────────────

def test_no_transcription_no_disagreement():
    fuser = make_fuser()
    result = fuser.fuse(audio(valence=0.3, text=None))
    assert result.text_confidence == 0.0
    assert result.text_sentiment == pytest.approx(0.3)
    assert result.disagreement == pytest.approx(0.0)
    fuser._sentiment.assert_not_called()

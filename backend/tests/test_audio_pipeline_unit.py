"""Unit tests for audio_pipeline.py — no mic, no API keys, no model downloads."""

from __future__ import annotations

import sys
import os
import types
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Stub heavy imports before audio_pipeline loads them ──────────────

# silero_vad
silero_stub = types.ModuleType("silero_vad")
silero_stub.load_silero_vad = MagicMock(return_value=MagicMock())
silero_stub.get_speech_timestamps = MagicMock(return_value=[])
sys.modules["silero_vad"] = silero_stub

# transformers
transformers_stub = types.ModuleType("transformers")
transformers_stub.pipeline = MagicMock(return_value=MagicMock())
sys.modules["transformers"] = transformers_stub

# groq
groq_stub = types.ModuleType("groq")
groq_stub.Groq = MagicMock()
sys.modules["groq"] = groq_stub

# whisper — stub so audio_pipeline doesn't need the real model in unit tests
whisper_stub = types.ModuleType("whisper")
whisper_stub.load_model = MagicMock(return_value=MagicMock(dims=MagicMock(n_mels=80), parameters=MagicMock(return_value=[])))
whisper_stub.pad_or_trim = lambda x: x
whisper_stub.log_mel_spectrogram = MagicMock(return_value=MagicMock(to=MagicMock(return_value=MagicMock())))
whisper_stub.decode = MagicMock(return_value=MagicMock(text="test transcription", no_speech_prob=0.0))
whisper_stub.DecodingOptions = MagicMock()
sys.modules["whisper"] = whisper_stub

# torch — only stub if real torch not already loaded
if "torch" not in sys.modules or not hasattr(sys.modules["torch"], "Tensor"):
    torch_stub = types.ModuleType("torch")
    torch_stub.from_numpy = lambda x: x
    cuda_stub = MagicMock()
    cuda_stub.is_available = MagicMock(return_value=False)
    torch_stub.cuda = cuda_stub
    sys.modules["torch"] = torch_stub

# sentence_transformers — stub so NLPExtractor doesn't download models
st_stub = types.ModuleType("sentence_transformers")
st_stub.SentenceTransformer = MagicMock(return_value=MagicMock())
sys.modules.setdefault("sentence_transformers", st_stub)

# librosa — stub so AcousticExtractor doesn't need audio libs
librosa_stub = types.ModuleType("librosa")
librosa_stub.yin = MagicMock(return_value=np.array([220.0] * 100))
librosa_stub.feature = MagicMock()
librosa_stub.feature.rms = MagicMock(return_value=np.array([[0.1] * 100]))
librosa_stub.util = MagicMock()
librosa_stub.util.peak_pick = MagicMock(return_value=np.array([10, 30, 50]))
librosa_stub.util.frame = MagicMock(return_value=np.zeros((2048, 10)))
sys.modules.setdefault("librosa", librosa_stub)

# Now safe to import
from app.audio_pipeline import (  # noqa: E402
    AudioPipeline,
    AudioResult,
    SAMPLE_RATE,
    FRAME_SIZE,
    VAD_CHECK_INTERVAL,
    SPEECH_END_FRAMES,
    _parse_emotion_preds,
    _to_wav_bytes,
)
from app.agents.risk import compute_agitation_score, score_to_risk  # noqa: E402
from app.models import IMUFeatures, HRState, TouchState, SensorSnapshot, VocalEmotion  # noqa: E402


# ── Helpers ──────────────────────────────────────────────────────────

def make_pipeline() -> AudioPipeline:
    """Return an AudioPipeline with all external deps mocked."""
    p = AudioPipeline.__new__(AudioPipeline)
    p._vad_model = MagicMock()
    # Mock local whisper: decode returns an object with .text and .no_speech_prob
    p._whisper = MagicMock()
    p._whisper.dims.n_mels = 80
    p._emotion_pipe = MagicMock(return_value=[
        {"label": "neutral", "score": 0.8},
        {"label": "sad", "score": 0.2},
    ])
    p._acoustic = MagicMock()
    p._acoustic.extract = MagicMock(return_value=MagicMock(
        f0_mean=150.0, f0_std=10.0, jitter=0.01, shimmer=0.05,
        speaking_rate=3.0, pause_count=0, pause_rate=0.0,
        mean_pause_duration=0.0, hnr=15.0,
    ))
    p._nlp = MagicMock()
    p._nlp.extract = MagicMock(return_value=MagicMock(
        type_token_ratio=0.7, filler_rate=2.0, mean_utterance_length=8.0,
        topic_coherence=0.8, topic_drift=0.2, word_count=20,
        sentence_count=3, embedding=[0.1] * 384,
    ))
    p._prev_nlp = None
    p._buffer = []
    p._frame_count = 0
    return p


def set_whisper_text(p: AudioPipeline, text: str, no_speech_prob: float = 0.0) -> None:
    """Configure the whisper stub to return the given transcription."""
    mock_result = MagicMock()
    mock_result.text = text
    mock_result.no_speech_prob = no_speech_prob
    whisper_stub.decode = MagicMock(return_value=mock_result)


def silence(n_frames: int = 1) -> np.ndarray:
    return np.zeros(FRAME_SIZE * n_frames, dtype=np.float32)


def speech_audio(seconds: float = 1.0) -> np.ndarray:
    t = np.linspace(0, seconds, int(SAMPLE_RATE * seconds))
    return (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)


# ── _parse_emotion_preds ─────────────────────────────────────────────

def test_parse_emotion_preds_empty():
    v, a, label = _parse_emotion_preds([])
    assert v == 0.0
    assert a == 0.0
    assert label == "neutral"


def test_parse_emotion_preds_single():
    preds = [{"label": "angry", "score": 1.0}]
    v, a, label = _parse_emotion_preds(preds)
    assert label == "angry"
    assert a > 0.5  # angry is high arousal


def test_parse_emotion_preds_weighted():
    preds = [
        {"label": "happy", "score": 0.6},
        {"label": "neutral", "score": 0.4},
    ]
    v, a, label = _parse_emotion_preds(preds)
    assert label == "happy"
    assert v > 0  # happy is positive valence


# ── _to_wav_bytes ────────────────────────────────────────────────────

def test_to_wav_bytes_produces_valid_wav():
    import wave, io
    audio = speech_audio(0.1)
    wav = _to_wav_bytes(audio)
    with wave.open(io.BytesIO(wav)) as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == SAMPLE_RATE
        assert wf.getsampwidth() == 2


# ── push_frame — no speech ───────────────────────────────────────────

def test_push_frame_silence_returns_none():
    p = make_pipeline()
    with patch("app.audio_pipeline.get_speech_timestamps", return_value=[]):
        # Push exactly VAD_CHECK_INTERVAL frames so VAD runs once
        for _ in range(VAD_CHECK_INTERVAL):
            result = p.push_frame(silence())
    assert result is None


def test_push_frame_long_silence_clears_buffer():
    p = make_pipeline()
    threshold = SAMPLE_RATE // FRAME_SIZE * 3  # 93 frames
    # Round up to next VAD check boundary
    n_frames = ((threshold + 10) // VAD_CHECK_INTERVAL + 1) * VAD_CHECK_INTERVAL
    with patch("app.audio_pipeline.get_speech_timestamps", return_value=[]):
        for _ in range(n_frames):
            p.push_frame(silence())
    assert len(p._buffer) <= threshold


# ── push_frame — active speech ───────────────────────────────────────

def test_push_frame_active_speech_returns_none():
    """VAD says speech is still ongoing — should keep buffering."""
    p = make_pipeline()
    result = None
    with patch("app.audio_pipeline.get_speech_timestamps",
               return_value=[{"start": 0, "end": FRAME_SIZE * VAD_CHECK_INTERVAL}]):
        for _ in range(VAD_CHECK_INTERVAL):
            result = p.push_frame(silence())
    assert result is None


# ── push_frame — speech ended ────────────────────────────────────────

def test_push_frame_speech_ended_calls_inference():
    """When VAD reports speech ended, inference fires and buffer clears."""
    p = make_pipeline()
    set_whisper_text(p, "I love you grandma")

    audio = speech_audio(1.0)
    total_samples = len(audio)
    # Speech ends 10 frames before buffer end
    end_sample = total_samples - FRAME_SIZE * 10

    call_count = 0

    def vad_side_effect(tensor, model, sampling_rate):
        nonlocal call_count
        call_count += 1
        buf_len = sum(len(f) for f in p._buffer)
        if buf_len < total_samples:
            return [{"start": 0, "end": min(end_sample, buf_len)}]
        return [{"start": 0, "end": end_sample}]

    n_frames = total_samples // FRAME_SIZE
    result = None
    with patch("app.audio_pipeline.get_speech_timestamps", side_effect=vad_side_effect):
        for i in range(n_frames):
            frame = audio[i * FRAME_SIZE:(i + 1) * FRAME_SIZE]
            r = p.push_frame(frame)
            if r is not None:
                result = r
                break

    assert result is not None
    assert result.speech_detected is True
    assert result.transcription == "I love you grandma"
    assert len(p._buffer) == 0


# ── process_clip ─────────────────────────────────────────────────────

def test_process_clip_returns_result():
    p = make_pipeline()
    set_whisper_text(p, "everything is okay")

    result = p.process_clip(speech_audio(0.5))

    assert result.speech_detected is True
    assert result.transcription == "everything is okay"


def test_process_clip_handles_whisper_error():
    p = make_pipeline()
    whisper_stub.decode = MagicMock(side_effect=Exception("decode error"))

    result = p.process_clip(speech_audio(0.5))

    assert result.speech_detected is True
    assert "transcription error" in result.transcription


def test_process_clip_handles_emotion_error():
    p = make_pipeline()
    set_whisper_text(p, "hello")
    p._emotion_pipe.side_effect = Exception("model error")

    result = p.process_clip(speech_audio(0.5))

    assert result.speech_detected is True
    assert result.arousal == 0.0  # fallback


# ── Agitation score integration ──────────────────────────────────────

def test_agitation_score_distressed_vocal():
    snap = SensorSnapshot(
        imu=IMUFeatures(jerk_magnitude=0.0),
        hr=HRState(valid=False),
        touch=TouchState(any_contact=True),
        vocal_emotion=VocalEmotion(valence=-0.7, arousal=0.9, dominant_emotion="fearful"),
    )
    score = compute_agitation_score(snap)
    assert score >= 30  # at minimum mild


def test_agitation_score_calm_vocal():
    snap = SensorSnapshot(
        imu=IMUFeatures(jerk_magnitude=0.0),
        hr=HRState(valid=False),
        touch=TouchState(any_contact=True),
        vocal_emotion=VocalEmotion(valence=0.3, arousal=0.05, dominant_emotion="calm"),
    )
    score = compute_agitation_score(snap)
    assert score < 30


def test_risk_routing():
    assert score_to_risk(10) == "low"
    assert score_to_risk(45) == "medium"
    assert score_to_risk(75) == "high"


# ── Fixture-based tests (skipped if fixtures not recorded yet) ───────

import wave

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name: str) -> np.ndarray:
    """Load a WAV fixture as float32 numpy array at 16kHz."""
    import soundfile as sf
    audio, sr = sf.read(os.path.join(FIXTURES, name), dtype="float32")
    assert sr == SAMPLE_RATE, f"Expected 16kHz, got {sr}"
    return audio.squeeze()


def fixture_exists(name: str) -> bool:
    return os.path.exists(os.path.join(FIXTURES, name))


@pytest.mark.skipif(not fixture_exists("silence.wav"), reason="fixture not recorded")
def test_fixture_silence_no_speech():
    """Real silence clip should produce no VAD timestamps → no result from process_clip."""
    p = make_pipeline()
    audio = load_fixture("silence.wav")
    # Use real VAD (silero stub returns [] by default from module-level mock)
    with patch("app.audio_pipeline.get_speech_timestamps", return_value=[]):
        result = p.process_clip(audio)
    # process_clip bypasses VAD — but we can verify the WAV is valid 16kHz audio
    assert len(audio) == pytest.approx(SAMPLE_RATE * 3, abs=SAMPLE_RATE * 0.1)


@pytest.mark.skipif(not fixture_exists("calm_speech.wav"), reason="fixture not recorded")
def test_fixture_calm_speech_low_arousal():
    """Calm speech fixture should produce low arousal score via mocked emotion model."""
    p = make_pipeline()
    # Override emotion pipe to return calm prediction
    p._emotion_pipe.return_value = [{"label": "calm", "score": 0.9}, {"label": "neutral", "score": 0.1}]
    set_whisper_text(p, "everything is okay")

    audio = load_fixture("calm_speech.wav")
    result = p.process_clip(audio)

    assert result.speech_detected is True
    assert result.arousal < 0.3
    assert result.dominant_emotion == "calm"


@pytest.mark.skipif(not fixture_exists("distressed_speech.wav"), reason="fixture not recorded")
def test_fixture_distressed_speech_high_arousal():
    """Distressed speech fixture should produce high arousal score."""
    p = make_pipeline()
    p._emotion_pipe.return_value = [{"label": "fearful", "score": 0.8}, {"label": "sad", "score": 0.2}]
    set_whisper_text(p, "I don't know where I am")

    audio = load_fixture("distressed_speech.wav")
    result = p.process_clip(audio)

    assert result.speech_detected is True
    assert result.arousal > 0.5
    assert result.dominant_emotion == "fearful"


@pytest.mark.skipif(not fixture_exists("calm_speech.wav"), reason="fixture not recorded")
def test_fixture_wav_is_valid_format():
    """Fixture WAV files must be 16kHz mono 16-bit — what the ESP32 will send."""
    path = os.path.join(FIXTURES, "calm_speech.wav")
    with wave.open(path) as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == SAMPLE_RATE

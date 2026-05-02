from dataclasses import dataclass

import librosa
import numpy as np


@dataclass
class AcousticFeatures:
    f0_mean: float           # mean fundamental frequency (Hz), 0 if unvoiced
    f0_std: float            # std of F0
    jitter: float            # cycle-to-cycle F0 variation (0-1)
    shimmer: float           # cycle-to-cycle amplitude variation (0-1)
    speaking_rate: float     # syllables per second (approx via energy envelope)
    pause_count: int         # number of pauses > 200ms
    pause_rate: float        # pauses per second
    mean_pause_duration: float  # mean pause duration in seconds
    hnr: float               # harmonics-to-noise ratio (dB)


_ZERO = AcousticFeatures(0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0, 0.0, 0.0)


class AcousticExtractor:
    def extract(self, audio: np.ndarray, sr: int = 16000) -> AcousticFeatures:
        if audio.size == 0:
            return _ZERO

        duration = len(audio) / sr

        # F0
        f0 = librosa.yin(audio, fmin=75, fmax=400, sr=sr)
        voiced = f0[f0 > 0]
        if voiced.size < 2:
            return _ZERO

        f0_mean = float(voiced.mean())
        f0_std = float(voiced.std())
        jitter = float(np.abs(np.diff(voiced)).mean() / f0_mean) if f0_mean > 0 else 0.0

        # RMS per frame
        rms = librosa.feature.rms(y=audio)[0]  # shape: (n_frames,)
        mean_rms = float(rms.mean())
        shimmer = float(np.abs(np.diff(rms)).mean() / mean_rms) if mean_rms > 0 else 0.0

        # Speaking rate via energy envelope peaks
        hop = 512
        peaks = librosa.util.peak_pick(rms, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.02, wait=8)
        speaking_rate = len(peaks) / duration if duration > 0 else 0.0

        # Pauses: RMS frames below 1% of max
        max_rms = float(rms.max())
        if max_rms == 0:
            return _ZERO
        silence_mask = rms < 0.01 * max_rms
        frame_dur = hop / sr
        min_frames = int(np.ceil(0.2 / frame_dur))  # 200ms

        pause_durations: list[float] = []
        count = 0
        for val in silence_mask:
            if val:
                count += 1
            else:
                if count >= min_frames:
                    pause_durations.append(count * frame_dur)
                count = 0
        if count >= min_frames:
            pause_durations.append(count * frame_dur)

        pause_count = len(pause_durations)
        pause_rate = pause_count / duration if duration > 0 else 0.0
        mean_pause_duration = float(np.mean(pause_durations)) if pause_durations else 0.0

        # HNR via autocorrelation on voiced frames
        frame_len = 2048
        frames = librosa.util.frame(audio, frame_length=frame_len, hop_length=hop)
        # voiced frame indices (align to f0 length)
        n = min(frames.shape[1], len(f0))
        voiced_idx = np.where(f0[:n] > 0)[0]
        if voiced_idx.size == 0:
            hnr = 0.0
        else:
            ratios = []
            for i in voiced_idx:
                frame = frames[:, i].astype(float)
                ac = np.correlate(frame, frame, mode="full")[frame_len - 1:]
                if ac[0] == 0:
                    continue
                peak_idx = int(np.argmax(ac[1:]) + 1)
                peak = ac[peak_idx]
                noise = ac[0] - peak
                if noise > 0:
                    ratios.append(10 * np.log10(peak / noise))
            hnr = float(np.mean(ratios)) if ratios else 0.0

        return AcousticFeatures(
            f0_mean=f0_mean,
            f0_std=f0_std,
            jitter=jitter,
            shimmer=shimmer,
            speaking_rate=speaking_rate,
            pause_count=pause_count,
            pause_rate=pause_rate,
            mean_pause_duration=mean_pause_duration,
            hnr=hnr,
        )


_extractor = AcousticExtractor()


def extract_acoustic(audio: np.ndarray, sr: int = 16000) -> AcousticFeatures:
    return _extractor.extract(audio, sr)

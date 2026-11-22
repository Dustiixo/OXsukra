"""Audio DSP and deterministic sample-accurate transport for VELA Water's Edge M1.

The playback device is deliberately optional so processing can be tested offline.
"""
from __future__ import annotations
import os
import subprocess
import threading
from queue import SimpleQueue
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import soundfile as sf

RATE = 44100


def stereo(data: np.ndarray) -> np.ndarray:
    x = np.asarray(data, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[1] < 1:
        raise ValueError("Expected mono or multichannel audio")
    if x.shape[1] == 1:
        return np.repeat(x, 2, axis=1)
    return x[:, :2].copy()


def resample(data: np.ndarray, old_rate: int, new_rate: int = RATE) -> np.ndarray:
    x = stereo(data)
    if old_rate == new_rate:
        return x
    from scipy.signal import resample_poly
    from math import gcd
    d = gcd(old_rate, new_rate)
    return resample_poly(x, new_rate // d, old_rate // d, axis=0).astype(np.float32)


def read_audio(filename: str | Path) -> np.ndarray:
    filename = str(filename)
    if not os.path.isfile(filename):
        raise FileNotFoundError(filename)
    try:
        data, sr = sf.read(filename, dtype="float32", always_2d=True)
    except Exception as error:
        # FFmpeg is optional; WAV/FLAC/OGG are handled by bundled soundfile.
        try:
            p = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", filename,
                "-f", "f32le", "-acodec", "pcm_f32le", "-ar", str(RATE), "-ac", "2", "pipe:1"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90, check=True)
            return np.frombuffer(p.stdout, dtype="<f4").reshape(-1, 2).copy()
        except Exception:
            raise RuntimeError(f"Could not decode {Path(filename).name}. Try WAV/FLAC/OGG, or install FFmpeg for MP3. Original error: {error}") from error
    if len(data) == 0:
        raise ValueError("The selected audio file is empty")
    return resample(data, sr)


def write_audio(path: str | Path, audio: np.ndarray) -> None:
    sf.write(str(path), stereo(audio), RATE, subtype="PCM_16")


def get_loop_frames(bpm: float, bars: int) -> int:
    if not (55 <= float(bpm) <= 220):
        raise ValueError("BPM must be between 55 and 220")
    return int(round(RATE * 60.0 / float(bpm) * 4 * int(bars)))


def wrap_to_loop(data: np.ndarray | None, frames: int) -> np.ndarray:
    if data is None or len(data) == 0:
        return np.zeros((frames, 2), dtype=np.float32)
    x = stereo(data)
    if len(x) >= frames:
        return x[:frames].copy()
    reps = (frames + len(x) - 1) // len(x)
    return np.tile(x, (reps, 1))[:frames].copy()


def audio_summary(data: np.ndarray | None, bpm: float) -> dict:
    if data is None or len(data) == 0:
        return {"rms": 0, "peak": 0, "onsets": [], "chroma": 0, "pitch_confidence": 0}
    mono = stereo(data).mean(axis=1)
    rms = float(np.sqrt(np.mean(mono * mono) + 1e-15))
    peak = float(np.max(np.abs(mono)))
    hop = 512
    # Energy transients: transparent, fast, deterministic onset estimator.
    usable = len(mono) // hop * hop
    if usable == 0:
        return {"rms": rms, "peak": peak, "onsets": [], "chroma": 0, "pitch_confidence": 0}
    env = np.sqrt((mono[:usable].reshape(-1, hop) ** 2).mean(axis=1))
    diff = np.maximum(0, np.diff(env, prepend=env[0]))
    threshold = float(max(np.quantile(diff, .85), .002))
    mask = (diff > threshold) & (diff >= np.roll(diff, 1)) & (diff >= np.roll(diff, -1))
    starts = np.flatnonzero(mask)
    # Coarse global dominant pitch-class estimate; not transcription or stem separation.
    seg = mono[:min(len(mono), RATE * 6)]
    if len(seg) > 2048:
        nfft = min(65536, len(seg))
        part = seg[:nfft] * np.hanning(nfft)
        spectrum = abs(np.fft.rfft(part))
        freqs = np.fft.rfftfreq(nfft, 1 / RATE)
        ids = np.where((freqs >= 55) & (freqs <= 1200))[0]
        energy = np.zeros(12)
        if len(ids):
            pcs = np.mod(np.rint(69 + 12 * np.log2(freqs[ids] / 440.)).astype(int), 12)
            np.add.at(energy, pcs, spectrum[ids])
        chroma = int(energy.argmax())
        confidence = float(energy.max() / max(energy.sum(), 1e-8))
    else:
        chroma, confidence = 0, 0.
    return {"rms": round(rms, 5), "peak": round(peak, 5),
            "onsets": [round(int(v) * hop / RATE, 3) for v in starts[:120]],
            "chroma": chroma, "pitch_confidence": round(confidence, 3)}


@dataclass
class TransportEvent:
    kind: str
    frame: int
    response_id: str | None = None


class Transport:
    """Offline-testable mixer; Windows audio output is a separate stream adapter.

    render() is owned by the audio stream callback. Control writes are locked.
    The callback does not wait for inference/generation/file IO.
    """
    def __init__(self, bpm=120., bars=8):
        self.lock = threading.RLock()
        self.events: SimpleQueue[TransportEvent] = SimpleQueue()
        self.position = 0
        self.playing = False
        self.a = None
        self.b = None
        self.active = None
        self.active_id = None
        self.previous = None
        self.pending = None
        self.pending_id = None
        self.pending_at = None
        self.previous_on_swap = None
        self.fade_left = 0
        self.fade_total = int(RATE * 0.18)
        self.volume = 0.65
        self.crossfade = 0.0
        self.response_gain = .75
        self.compare_original = False
        self.loops = 0
        self.set_timing(bpm, bars)

    def set_timing(self, bpm, bars):
        with self.lock:
            self.bpm = float(bpm)
            self.bars = int(bars)
            self.frames = get_loop_frames(self.bpm, self.bars)
            self.bar_frames = get_loop_frames(self.bpm, 1)
            self.position = 0
            self.loops = 0
            self.pending_at = None
            self.pending = None
            self.a = wrap_to_loop(self.a, self.frames) if self.a is not None else None
            self.b = wrap_to_loop(self.b, self.frames) if self.b is not None else None
            self.active = wrap_to_loop(self.active, self.frames) if self.active is not None else None

    def set_deck(self, deck: str, data: np.ndarray | None):
        with self.lock:
            if deck not in ('a', 'b'):
                raise ValueError("deck must be a or b")
            setattr(self, deck, wrap_to_loop(data, self.frames) if data is not None else None)

    def queue_response(self, data: np.ndarray, response_id: str, quantize_bars: int = 1):
        """Queue a response at the next bar or 2/4/8-bar phrase boundary.

        Defaults to the legacy next-bar behavior; generation remains outside the
        audio callback and the proposal is not automatically approved.
        """
        if type(quantize_bars) is not int or quantize_bars not in (1, 2, 4, 8):
            raise ValueError("quantize_bars must be one of 1, 2, 4, 8")
        with self.lock:
            self.pending = wrap_to_loop(data, self.frames)
            self.pending_id = response_id
            boundary = self.bar_frames * quantize_bars
            self.pending_at = (self.position // boundary + 1) * boundary
            self.events.put(TransportEvent("queued", self.position, response_id))
            return self.pending_at

    def revert(self):
        with self.lock:
            self.pending = None
            self.pending_id = None
            self.pending_at = None
            self.previous_on_swap = self.active
            self.fade_left = self.fade_total
            self.active, self.active_id = self.previous if self.previous else (None, None)
            self.events.put(TransportEvent("reverted", self.position, self.active_id))

    def render(self, n: int) -> np.ndarray:
        if n <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        with self.lock:
            out = np.zeros((n, 2), dtype=np.float32)
            if not self.playing:
                return out
            done = 0
            while done < n:
                if self.pending is not None and self.pending_at is not None and self.position >= self.pending_at:
                    self.previous = (self.active, self.active_id)
                    self.previous_on_swap = self.active
                    self.fade_left = self.fade_total
                    self.active, self.active_id = self.pending, self.pending_id
                    self.pending, self.pending_id, self.pending_at = None, None, None
                    self.events.put(TransportEvent("applied", self.position, self.active_id))
                until = n - done
                if self.pending_at is not None:
                    until = min(until, max(1, self.pending_at - self.position))
                # Audio loops: track when a full original loop completes.
                until = min(until, self.frames - self.position % self.frames)
                ids = (np.arange(until) + self.position) % self.frames
                chunk = np.zeros((until, 2), dtype=np.float32)
                # Crossfader -1 (A), 0 (balanced), 1 (B)
                fa = np.sqrt((1 - self.crossfade) / 2)
                fb = np.sqrt((1 + self.crossfade) / 2)
                if self.a is not None:
                    chunk += self.a[ids] * fa
                if self.b is not None:
                    chunk += self.b[ids] * fb
                if not self.compare_original and self.active is not None:
                    response = self.active[ids] * self.response_gain
                    if self.fade_left > 0:
                        k = min(until, self.fade_left)
                        ramp = np.minimum(1., np.arange(k, dtype=np.float32) / max(self.fade_total, 1) + (self.fade_total - self.fade_left)/max(self.fade_total,1))
                        response[:k] *= ramp[:, None]
                        if self.previous_on_swap is not None:
                            response[:k] += self.previous_on_swap[ids[:k]] * self.response_gain * (1-ramp)[:, None]
                        self.fade_left -= k
                        if self.fade_left == 0:
                            self.previous_on_swap = None
                    chunk += response
                # Saturating limiter to avoid clipping when decks + generated layer overlap.
                out[done:done + until] = np.tanh(chunk * self.volume * 1.2).astype(np.float32)
                self.position += until
                if self.position % self.frames == 0:
                    self.loops += 1
                    self.events.put(TransportEvent("loop", self.position, self.active_id))
                done += until
                # Commit at the exact sample boundary even if this callback ends
                # there. Otherwise the event/impact marker lags one callback.
                if self.pending is not None and self.pending_at is not None and self.position >= self.pending_at:
                    self.previous = (self.active, self.active_id)
                    self.previous_on_swap = self.active
                    self.fade_left = self.fade_total
                    self.active, self.active_id = self.pending, self.pending_id
                    self.pending, self.pending_id, self.pending_at = None, None, None
                    self.events.put(TransportEvent("applied", self.position, self.active_id))
            return out


def audition_queued_response(transport: Transport, frames: int, *, return_response_id: bool = False, expected_response_id: str | None = None, expected_pending_at: int | None = None):
    """Render a queued musical response offline without advancing live playback.

    This is a non-destructive, deterministic audition of the transport mix,
    including the scheduled phrase entry and its existing crossfade. It does
    not access audio hardware, approve proposals, or modify source recordings.
    """
    if type(frames) is not int or frames < 0 or frames > RATE * 120:
        raise ValueError("frames must be an integer from 0 to 120 seconds")
    with transport.lock:
        if expected_response_id is not None and (transport.pending is None or transport.pending_id != expected_response_id):
            raise ValueError("Approved queued response changed before audition export")
        if expected_pending_at is not None and (transport.pending is None or transport.pending_at != expected_pending_at):
            raise ValueError("Approved queued response schedule changed before audition export")
        preview = Transport(transport.bpm, transport.bars)
        preview.position = transport.position
        preview.loops = transport.loops
        preview.a = transport.a
        preview.b = transport.b
        preview.active = transport.active
        preview.active_id = transport.active_id
        preview.previous = transport.previous
        preview.previous_on_swap = transport.previous_on_swap
        preview.pending = transport.pending
        preview.pending_id = transport.pending_id
        preview.pending_at = transport.pending_at
        preview.fade_left = transport.fade_left
        preview.fade_total = transport.fade_total
        preview.volume = transport.volume
        preview.crossfade = transport.crossfade
        preview.response_gain = transport.response_gain
        preview.compare_original = transport.compare_original
        preview.playing = True
    rendered = preview.render(frames)
    return (rendered, preview.pending_id if preview.pending_id is not None else preview.active_id) if return_response_id else rendered


class BarAudition:
    """Isolated one-shot A/B player; never advances the project transport."""
    def __init__(self, before, after):
        self.buffers = {'a': stereo(before), 'b': stereo(after)}
        if not len(self.buffers['a']) or self.buffers['a'].shape != self.buffers['b'].shape:
            raise ValueError('Audition buffers must have equal nonzero length')
        self.lock = threading.RLock()
        self.playing = False
        self.choice = 'a'
        self.position = 0
        self.loop_region = None  # optional half-open sample interval, independent of main transport

    def set_loop_region(self, start_frame: int, end_frame: int):
        """Enable a bounded, repeating A/B interval without modifying either buffer."""
        if (type(start_frame) is not int or type(end_frame) is not int
                or not 0 <= start_frame < end_frame <= len(self.buffers['a'])):
            raise ValueError('Loop region must be a nonempty interval within the audition')
        with self.lock:
            self.loop_region = (start_frame, end_frame)
            self.position = start_frame

    def clear_loop_region(self):
        """Restore the legacy one-shot preview behavior."""
        with self.lock:
            self.loop_region = None
            self.position = 0

    def select(self, choice, start_frame: int = 0):
        """Select either audition from one sample-accurate, matching cue point.

        The default preserves the original start-at-zero playback behavior.
        """
        if choice not in self.buffers:
            raise ValueError('Choose A or B')
        if type(start_frame) is not int or not 0 <= start_frame < len(self.buffers['a']):
            raise ValueError('Cue frame must be within the audition interval')
        with self.lock:
            if self.loop_region is not None and not self.loop_region[0] <= start_frame < self.loop_region[1]:
                raise ValueError('Cue frame must be within the active loop region')
            self.choice = choice
            self.position = start_frame

    def render(self, frames):
        out = np.zeros((frames, 2), dtype=np.float32)
        with self.lock:
            if not self.playing:
                return out
            source = self.buffers[self.choice]
            if self.loop_region is not None:
                start, end = self.loop_region
                filled = 0
                while filled < frames:
                    n = min(frames - filled, end - self.position)
                    out[filled:filled+n] = source[self.position:self.position+n] * .65
                    filled += n
                    self.position += n
                    if self.position == end:
                        self.position = start
            else:
                n = min(frames, len(source) - self.position)
                out[:n] = source[self.position:self.position+n] * .65
                self.position += n
                if self.position == len(source):
                    self.playing = False
        return out


class AudioDevice:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.stream = None

    def start(self):
        import sounddevice as sd
        if self.stream is None:
            def callback(outdata, frames, time_info, status):
                try:
                    outdata[:] = self.transport.render(frames)
                except Exception:
                    outdata.fill(0)
            self.stream = sd.OutputStream(samplerate=RATE, channels=2, dtype="float32", blocksize=1024, callback=callback, latency="high")
            self.stream.start()
        self.transport.playing = True

    def stop(self):
        self.transport.playing = False

    def close(self):
        self.transport.playing = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class Microphone:
    def __init__(self):
        self.stream = None
        self.blocks = []
        self.recording = False

    def start(self):
        import sounddevice as sd
        self.blocks = []
        def cb(indata, frames, time_info, status):
            self.blocks.append(indata.copy())
        self.stream = sd.InputStream(samplerate=RATE, channels=1, blocksize=1024, callback=cb)
        self.stream.start()
        self.recording = True

    def stop(self):
        if self.stream is not None:
            self.stream.stop(); self.stream.close(); self.stream = None
        self.recording = False
        if not self.blocks:
            raise ValueError("No microphone samples captured")
        return stereo(np.concatenate(self.blocks, axis=0))

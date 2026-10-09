"""Play the bundled audio assets through Windows Media Control Interface."""
import ctypes
import os
import tempfile
import wave
from array import array
from pathlib import Path


SOUND_FILES = {
    "countdown": "countdown.mp3",
    "win": "win.mp3",
    "lose": "lose.mp3",
    "draw": "draw.mp3",
    "match": "match.wav",
}


class AudioManager:
    def __init__(self, volume: float = 0.8) -> None:
        if os.name != "nt":
            raise OSError("The desktop audio player requires Windows.")
        self._mci = ctypes.WinDLL("winmm")
        self._mci.mciSendStringW.argtypes = (
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p,
        )
        self._mci.mciSendStringW.restype = ctypes.c_uint
        self._sounds: dict[str, tuple[str, str, Path]] = {}
        self._temporary_audio = tempfile.TemporaryDirectory(prefix="handplay-audio-")
        self.available = False
        self.enabled = False
        self.volume = min(max(volume, 0.0), 1.0)

        try:
            for name, filename in SOUND_FILES.items():
                path = Path(__file__).resolve().parent.parent / "assets" / "sounds" / filename
                signature = path.read_bytes()[:4]
                if signature == b"RIFF":
                    media_type = "waveaudio"
                    playback_path = self._scaled_wave(name, path, self.volume)
                elif signature[:1] == b"\xff" or signature[:3] == b"ID3":
                    media_type = "mpegvideo"
                    playback_path = path
                else:
                    raise ValueError(f"Unsupported sound-file format: {path}")
                alias = f"rps_{name}"
                self._send(f'open "{playback_path}" type {media_type} alias {alias}')
                self._sounds[name] = (alias, media_type, path)
            self.available = True
            self.set_volume(self.volume)
            self.enabled = True
        except (OSError, ValueError) as error:
            self.close()
            print(f"[Audio] Sound effects are unavailable: {error}")

    def _send(self, command: str) -> None:
        error = self._mci.mciSendStringW(command, None, 0, None)
        if error:
            message = ctypes.create_unicode_buffer(256)
            self._mci.mciGetErrorStringW(error, message, len(message))
            raise OSError(f"{command}: {message.value}")

    def _scaled_wave(self, name: str, source: Path, volume: float) -> Path:
        target = Path(self._temporary_audio.name) / f"{name}-{round(volume * 100)}.wav"
        with wave.open(str(source), "rb") as original:
            if original.getcomptype() != "NONE" or original.getsampwidth() != 2:
                raise ValueError(f"Expected uncompressed 16-bit PCM audio: {source}")
            params = original.getparams()
            samples = array("h")
            samples.frombytes(original.readframes(original.getnframes()))
        samples = array("h", (round(sample * volume) for sample in samples))
        with wave.open(str(target), "wb") as scaled:
            scaled.setparams(params)
            scaled.writeframes(samples.tobytes())
        return target

    def play(self, name: str) -> None:
        if name not in SOUND_FILES:
            raise ValueError(f"Unknown sound effect: {name!r}")
        if self.available and self.enabled:
            alias = self._sounds[name][0]
            self._send(f"stop {alias}")
            self._send(f"play {alias} from 0")

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled and self.available)
        if not self.enabled and self.available:
            for alias, _, _ in self._sounds.values():
                self._send(f"stop {alias}")

    def set_volume(self, volume: float) -> None:
        self.volume = min(max(volume, 0.0), 1.0)
        if self.available:
            level = round(self.volume * 1000)
            for name, (alias, media_type, source) in self._sounds.items():
                if media_type == "waveaudio":
                    self._send(f"close {alias}")
                    scaled_path = self._scaled_wave(name, source, self.volume)
                    self._send(
                        f'open "{scaled_path}" type waveaudio alias {alias}'
                    )
                else:
                    self._send(f"setaudio {alias} volume to {level}")

    def close(self) -> None:
        for alias, _, _ in self._sounds.values():
            try:
                self._send(f"stop {alias}")
                self._send(f"close {alias}")
            except OSError as error:
                print(f"[Audio] Could not close sound device {alias}: {error}")
        self._sounds.clear()
        self.available = False
        self.enabled = False
        self._temporary_audio.cleanup()

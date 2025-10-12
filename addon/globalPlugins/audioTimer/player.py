import threading
import wave
from pathlib import Path

import config
from nvwave import AudioPurpose, WavePlayer


class Player(WavePlayer):
    def __init__(self):
        super().__init__()

    @classmethod
    def play_file(self, file_path: Path):
        thread = threading.Thread(target=self._play_file_blocking, args=[file_path])
        thread.start()

    @classmethod
    def _play_file_blocking(cls, file_path: Path):
        f = wave.open(str(file_path), "r")
        player = WavePlayer(
            channels=f.getnchannels(),
            samplesPerSec=f.getframerate(),
            bitsPerSample=f.getsampwidth() * 8,
            outputDevice=config.conf["audio"]["outputDevice"],
            wantDucking=False,
            purpose=AudioPurpose.SOUNDS,
        )
        while True:
            chunk = f.readframes(4096)
            if not chunk:
                break
            player.feed(chunk)
        f.close()
        player.idle()
        player.close()

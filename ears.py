import pvporcupine
import pvleopard
from pvrecorder import PvRecorder
import os
from dotenv import load_dotenv
load_dotenv()
from threading import Thread

from _utils import you_speak

class Ears:
    def __init__(self):
        self.access_key = os.environ.get("PICOVOICE_KEY")
        self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=["hey howey"], keyword_paths=["models/Hey-Howey_en_mac_v2_2_0.ppn"])
        self.leopard = pvleopard.create(access_key=self.access_key)
        self.recorder = None
        self.audio_device_index = -1

        
    def listen_for_wake_word(self):
        try:
            while True:
                pcm = self.audio_stream.read(512)
                pcm = [int(x) for x in pcm]
                pcm_mono = [(pcm[i] + pcm[i+1]) // 2 for i in range(0, len(pcm), 2)]

                keyword_index = self.porcupine.process(pcm_mono)
                if keyword_index >= 0:
                    return True
        except KeyboardInterrupt:
            print("Stopping listening for wake word")
        finally:
            self._cleanup()

    def listen_for_input(self):
        if self.recorder is not None:
            print('>>> Recording ... Press `ENTER` to stop: ')
            pcm = self.recorder.stop()
            try:
                transcript, _ = self.leopard.process(pcm)
                print(transcript)
            except pvleopard.LeopardActivationLimitError:
                print('AccessKey has reached its processing limit.')
            except pvleopard.LeopardInvalidArgumentError:
                print('An error occurred while processing the audio data.')
            print()
            self.recorder = None
        else:
            print('>>> Press `ENTER` to start: ')
            self.recorder = Recorder(self.audio_device_index)
            self.recorder.start()

    def _cleanup(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        if self.leopard is not None:
            self.leopard.delete()

class Recorder(Thread):
    def __init__(self, audio_device_index):
        super().__init__()
        self._pcm = list()
        self._is_recording = False
        self._stop = False
        self._audio_device_index = audio_device_index

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True

        recorder = PvRecorder(frame_length=512, device_index=self._audio_device_index)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())
        recorder.stop()

        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass

        return self._pcm
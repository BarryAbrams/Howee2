import pvporcupine
import pvleopard
from pvrecorder import PvRecorder
import os, time
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
from tabulate import tabulate
from _utils import *

class Ears:
    def __init__(self):
        self.access_key = os.environ.get("PICOVOICE_KEY")
        try:
            self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=["hey howey"], keyword_paths=["models/Hey-Howey_en_mac_v2_2_0.ppn"])
            self.leopard = pvleopard.create(access_key=self.access_key,enable_automatic_punctuation=True)
            self.recorder = PvRecorder(frame_length=512, device_index=-1)
        except:
            self.porcupine = None
            self.leopard = None
            self.recorder = None
            print_c("Picovoice not available. Howee has no ears.", "red")

    def listen_for_wake_word(self):
        try:
            while True and self.recorder is not None:
                pcm = self.recorder.read()
                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    return "hey howee"
        except KeyboardInterrupt:
            print("Stopping listening for wake word")
        finally:
            self._cleanup()

    def listen_for_input(self):
        while True and self.recorder is not None:
            try:
                pcm = self.recorder.read()
                transcript, words = self.leopard.process(pcm)
                print(transcript)
                print(tabulate(words, headers=['word', 'start_sec', 'end_sec', 'confidence'], floatfmt='.2f'))
            except pvleopard.LeopardActivationLimitError:
                print('AccessKey has reached its processing limit.')

    def _cleanup(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        
        if self.leopard is not None:
            self.leopard.delete()

        if self.recorder is not None:
            self.recorder.stop()

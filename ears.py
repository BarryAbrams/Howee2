import pvporcupine
import pvleopard
from pvrecorder import PvRecorder
import os, time
import numpy as np
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
from tabulate import tabulate
from _utils import *

class Ears:
    def __init__(self):
        self.socketio = None
        self.access_key = os.environ.get("PICOVOICE_KEY")
        self.recorder = PvRecorder(frame_length=512, device_index=-1)
        self.recorder.start()
        self.high_volume = 0
        self.low_volume = 10000000
        self.last_emit_time = 0
        try:
            self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=["hey howey"], keyword_paths=["models/Hey-Howey_en_mac_v2_2_0.ppn"])
            self.leopard = pvleopard.create(access_key=self.access_key,enable_automatic_punctuation=True)
        except:
            self.porcupine = None
            self.leopard = None
            # self.recorder = None
            print_c("Picovoice not available. Howee has no ears.", "red")

    def listen_for_wake_word(self):
        if self.recorder is None:
            return None

        pcm = self.recorder.read()
        self.emit_state(pcm)
        if self.porcupine:
            keyword_index = self.porcupine.process(pcm)
            if keyword_index >= 0:
                return "hey howee"
        return None

    def listen_for_input(self):
        if self.recorder is None:
            return None

        pcm = self.recorder.read()
        self.emit_state(pcm)
        if self.leopard:
            transcript, words = self.leopard.process(pcm)
            print(transcript)
            print(tabulate(words, headers=['word', 'start_sec', 'end_sec', 'confidence'], floatfmt='.2f'))
        return None

    def _cleanup(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        
        if self.leopard is not None:
            self.leopard.delete()

        if self.recorder is not None:
            self.recorder.stop()

    def emit_state(self, pcm):
        current_time = time.time()
        time_elapsed_since_last_emit = current_time - self.last_emit_time
    
        if time_elapsed_since_last_emit > 0.03:
            if self.socketio:
                rms_value = np.sqrt(np.mean(np.square(pcm)))
                normalized_rms = rms_value / 1.0  

                if normalized_rms < self.low_volume:
                    self.low_volume = normalized_rms

                if normalized_rms > self.high_volume:
                    self.high_volume = normalized_rms

                calibrated = round(normalized_rms/self.high_volume, 3)
         
                self.socketio.emit('ear_change', {'level': calibrated})

            self.last_emit_time = time.time()
import pvporcupine
import pvleopard
import pvcobra
from pvrecorder import PvRecorder
import os, time
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
from tabulate import tabulate
from _utils import *
from pydub import AudioSegment
from array import array
import math
import datetime
import sys
import wave
import numpy as np

class Ears:
    def __init__(self):

        self.access_key = os.environ.get("PICOVOICE_KEY")
        self.buffer = []
        self.silence_duration = 0
        self.voice_detected = False
        self.last_percentage = 0
        self.timeout = 0
        self.purge_files_from_folder('audio')
        os.system(f"amixer -c 3 set Capture 100%")

        try:
            self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=["Hey-Howey"], sensitivities=[0.6] * 1)
            self.leopard = pvleopard.create(access_key=self.access_key,enable_automatic_punctuation=True)
            self.cobra = pvcobra.create(access_key=self.access_key)
            self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
            self.recorder.start()
            # 1/0
        except:
            self.porcupine = None
            self.leopard = None
            self.recorder = None
            self.cobra = None
            print_c("Picovoice not available. Howee has no ears.", "red")

    def listen_for_wake_word(self):
        if self.recorder is None:
            return
        pcm = self.recorder.read()
        keyword_index = self.porcupine.process(pcm)
        if keyword_index >= 0:
            return "hey howee"

    def stop_recorder(self):
        self.recorder.stop()
        self.socketio.emit('on_resume_blinks', {})

    def reset_recorder_wake(self):
        if self.recorder is not None:
            self.recorder.stop()
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()
        self.socketio.emit('on_pause_blinks', {})

    def reset_recorder(self):
        if self.recorder is not None:
            self.recorder.stop()
        self.timeout = 0
        self.voice_detected = False
        self.recorder = PvRecorder(device_index=-1, frame_length=512)
        self.recorder.start()
        self.socketio.emit('on_pause_blinks', {})

    def listen_for_input(self, buffer_duration_seconds=3, silence_threshold=1.5):
        if self.recorder is None:
            return None

        frame = self.recorder.read()

        voice_probability = self.cobra.process(frame)
        percentage = voice_probability * 100

        self.socketio.emit('ear_change', {'level': percentage})
        self.buffer.extend(frame)

        if percentage > 25:
            self.voice_detected = True
            self.silence_duration = 0
            self.timeout = 0
        elif self.voice_detected and percentage < 10:
            self.silence_duration += len(frame) / self.recorder.sample_rate

            if self.silence_duration >= 1:
                transcript, words = self.leopard.process(self.buffer)
                self.save_to_wav(self.buffer, "audio/output.wav")
                self.buffer = []
                self.voice_detected = False
                self.silence_duration = 0
                return transcript
        elif percentage < 10 and not self.voice_detected:
            self.timeout += len(frame) / self.recorder.sample_rate

            if self.timeout >= 60:
                return "go to sleep"
            
        return None

    def save_to_wav(self, buffer, filename="audio/output.wav"):
        np_buffer = np.array(buffer, dtype=np.int16)

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.recorder.sample_rate)
            wf.writeframes(np_buffer.tobytes())

    def _cleanup(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        
        if self.leopard is not None:
            self.leopard.delete()

        if self.recorder is not None:
            self.recorder.stop()

    def purge_files_from_folder(self, folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            
            if os.path.isfile(item_path):
                os.remove(item_path)

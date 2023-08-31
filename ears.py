import pvporcupine
import pvleopard
from pvrecorder import PvRecorder
import os, time
from dotenv import load_dotenv
load_dotenv()
from threading import Thread
from tabulate import tabulate
from _utils import *
from pydub import AudioSegment
from array import array

class Ears:
    def __init__(self):
        self.access_key = os.environ.get("PICOVOICE_KEY")
        self.buffer = []
        self.silence_duration = 0

        try:
            self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=["Hey-Howey"], sensitivities=[0.6] * 1)
            self.leopard = pvleopard.create(access_key=self.access_key,enable_automatic_punctuation=True)
            self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
            self.recorder.start()
        except:
            self.porcupine = None
            self.leopard = None
            self.recorder = None
            print_c("Picovoice not available. Howee has no ears.", "red")

    def listen_for_wake_word(self):
        if self.recorder is None:
            return
        pcm = self.recorder.read()
        keyword_index = self.porcupine.process(pcm)
        if keyword_index >= 0:
            
            return "hey howee"

    def reset_recorder(self):
        if self.recorder is not None:
            self.recorder.stop()
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        self.recorder.start()

    def listen_for_input(self, buffer_duration_seconds=3, silence_threshold=1.5):
        if self.recorder is None:
            return None

        # Keep appending to the buffer
        frame = self.recorder.read()
        self.buffer.extend(frame)
        
        frame_bytes = array('h', frame).tobytes()
        # Check if current frame is silent
        audio_segment = AudioSegment(
            frame_bytes, 
            sample_width=2, 
            frame_rate=self.recorder.sample_rate/2, 
            channels=2)
        

        
        # Threshold can be adjusted based on your mic and environment
        if audio_segment.dBFS < -20:  
            self.silence_duration += len(audio_segment) / 1000.0  # Convert from ms to seconds
        else:
            self.silence_duration = 0
        

        # If we detect enough silence, process the buffer
        if self.silence_duration >= silence_threshold:
            buffer_bytes = array('h', self.buffer).tobytes()
            buffer_audio_segment = AudioSegment(
                buffer_bytes,
                sample_width=2,
                frame_rate=self.recorder.sample_rate/2,
                channels=2)
            buffer_audio_segment.export("buffer_output.wav", format="wav")
            
            transcript, words = self.leopard.process(self.buffer)
            self.buffer = []  # Clear the buffer
            self.silence_duration = 0
            return transcript

        return None

    def _cleanup(self):
        if self.porcupine is not None:
            self.porcupine.delete()
        
        if self.leopard is not None:
            self.leopard.delete()

        if self.recorder is not None:
            self.recorder.stop()

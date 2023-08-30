import threading
import boto3
import queue
import time
import os
import io
import numpy as np
import pygame
from pydub import AudioSegment
from pydub.playback import play
import tempfile

polly = boto3.client('polly', region_name='us-west-2')

from _utils import howee_speak

class Mouth:
    def __init__(self):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()  # Initialize all pygame modules
        pygame.mixer.init()  # Set a consistent sample rate
        self.audio_queue = queue.Queue()
        self.socketio = None
        self.output = 0
        self.output_prev = 1
        self.segments = []  # Initialize as an empty list
        self.current_segment = 0  # Initialize as 0
        self.audio_thread = threading.Thread(target=self._audio_worker)
        self.audio_thread.start()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        while True:
            self.emit_state()
            time.sleep(0.033)

    def speak(self, message):
        howee_speak(message)
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3", VoiceId="Joey")

        if "AudioStream" in voiceResponse:
            if not os.path.exists("audio"):
                os.makedirs("audio")
            with voiceResponse["AudioStream"] as stream:
                data = stream.read()
                timestamp = int(time.time() * 1000)
                base_dir = os.getcwd()
                output_file = os.path.join(base_dir, f"audio/howee_speech_{timestamp}.mp3")
                with open(output_file, "wb") as file:
                    file.write(data)

                self.audio_queue.put(output_file)
        else:
            print("did not work")

    def play_and_analyze(self, filename):
        sound = AudioSegment.from_mp3(filename)
        segment_duration = 33  # in milliseconds
        self.segments = [sound[i:i+segment_duration] for i in range(0, len(sound), segment_duration)]
        self.current_segment = 0

        # Save the entire sound as a temporary WAV file
        with tempfile.NamedTemporaryFile(delete=True) as temp_wav:
            sound.export(temp_wav.name, format="wav")
            pygame.mixer.music.load(temp_wav.name)
            pygame.mixer.music.play()

            start_time = time.time()
            while pygame.mixer.music.get_busy():
                elapsed_time = time.time() - start_time
                self.current_segment = int(elapsed_time * 1000 / segment_duration)
                time.sleep(0.01)  # Sleep for a short duration to prevent busy-waiting

        self.current_segment = len(self.segments)  # reset after playing


    def _play_audio(self, sound):
        play(sound)
        self.current_segment = len(self.segments)  # reset after playing

    def emit_state(self):

        if self.current_segment < len(self.segments):
            segment = self.segments[self.current_segment]
            self.output = segment.rms / 32768  # Normalize RMS value to [0, 1]
            self.current_segment += 1
        else:
            self.output = 0  # No audio is playing

        if self.socketio and self.output != self.output_prev:
            self.socketio.emit('mouth_change', {'level': self.output})
        self.output_prev = self.output

    def _audio_worker(self):
        while True:
            try:
                output_file = self.audio_queue.get()
                self.play_and_analyze(output_file)
                os.remove(output_file)
                self.audio_queue.task_done()
            except Exception as e:
                self.audio_queue.task_done()
                print(f"Error: {e}")


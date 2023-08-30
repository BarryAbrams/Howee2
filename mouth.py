import threading, boto3, pygame, queue, time, os
import sounddevice as sd
import numpy as np
polly = boto3.client('polly', region_name='us-west-2')

from _utils import howee_speak

class Mouth:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.audio_thread = threading.Thread(target=self._audio_worker)
        self.audio_thread.start()
        self.socketio = None
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.output = 0
        self.output_prev = 1
        
    def _run(self):
        while True:
            self.emit_state()
            time.sleep(0.033)
            

    def speak(self, message):
        # Convert message to TTS and play
        howee_speak(message)
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3", VoiceId="Joey")

        if "AudioStream" in voiceResponse:
            if not os.path.exists("audio"):
                os.makedirs("audio")
            with voiceResponse["AudioStream"] as stream:
                data = stream.read()
                timestamp = int(time.time() * 1000)
                base_dir = os.getcwd()
                output_file = os.path.join(base_dir, f"howee_speech_{timestamp}.mp3")
                with open(output_file, "wb") as file:
                    file.write(data)
                    file.close()  # Explicitly close the file

                self.audio_queue.put(output_file)
        else:
            print("did not work")



    def play_audio(self, output_file):
        try:
            # Initialize pygame mixer and play the audio file
            pygame.mixer.init(frequency=int(44100 * 1.15))
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()

            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove(output_file)
        except IOError as error:
            print(error)

    def audio_callback(self, indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        self.output = volume_norm / 10  # Normalize to a value between 0 and 1
        if self.socketio and self.output != self.output_prev:
            self.socketio.emit('mouth_change', {'level': self.output})
        self.output_prev = self.output

    def play_and_analyze(self, filename):
        data, samplerate = sf.read(filename, dtype='float32')
        sd.play(data, samplerate=samplerate, callback=self.audio_callback)
        sd.wait()

    def _audio_worker(self):
        while True:
            # Get the next audio file from the queue and play it
            try:
                output_file = self.audio_queue.get()
                self.play_and_analyze(output_file)
                os.remove(output_file)
                self.audio_queue.task_done()
            except Exception as e:
                self.audio_queue.task_done()
                print(f"Error: {e}")
                
    def emit_state(self):
        if self.socketio:
            # Check if the mixer is initialized
            if pygame.mixer.get_init():
                # Get the current volume level of the mixer
                self.output = pygame.mixer.music.get_volume()
                print(self.output)
                
                if self.output != self.output_prev:
                    self.socketio.emit('mouth_change', {'level': self.output})
                
                self.output_prev = self.output

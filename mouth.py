import threading, boto3, pygame, queue, time, os

polly = boto3.client('polly', region_name='us-west-2')

from _utils import howee_speak

class Mouth:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.audio_thread = threading.Thread(target=self._audio_worker)
        self.audio_thread.start()

    def speak(self, message):
        # Convert message to TTS and play
        howee_speak(message)
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3", VoiceId="Joey")
        if "AudioStream" in voiceResponse:
            with voiceResponse["AudioStream"] as stream:
                timestamp = int(time.time() * 1000)  # Current time in milliseconds
                output_file = f"audio/howee_speech_{timestamp}.mp3"
                with open(output_file, "wb") as file:
                    file.write(stream.read())

                # Add the audio file to the queue
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

    def _audio_worker(self):
        while True:
            # Get the next audio file from the queue and play it
            output_file = self.audio_queue.get()
            self.play_audio(output_file)
            self.audio_queue.task_done()
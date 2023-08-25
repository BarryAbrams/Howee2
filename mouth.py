import threading, boto3, pygame

polly = boto3.client('polly', region_name='us-west-2')

from _utils import howee_speak

class Mouth:
    def speak(self, message):
        # Convert message to TTS and play
        howee_speak(message)
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3", VoiceId="Joey")
        if "AudioStream" in voiceResponse:
            with voiceResponse["AudioStream"] as stream:
                output_file = "audio/howee_speech.mp3"
                with open(output_file, "wb") as file:
                    file.write(stream.read())

                # Start a new thread to play the audio
                audio_thread = threading.Thread(target=self.play_audio, args=(output_file,))
                audio_thread.start()
        else:
            print("did not work")
        pass

    def play_audio(self, output_file):
        # return
        try:
            # Initialize pygame mixer and play the audio file
            pygame.mixer.init(frequency=int(44100 * 1.15))
            pygame.mixer.music.load(output_file)
            pygame.mixer.music.play()

            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except IOError as error:
            print(error)

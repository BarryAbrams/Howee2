import boto3
import os, tempfile, time, queue, threading, random
import pygame
from pydub import AudioSegment
from pydub.playback import play

polly = boto3.client('polly', region_name='us-west-2')

from _utils import howee_speak

class Mouth:
    def __init__(self, done_speaking_callback):
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        pygame.mixer.init()
        self.audio_queue = queue.Queue()
        self.socketio = None
        self.output = 0
        self.output_prev = 1
        self.segments = [] 
        self.current_segment = 0
        self.audio_thread = threading.Thread(target=self._audio_worker)
        self.audio_thread.start()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.unused_sfx_sounds = []
        self.last_deviation_time = 0
        self.done_speaking_callback = done_speaking_callback
        self.volume = 0.5

    def _run(self):
        if not os.path.exists("audio"):
            os.makedirs("audio")
        while True:
            self.emit_state()
            time.sleep(0.5)

    def speak(self, message):
        howee_speak(message)
        voiceResponse = polly.synthesize_speech(Text=message, OutputFormat="mp3", VoiceId="Joey")

        if "AudioStream" in voiceResponse:
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
        segment_duration = 33
        self.segments = [sound[i:i+segment_duration] for i in range(0, len(sound), segment_duration)]
        self.current_segment = 0

        with tempfile.NamedTemporaryFile(delete=True) as temp_wav:
            sound.export(temp_wav.name, format="wav")
            self.change_voice(temp_wav.name, temp_wav.name)
            pygame.mixer.music.load(temp_wav.name)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()

            start_time = time.time()
            while pygame.mixer.music.get_busy():
                elapsed_time = time.time() - start_time
                self.current_segment = int(elapsed_time * 1000 / segment_duration)
                time.sleep(0.1)

        self.current_segment = len(self.segments)

    def change_voice(self, input_path, output_path):
        sound = AudioSegment.from_wav(input_path)
        modified_sound = sound
        current_time = time.time()
        # 1. Pitch Shift
        if True:  # Set to False to disable
            octaves = 0.3
            shift = 2.0
            if len(modified_sound) < 1000 and current_time - self.last_deviation_time > 10:
                random_number = random.random()
                if random_number < 0.25:
                    octaves = 0.6
                    shift = .7
                    self.last_deviation_time = current_time
                if random_number > 0.75:
                    octaves = 0.5
                    shift = 3
                    self.last_deviation_time = current_time
            new_sample_rate = int(sound.frame_rate * (shift ** octaves))
            modified_sound = modified_sound._spawn(modified_sound.raw_data, overrides={"frame_rate": new_sample_rate}).set_frame_rate(modified_sound.frame_rate)
        
        # 2. Reverb (using inbuilt reverb effect of pydub)
        if False:  # Set to False to disable
            modified_sound = self.simple_reverb(modified_sound)

        # 3. Overdrive (Amplify the sound to introduce clipping)
        if False:  # Set to False to disable
            modified_sound = modified_sound + 20  # Adjust the value for more or less distortion

        # 4. Slicing
        if False:  # Set to False to disable
            segment_duration = 10
            segments = [modified_sound[i:i+segment_duration] for i in range(0, len(modified_sound), segment_duration)]
            num_glitch_segments = len(segments) // 25
            
            # Randomly select segments to shuffle
            glitch_indices = random.sample(range(len(segments)), num_glitch_segments)
            glitched_segments = [segments[i] for i in glitch_indices]
            random.shuffle(glitched_segments)

            # Insert the shuffled segments back into their positions
            for i, index in enumerate(glitch_indices):
                segments[index] = glitched_segments[i]

            # Combine the segments
            glitchy = AudioSegment.empty()
            for seg in segments:
                glitchy += seg
            modified_sound = glitchy


        # 5. Add SFX
        if True:  # Set to False to disable
            sfx_directory = "audio/sfx"
            modified_sound = self.add_random_sfx_to_sound(modified_sound, sfx_directory, num_sfx_inserts=1)

        # Export to output path
        modified_sound.export(output_path, format="wav")
        
        return modified_sound

    def simple_reverb(self, sound, num_delays=10, delay_duration=1000, decay_factor=.9):
        """Applies a simple reverb effect to the given sound."""
        result = sound
        for i in range(num_delays):
            delay = (i + 1) * delay_duration
            delayed_sound = sound._spawn(b"\0" * delay).overlay(sound + (-3 * decay_factor * (i + 1)))
            result = result.overlay(delayed_sound)
        return result
    
    def add_random_sfx_to_sound(self, main_sound, sfx_directory, num_sfx_inserts):
        """Add random SFX intermittently to the main sound."""
        # 20% probability of adding SFX
        if random.random() > 0.2:
            return main_sound
        
        # Load all .wav files from the sfx directory if unused_sfx_sounds is empty
        if not self.unused_sfx_sounds:
            sfx_files = [os.path.join(sfx_directory, f) for f in os.listdir(sfx_directory) if f.endswith('.wav')]
            self.unused_sfx_sounds = [AudioSegment.from_wav(sfx_file) for sfx_file in sfx_files]

        # Calculate the intervals to insert the SFX
        duration = len(main_sound)
        # longest_sfx = max(len(sfx) for sfx in self.unused_sfx_sounds)
        
        # Extend the main sound duration to allow the last SFX to play fully
        # extended_duration = duration + longest_sfx
        # silence_needed = extended_duration - duration
        # silence = AudioSegment.silent(duration=silence_needed)
        # main_sound += silence

        # Choose a random SFX from the unused list, remove it from the list
        random_sfx = random.choice(self.unused_sfx_sounds)
        self.unused_sfx_sounds.remove(random_sfx)
        random_sfx = random_sfx - 3

        # Overlay the SFX at the beginning of the main sound
        main_sound = main_sound.overlay(random_sfx, position=0)
        return main_sound


    def _audio_worker(self):
        while True:
            try:
                output_file = self.audio_queue.get()
                self.play_and_analyze(output_file)
                os.remove(output_file)
                self.audio_queue.task_done()
                if self.audio_queue.empty():  # Check if the queue is empty
                    self.queue_emptied_callback()  # Call the callback
            
            except Exception as e:
                self.audio_queue.task_done()
                print(f"Error: {e}")

    def queue_emptied_callback(self):
        if self.done_speaking_callback:
            self.done_speaking_callback()
        # Add any additional logic you want to execute when the queue is emptied


    def emit_state(self):
        if self.current_segment < len(self.segments):
            segment = self.segments[self.current_segment]
            self.output = segment.rms / 32768
            self.current_segment += 1
        else:
            self.output = 0

        if self.socketio and self.output != self.output_prev:
            self.socketio.emit('mouth_change', {'level': self.output})
        self.output_prev = self.output
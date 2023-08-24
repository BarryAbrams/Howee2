import threading, time

from _utils import *
from knowledge import System, OpenAI, Weather
from mouth import Mouth
from ears import Ears

user_input_value = None

def get_input_from_user(prompt):
    global user_input_value
    user_input_value = input_c(prompt)

class Brain:
    def __init__(self, mode='audio'):
        self.mode = mode
        self.mouth = Mouth()
        self.ears = Ears()
        self.knowledge_sources = {
            "system": System(),
            "openai": OpenAI(),
            "weather": Weather()
        }

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        while True:
            wake_word = self._listen_for_wake_word()
            if wake_word:
                self.mouth.speak(self._filter_in_voice("hello!"))
                
                while True: 
                    user_input = self._listen_for_input()
                    if not user_input:
                        break
                    
                    you_speak(user_input)
                    
                    if user_input == 'exit':
                        break

                    response = self._process_input(user_input)
                    self.mouth.speak(response)
                
    def _filter_in_voice(self, message):
        return self.knowledge_sources["openai"].query_voice(message)

    def _listen_for_wake_word(self):
        if self.mode == 'audio':
            detected_word = self.ears.listen_for_wake_word()
            if detected_word:
                you_speak(detected_word)
                return detected_word
        elif self.mode == 'terminal':
            input_word = input_c("Enter wake word (or type 'exit' to quit): ")
            if input_word in ['hey howee', 'exit']:
                you_speak(input_word)
                return input_word

    def _listen_for_input(self):
        if self.mode == 'audio':
            return self.ears.listen_for_input()
        elif self.mode == 'terminal':
            global user_input_value

            user_input_value = None
            input_thread = threading.Thread(target=get_input_from_user, args=("Enter your command (or 'exit' to return to wake word listening): ",))
            input_thread.start()

            end_time = time.time() + 25
            while input_thread.is_alive() and time.time() < end_time:
                time.sleep(0.1)

            if time.time() >= end_time and not user_input_value:
                self.mouth.speak(self._filter_in_voice("I'm going back to sleep. Wake me up when you need me."))
                time.sleep(.1)
                return None

            return user_input_value
        
    def _process_input(self, user_input):
        intent = self.knowledge_sources["openai"].query_intent(user_input)

        if not intent:
            intent_type = "openai"
        output = user_input

        if intent and intent['type'] == "system":
            intent_type = "system"
            output = intent['action']

        if intent and intent['type'] == "weather":
            intent_type = "weather"


        if intent_type in self.knowledge_sources:
            if intent_type == "openai":
                return self.knowledge_sources[intent_type].query(output)
            
            if intent_type == "weather":
                return self._filter_in_voice(self.knowledge_sources["weather"].query(output, intent["action"]))

            response = self.knowledge_sources[intent_type].query(output)
            return self._filter_in_voice(response)

        return "I'm not sure how to handle that request."
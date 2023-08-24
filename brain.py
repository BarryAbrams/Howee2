from knowledge import System, OpenAI
from mouth import Mouth
from ears import Ears

class Brain:
    def __init__(self, mode='audio'):
        self.mode = mode
        self.mouth = Mouth()
        self.ears = Ears()
        self.knowledge_sources = {
            "system": System(),
            "openai": OpenAI()
        }

    def start(self):
        while True:
            wake_word = self._listen_for_wake_word()
            if wake_word:
                self.respond_to_wake_word()
                while True:
                    user_input = self._listen_for_input()
                    self.you_speak(user_input)
                    if user_input == 'exit':
                        break
                    if user_input:
                        intent = self.determine_intent(user_input)
                        response = self.query_knowledge(intent, user_input)
                        self.respond(response)

    def _listen_for_wake_word(self):
        if self.mode == 'audio':
            detected_word = self.ears.listen_for_wake_word()
            if detected_word:
                self.you_speak(detected_word)
                return detected_word
        elif self.mode == 'terminal':
            input_word = input("Enter wake word (or type 'exit' to quit): ")
            if input_word in ['hey howee', 'exit']:
                self.you_speak(input_word)
                return input_word

    def _listen_for_input(self):
        if self.mode == 'audio':
            return self.ears.listen_for_input()
        elif self.mode == 'terminal':
            return input("Enter your command (or 'exit' to return to wake word listening): ")

    def respond(self, response):
        self.howee_speak(response)
        if self.mode == 'audio':
            self.mouth.speak(response)

    def howee_speak(self, text):
        self.print_c("HOWEE: " + text, "cyan")

    def you_speak(self, text):
        self.print_c("YOU: " + text, "green")

    def respond_to_wake_word(self):
        self.respond("Hello!")

    def determine_intent(self, user_input):
        input_data = user_input.lower()
        if "volume" in input_data:
            return "system"
        return "openai"

    def query_knowledge(self, intent, input_data):
        if intent in self.knowledge_sources:
            return self.knowledge_sources[intent].query(input_data)
        return "I'm not sure how to handle that request."

    def print_c(self, text, color):
        color_codes = {
            "black": "\033[30m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m"
        }
        reset_code = "\033[0m"
        print(f"{color_codes[color]}{text}{reset_code}")

import threading, time

from _utils import *
from knowledge import System, OpenAI, Weather
from mouth import Mouth
from ears import Ears
from flask_socketio import SocketIO

user_input_value = None

def get_input_from_user(prompt):
    global user_input_value
    user_input_value = input_c(prompt)

class Brain:
    def __init__(self):
        self.mouth = Mouth()
        self.ears = Ears()
        self.knowledge_sources = {
            "system": System(self.transition),
            "openai": OpenAI(self.transition),
            "weather": Weather(self.transition)
        }
        self.awake_state = AwakeState.ASLEEP
        self.action_state = ActionState.LISTENING
        self.awake_state_prev = AwakeState.ASLEEP
        self.action_state_prev = ActionState.LISTENING
        self.user_input = None
        self.socketio = None

    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.transition(AwakeState.ASLEEP, ActionState.LISTENING)

    def transition(self, awake=None, action=None):
        if awake:
            self.awake_state = awake
        if action:
            self.action_state = action

        self.print_state()
        self.emit_state()

    def print_state(self):
        print(self.awake_state, self.action_state)

    def emit_state(self):
        if self.socketio:
            self.socketio.emit('state_change', {'awake_state': self.awake_state.to_json(), 'action_state': self.action_state.to_json()})

    def _run(self):
        while True:
            if self.awake_state == AwakeState.ASLEEP:
                wake_word = self._listen_for_wake_word() or self.user_input == "hey howee"
                if wake_word:
                    if self.user_input:
                        you_speak(self.user_input)
                        self._filter_in_voice("Hello")
                    self.transition(AwakeState.AWAKE, ActionState.LISTENING)
            elif self.awake_state == AwakeState.AWAKE:
                if self.action_state == ActionState.LISTENING:
                    input_words = self._listen_for_input() or self.user_input
                    if input_words:
                        if self.user_input:
                            you_speak(self.user_input)
                            self.transition(AwakeState.AWAKE, ActionState.PROCESSING)
                            self._process_input(self.user_input)
                elif self.action_state == ActionState.PROCESSING:
                    # this handling will happen within the functions called _process_input from
                    pass
                elif self.action_state == ActionState.TALKING:
                    # this handling will happen within the functions called _process_input from
                    pass
                elif self.action_state == ActionState.IDLE:
                    self.transition(AwakeState.AWAKE, ActionState.LISTENING)
                    pass
            
            self.user_input = None
            self.action_state_prev = self.action_state
            self.awake_state_prev = self.awake_state

            time.sleep(0.01)
            
    def _filter_in_voice(self, message):
        return self.knowledge_sources["openai"].query_voice(message, self.mouth.speak)

    def _listen_for_wake_word(self):
        detected_word = self.ears.listen_for_wake_word()
        if detected_word:
            you_speak(detected_word)
            return detected_word


    def _listen_for_input(self):
        return self.ears.listen_for_input()
               
    def _process_input(self, user_input):
        intent = self.knowledge_sources["openai"].query_intent(user_input)

        intent_type = "openai"  # Default value
        output = user_input

        if intent:
            if intent['type'] == "system":
                intent_type = "system"
                output = intent['action']
            elif intent['type'] == "weather":
                intent_type = "weather"

        if intent_type in self.knowledge_sources:
            if intent_type == "openai":
                words = self.knowledge_sources[intent_type].query(output, self.mouth.speak)
                
            elif intent_type == "weather":
                city = "Champaign"
                if "city" in intent:
                    city = intent["city"]
                words = self._filter_in_voice(self.knowledge_sources["weather"].query(output, intent["action"], city))
            else:
                response = self.knowledge_sources[intent_type].query(output)
                words = self._filter_in_voice(response)

            return words

        return "I'm not sure how to handle that request."
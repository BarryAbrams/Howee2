import threading, time, datetime

from _utils import *
from knowledge import System, OpenAI, Weather, OneAI
from mouth import Mouth
from ears import Ears
# from eyes import Eyes
from flask_socketio import SocketIO

user_input_value = None

def get_input_from_user(prompt):
    global user_input_value
    user_input_value = input_c(prompt)

class Brain:
    def __init__(self):
        self.mouth = Mouth(self._done_speaking_callback)
        self.ears = Ears()
        # self.eyes = Eyes()
        self.knowledge_sources = {
            "system": System(self.transition),
            "openai": OpenAI(self.transition),
            "weather": Weather(self.transition),
            "emotions": OneAI(self.transition)
        }
        self.awake_state = AwakeState.ASLEEP
        self.action_state = ActionState.LISTENING
        self.awake_state_prev = AwakeState.ASLEEP
        self.action_state_prev = ActionState.LISTENING
        self.user_input = None
        self.socketio = None
        self.listening_for_wake_word = False
        self.after_callback_is_awake = True
        self.user_emotions = []
        self.howee_emotions = []
        
    def start(self):
        self.thread = threading.Thread(target=self._run)
        self.thread.start()
        self.transition(AwakeState.ASLEEP, ActionState.LISTENING)
        self.mouth.socketio = self.socketio
        self.ears.socketio = self.socketio
        self.start_emotion_print_thread()

    def transition(self, awake=None, action=None):
        print(awake, action)
        if self.awake_state == AwakeState.ASLEEP and awake == AwakeState.AWAKE:
            self.socketio.emit('on_eye_update', {'awake_state':"awake"})
        elif self.awake_state == AwakeState.AWAKE and awake == AwakeState.ASLEEP:
            self.socketio.emit('on_eye_update', {'awake_state':"asleep"})

        if action == ActionState.IDLE:
            self.socketio.emit('response', {'type':"stop", 'from':"Howee", "message":""})


        if awake:
            self.awake_state = awake
        if action:
            self.action_state = action

        self.print_state()
        self.emit_state()

    def print_state(self):
        # print(self.awake_state, self.action_state)
        pass

    def emit_state(self):
        if self.socketio:
            self.socketio.emit('state_change', {'awake_state': self.awake_state.to_json(), 'action_state': self.action_state.to_json()})

    def _run(self):
        while True:
            if self.awake_state == AwakeState.ASLEEP:
                wake_word = self._listen_for_wake_word() or self.user_input == "hey howee"
                if wake_word:
                    self.ears.stop_recorder()
                    if self.user_input:
                        you_speak(self.user_input)
                    else:
                        you_speak(wake_word)
                    self._filter_in_voice("Hello")
                    self.after_callback_is_awake = True
                    self.transition(AwakeState.AWAKE, ActionState.TALKING)
            elif self.awake_state == AwakeState.AWAKE:
                if self.action_state == ActionState.LISTENING:
                    input_words = self._listen_for_input() or self.user_input
                    if input_words:
                        self.ears.stop_recorder()
                        if self.user_input:
                            you_speak(self.user_input)
                            self._process_input(self.user_input)
                        else:
                            you_speak(input_words)
                            self._process_input(input_words)
                        self.transition(AwakeState.AWAKE, ActionState.PROCESSING)
                        
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
            
            if self.awake_state != ActionState.LISTENING:
                time.sleep(0.01)
            else:
                time.sleep(0.1)


    def _done_speaking_callback(self):
        if self.after_callback_is_awake:
            self.transition(AwakeState.AWAKE, ActionState.LISTENING)
            self.ears.reset_recorder()
        else:
            self.transition(AwakeState.ASLEEP, ActionState.LISTENING)
            self.ears.reset_recorder_wake()
            
    def _filter_in_voice(self, message):
        return self.knowledge_sources["openai"].query_voice(message, self.mouth.speak)

    def _listen_for_wake_word(self):
        detected_word = self.ears.listen_for_wake_word()
        if detected_word:
            self.listening_for_wake_word = False  # Reset the flag when done listening
            return detected_word


    def _listen_for_input(self):
        # pass
        return self.ears.listen_for_input()

    def _prune_old_emotions(self):
        ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)
        self.user_emotions = [event for event in self.user_emotions if datetime.datetime.fromisoformat(event["event"]) > ten_minutes_ago]
        self.howee_emotions = [event for event in self.howee_emotions if datetime.datetime.fromisoformat(event["event"]) > ten_minutes_ago]

    def start_emotion_print_thread(self):
        def emotion_print_loop():
            while True:
                self._print_emotions()
                time.sleep(60)  # Wait for 60 seconds

        # Start the repeating thread
        emotion_thread = threading.Thread(target=emotion_print_loop)
        emotion_thread.start()

    def _print_emotions(self):
        
        # Print and emit for user
        user_data = self.process_emotions(self.user_emotions)
        # Print and emit for Howee
        howee_data = self.process_emotions(self.howee_emotions)

        # Emit to SocketIO if flag is True
        if self.socketio:
            self.socketio.emit('emotions', {"user":user_data, "howee":howee_data})

    def process_emotions(self, emotion_data):
        emotion_summation = {}  # compute this from emotion_data

        for event in emotion_data:
            timestamp = event["event"]
            emotions = event["emotions"]
            emotions_str = ', '.join([f"{emotion_key}:{emotion_value}" for emotion_dict in emotions for emotion_key, emotion_value in emotion_dict.items()])
            
            for emotion_dict in emotions:
                for emotion, value in emotion_dict.items():
                    # Skip the 'neutral' emotion
                    if emotion != 'neutral':
                        emotion_summation[emotion] = emotion_summation.get(emotion, 0) + value

        # If emotion_summation is empty, return a default response
        if not emotion_summation:
            return {
                "predominant_emotion": "none",
                "strength": 0,
                "emotion_summation": {}
            }

        max_emotion = max(emotion_summation, key=emotion_summation.get)
        max_count = emotion_summation[max_emotion]
        total_count = sum(emotion_summation.values())
        strength = max_count / total_count if total_count != 0 else 0

        predominant_emotion_data = {
            "predominant_emotion": max_emotion,
            "strength": strength,
            "emotion_summation": emotion_summation
        }

        return predominant_emotion_data          

    def _process_input(self, user_input):
        intent = self.knowledge_sources["openai"].query_intent(user_input)
        if isinstance(intent, dict):

            def emotion_query_thread():
                emotions = self.knowledge_sources["emotions"].query(user_input)
                timestamp = datetime.datetime.now().isoformat()
                self.user_emotions.append({"event": timestamp, "emotions": emotions})
                self._prune_old_emotions()
                self._print_emotions()

            emotion_thread = threading.Thread(target=emotion_query_thread)
            emotion_thread.start()

            intent_type = "openai"  # Default value
            output = user_input

            self.after_callback_is_awake = True

            if intent:
                if intent['type'] == "system":
                    intent_type = "system"
                    output = intent['action']
                    if output == "sleep":
                        self.after_callback_is_awake = False
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

                def howee_emotion_query_thread():
                    emotions = self.knowledge_sources["emotions"].query(words)
                    timestamp = datetime.datetime.now().isoformat()
                    self.howee_emotions.append({"event": timestamp, "emotions": emotions})
                    self._prune_old_emotions()
                    self._print_emotions()

                emotion_thread = threading.Thread(target=howee_emotion_query_thread)
                emotion_thread.start()

                return words

        else:
            words = self._filter_in_voice("I didn't catch that. Sorry.")

                
        print(f"Unexpected intent type: {intent}")
        return "I'm not sure how to handle that request."
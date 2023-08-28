import os
from dotenv import load_dotenv
load_dotenv()

class Knowledge:
    def __init__(self, transition_state_callback):
        self.transition_state_callback = transition_state_callback
        pass

    def set_state(self, awake_state, action_state):
        if self.transition_state_callback:
            self.transition_state_callback(awake_state, action_state)

    def _get_env(self, key):
        return os.environ.get(key)

    def query(self, input):
        pass

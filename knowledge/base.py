import os
from dotenv import load_dotenv
load_dotenv()

class Knowledge:
    def __init__(self):
        pass

    def _get_env(self, key):
        return os.environ.get(key)

    def query(self, input):
        pass

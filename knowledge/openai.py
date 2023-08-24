from .base import Knowledge

class OpenAI(Knowledge):
    def query(self, input):
        return f"OPEN AI query - {input}"
        pass

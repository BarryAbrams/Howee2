from .base import Knowledge

class System(Knowledge):
    def query(self, input):
        return f"SYSTEM query - {input}"
        pass

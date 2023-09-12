from .base import Knowledge
from _utils import *
import requests, json

class OneAI(Knowledge):
    def __init__(self, transition_state_callback):
        super().__init__(transition_state_callback)
        self.oneai_key = self._get_env("ONEAI_KEY")
        self.history = []

    def query(self, input):
        url = "https://api.oneai.com/api/v0/pipeline"

        payload = {
            "input_type": "auto-detect",
            "output_type": "text",
            "encoding": "utf8",
            "content_type": "text/plain",
            "multilingual": {
                "enabled": False,
                "allowed_input_languages": ["ALL"],
                "override_language_detection": False
            },
            "include_empty_outputs": False,
            "csv_params": {
                "skip_rows": 0,
                "columns": ["input"]
            },
            "steps": [{ "skill": "emotions" }],
            "input": input
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.oneai_key
        }

        response = requests.post(url, json=payload, headers=headers)

        # Convert the response to a dictionary
        data = json.loads(response.text)

        # Extract the labels section which contains emotions
        labels = data.get('output', [{}])[0].get('labels', [])

        # Count the occurrences of each emotion
        emotion_counts = {}
        for label in labels:
            if label.get('type') == 'emotion':
                emotion_name = label.get('name')
                emotion_counts[emotion_name] = emotion_counts.get(emotion_name, 0) + 1

        # Print the results
        if not emotion_counts:
            return [{'neutral': 1}]

        # Convert the dictionary to an array of dictionaries for each emotion and its count
        emotion_array = [{emotion: count} for emotion, count in emotion_counts.items()]

        return emotion_array

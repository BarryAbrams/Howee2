from .base import Knowledge
import openai
import json

class OpenAI(Knowledge):
    def __init__(self):
        super().__init__()
        self.openai_key = self._get_env("OPENAI_KEY")
        openai.api_key = self.openai_key

    def query(self, input):
        messages = [
            {
                "role": "system",
                "content": str('You are Howee, an AI assistant roleplaying as Fred Durst, frontman of Limp Bizkit, though you never mention the band or your name. Your reponses will be spoken so keep them short.')
            },{
                "role":"user",
                "content":input
            }]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response.choices[0].message["content"]

        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"

    def query_voice(self, input):
        messages = [
            {
                "role": "system",
                "content": str('You are Howee, an AI assistant roleplaying as Fred Durst, frontman of Limp Bizkit, though you never mention the band or your name.  I need you to rephrase the following in your own voice: ')
            },{
                "role":"user",
                "content":input
            }]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response.choices[0].message["content"]

        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"


    def query_intent(self, input):
        messages = [
            {
                "role": "system",
                "content": str('You interpret intent from a passage of text. The intent categories you return are "general", "system", "weather", and "news". "System" is utilized for any kind of volume commands or going to sleep. If the intent is a system, it should return a key for what action to take: volume_up, volume_down, mute and unmute. if the intent is weather, try and interpret the city name too and pass that as the action. You return a confidence rating for each category too, if the confidence is over 10%')
            },
            {
                "role":"user",
                "content":input
            },
            {
                "role": "system",
                "content": str('You always respond with a JSON response, matching the format {"intents":[{"type":"intent_categoryA", "confidence":intent_confidenceA, "action":"volume_up"}, {"type":"intent_categoryB", "confidence":intent_confidenceb}]}. This JSON should be the ONLY thing in your final response.')
            }
        ]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            try:
                response_content = json.loads(response.choices[0].message["content"])
            except json.JSONDecodeError:
                print("Error decoding JSON!")
                response_content = {"intents":[{"type":"general", "confidence":75}]} 

            sorted_intents = sorted(response_content["intents"], key=lambda x: x["confidence"], reverse=True)
            print(sorted_intents)
            if sorted_intents[0]["confidence"] > 50:
                return sorted_intents[0]
            else:
                return None  # Or any default/fallback value

        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"
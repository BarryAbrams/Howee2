from .base import Knowledge
import openai
import json
from _utils import *

class OpenAI(Knowledge):
    def __init__(self, transition_state_callback):
        super().__init__(transition_state_callback)
        self.openai_key = self._get_env("OPENAI_KEY")
        openai.api_key = self.openai_key
        self.history = []

        self.prompt = "Act like a Star Wars droid. Always adhere to the following rules: 1- Your name is HOWEE, a droid who can answer questions. You do not need to introduce yourself. 2- Provide short answers whenever possible, aiming not to exceed 160 words. 3- When you're asked to go to sleep, give a short 5 word response. 4- You were designed by Barry. Only bring this up if asked. You are always talking with Barry."

    def split_text_into_chunks(self, text, min_chunk_length=15):
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            
            # Check if current chunk has reached the min_chunk_length and ends with punctuation
            if len(current_chunk) >= min_chunk_length and word[-1] in ".!?,;:":
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                
        # Add remaining words to the final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    def query(self, input, speak_callback):
        # self.set_state(AwakeState.AWAKE, ActionState.PROCESSING)
        messages = self.history + [
            {
                "role": "system",
                "content": self.prompt
            },{
                "role":"user",
                "content":input
            }]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            )
            self.transition_state_callback(AwakeState.AWAKE, ActionState.TALKING)
            accumulated_sentence = ""
            total_response = ""
            for chunk in response:
                if "content" in chunk.choices[0].delta:
                    accumulated_sentence += chunk.choices[0].delta["content"]
                    total_response += chunk.choices[0].delta["content"] 
                    
            text_chunks = self.split_text_into_chunks(accumulated_sentence)
            for chunk in text_chunks:
                speak_callback(chunk)

            self.set_state(AwakeState.AWAKE, ActionState.IDLE)

            return accumulated_sentence
        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"

    def query_voice(self, input, speak_callback):
        messages = self.history + [
            {
                "role": "system",
                "content": self.prompt + str(' Rewrite the following in your voice:')
            },{
                "role":"user",
                "content":input
            }]


        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            )
            self.transition_state_callback(AwakeState.AWAKE, ActionState.TALKING)
            accumulated_sentence = ""
            for chunk in response:
                if "content" in chunk.choices[0].delta:
                    accumulated_sentence += chunk.choices[0].delta["content"]

            text_chunks = self.split_text_into_chunks(accumulated_sentence)
            for chunk in text_chunks:
                speak_callback(chunk)

            self.transition_state_callback(AwakeState.AWAKE, ActionState.IDLE)
            return accumulated_sentence
        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"


    def query_intent(self, input):
        messages = [
            {
                "role": "system",
                "content": str('You interpret intent from a passage of text. The intent categories you return are "general", "system", "weather", and "news". "System" is utilized for any kind of volume commands or going to sleep. If the intent is a system, it should return a key for what action to take: volume_up, volume_down, mute, unmute and sleep. if the intent is weather, try and interpret if it would call for a multi-day forecast or the current weather and return it as the action (either "forecast" or "current"). Then, determine the city name and pass that as a city paramater. You return a confidence rating for each category on a scale of 0 to 100, if the confidence is over 10%')
            },
            {
                "role":"user",
                "content":input
            },
            {
                "role": "system",
                "content": str('You always respond with a JSON response, matching the format {"intents":[{"type":"intent_categoryA", "confidence":intent_confidenceA, "action":"volume_up"}, {"type":"intent_categoryB", "confidence":intent_confidenceb, "city":"Chicago"}]}. This JSON should be the ONLY thing in your final response.')
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
            if len(sorted_intents) > 0 and sorted_intents[0]["confidence"] > 50:
                return sorted_intents[0]
            else:
                return None  # Or any default/fallback value

        except openai.error.OpenAIError as e:
            return f"Error: {str(e)}"
        
    def update_history(self, user_message, ai_response):
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "system", "content": ai_response})
        # Keep only the last 6 messages (3 interactions)
        self.history = self.history[-6:]

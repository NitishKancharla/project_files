import google.generativeai as genai
import os

class GeminiHelper:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyDS0SXbtLKaawt2IdjTezO8HzsaSoM6RJM")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate(self, prompt, system_message=None):
        if system_message:
            messages = [{'role': 'user', 'parts': [system_message]},
                        {'role': 'model', 'parts': ['OK']},
                        {'role': 'user', 'parts': [prompt]}]
        else:
            messages = [{'role': 'user', 'parts': [prompt]}]

        response = self.model.generate_content(messages)
        return response.text
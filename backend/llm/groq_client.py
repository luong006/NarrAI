from groq import Groq
import os

class GroqClient:
    def __init__(self, model_name: str = "openai/gpt-oss-120b"):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = model_name
    
    def chat(self, messages, temperature=0.7, max_tokens=2000, response_format=None):
        """Send message to Groq LLM"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            params["response_format"] = response_format
            
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    def chat_stream(self, messages, temperature=0.7, max_tokens=2000):
        """Send message to Groq LLM with streaming"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

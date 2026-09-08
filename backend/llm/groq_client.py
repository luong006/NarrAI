from groq import Groq
import os

class GroqClient:
    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Thiếu biến môi trường GROQ_API_KEY hoặc key chuyên dụng tương ứng")
            
        self.client = Groq(api_key=self.api_key)
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

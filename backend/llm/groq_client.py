from groq import Groq
import os
import time

class GroqClient:
    # Leave headroom below Groq's 8000 TPM limit for estimation variance.
    MAX_REQUEST_TOKENS = 7600
    MIN_COMPLETION_TOKENS = 256
    MAX_STREAM_CONTINUATIONS = 2

    @staticmethod
    def _estimate_prompt_tokens(messages):
        text = "\n".join(str(message.get("content", "")) for message in messages)
        # Vietnamese prose can tokenize more densely than English; /3 is conservative.
        return max(1, (len(text) + 2) // 3)

    def _safe_max_tokens(self, messages, requested):
        prompt_tokens = self._estimate_prompt_tokens(messages)
        available = self.MAX_REQUEST_TOKENS - prompt_tokens
        if available < self.MIN_COMPLETION_TOKENS:
            raise ValueError("Nội dung yêu cầu quá dài, hãy rút gọn bản phác thảo hoặc lịch sử truyện rồi thử lại.")
        return min(requested, available)

    @staticmethod
    def _is_request_too_large(error):
        message = str(error)
        return "413" in message or "rate_limit_exceeded" in message or "Request too large" in message

    @staticmethod
    def _retry_budgets(initial):
        budgets = [initial, max(256, int(initial * 0.75)), max(256, int(initial * 0.5))]
        return list(dict.fromkeys(budgets))

    def __init__(self, model_name: str = "openai/gpt-oss-120b", api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Thiếu biến môi trường GROQ_API_KEY hoặc key chuyên dụng tương ứng")
            
        self.client = Groq(api_key=self.api_key)
        self.model = model_name
    
    def chat(self, messages, temperature=0.7, max_tokens=2000, response_format=None):
        """Send message to Groq LLM"""
        safe_max_tokens = self._safe_max_tokens(messages, max_tokens)
        budgets = self._retry_budgets(safe_max_tokens)
        last_error = None
        for index, budget in enumerate(budgets):
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": budget,
            }
            if response_format:
                params["response_format"] = response_format
            try:
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content
            except Exception as error:
                last_error = error
                if not self._is_request_too_large(error) or index == len(budgets) - 1:
                    raise
                time.sleep(0.25)
        raise last_error

    def chat_stream(self, messages, temperature=0.7, max_tokens=2000):
        """Stream the completion and resume once or twice if the provider cuts it off."""
        original_messages = list(messages)
        request_messages = original_messages
        generated_text = ""
        continuation_count = 0

        while True:
            safe_max_tokens = self._safe_max_tokens(request_messages, max_tokens)
            budgets = self._retry_budgets(safe_max_tokens)
            should_continue = False
            finish_reason = None

            for index, budget in enumerate(budgets):
                emitted_this_request = False
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=request_messages,
                        temperature=temperature,
                        max_tokens=budget,
                        stream=True
                    )
                    for chunk in response:
                        choice = chunk.choices[0]
                        finish_reason = getattr(choice, "finish_reason", None) or finish_reason
                        content = getattr(choice.delta, "content", None)
                        if content:
                            emitted_this_request = True
                            generated_text += content
                            yield content
                    break
                except Exception as error:
                    if (
                        not emitted_this_request
                        and self._is_request_too_large(error)
                        and index < len(budgets) - 1
                    ):
                        time.sleep(0.25)
                        continue
                    if generated_text and continuation_count < self.MAX_STREAM_CONTINUATIONS:
                        continuation_count += 1
                        should_continue = True
                        break
                    raise

            if finish_reason == "length":
                if not generated_text:
                    raise RuntimeError("The language model reached its output limit before producing story text.")
                if continuation_count >= self.MAX_STREAM_CONTINUATIONS:
                    raise RuntimeError("The language model repeatedly reached its output limit; the partial draft was preserved.")
                continuation_count += 1
                should_continue = True

            if not should_continue:
                return

            continuation_context = generated_text[-6000:]
            request_messages = [
                *original_messages,
                {
                    "role": "assistant",
                    "content": continuation_context,
                },
                {
                    "role": "user",
                    "content": (
                        "Hãy viết tiếp ngay từ vị trí kết thúc của đoạn văn bản trên. "
                        "Không lặp lại câu hoặc đoạn đã có; hoàn thành câu đang dang dở nếu cần, "
                        "sau đó tiếp tục tự nhiên và giữ nguyên nhân vật, bối cảnh, giọng văn."
                    ),
                },
            ]

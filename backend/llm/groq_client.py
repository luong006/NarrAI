from groq import Groq
import os
import time
import re
import base64

class GroqClient:
    # Leave headroom below Groq's 8000 TPM limit for estimation variance.
    MAX_REQUEST_TOKENS = 7600
    MIN_COMPLETION_TOKENS = 256
    MAX_STREAM_CONTINUATIONS = 2

    MODEL_LIMITS = {
        "qwen/qwen3.8-27b": 8192,
        "openai/gpt-oss-20b": 8192,
        "openai/gpt-oss-120b": 8192,
        "allam-2-7b": 4096,
    }

    FALLBACK_MODELS = [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "allam-2-7b",
    ]

    MODEL_CONTEXT_WINDOWS = {
        "qwen/qwen3.8-27b": 8192,
        "openai/gpt-oss-120b": 8192,
        "openai/gpt-oss-20b": 8192,
        "allam-2-7b": 4096,
    }

    @staticmethod
    def _estimate_prompt_tokens(messages):
        text = "\n".join(str(message.get("content", "")) for message in messages)
        # Vietnamese prose can tokenize more densely than English; /3 is conservative.
        return max(1, (len(text) + 2) // 3)

    def _safe_max_tokens(self, messages, requested, model_name: str = None):
        prompt_tokens = self._estimate_prompt_tokens(messages)
        context_limit = self.MODEL_CONTEXT_WINDOWS.get(model_name, self.MAX_REQUEST_TOKENS) if model_name else self.MAX_REQUEST_TOKENS
        available = context_limit - prompt_tokens - 100
        if available < self.MIN_COMPLETION_TOKENS:
            raise ValueError(f"Nội dung yêu cầu ({prompt_tokens} tokens) vượt quá dung lượng xử lý của mô hình {model_name or 'Groq'}.")
        model_cap = self.MODEL_LIMITS.get(model_name, 4096) if model_name else 4096
        return max(self.MIN_COMPLETION_TOKENS, min(requested, available, model_cap))

    @staticmethod
    def _is_request_too_large(error):
        message = str(error).lower()
        return (
            "413" in message
            or "rate_limit" in message
            or "request too large" in message
            or "must be less than or equal" in message
            or "max_tokens" in message
            or "context_length_exceeded" in message
            or "reduce the length" in message
            or "maximum value" in message
        )

    @staticmethod
    def _retry_budgets(initial, model_cap=4096):
        capped = min(initial, model_cap)
        budgets = [capped, max(256, int(capped * 0.75)), max(256, int(capped * 0.5)), 1024, 512, 256]
        return [b for b in dict.fromkeys(budgets) if b <= capped]

    def _get_api_keys(self) -> list:
        keys = []
        if getattr(self, "api_key", None) and self.api_key.strip():
            keys.append(self.api_key.strip())
        env_vars = [
            "GROQ_API_KEY_BIBLE",
            "GROQ_API_KEY_INTAKE",
            "GROQ_API_KEY_STORY",
            "GROQ_API_KEY",
            "GROQ_API_KEY_COPILOT",
            "GROQ_API_KEY_COMIC",
        ]
        for var in env_vars:
            val = os.environ.get(var)
            if val and val.strip() and val.strip() not in keys:
                keys.append(val.strip())
        return keys

    def __init__(self, model_name: str = "qwen/qwen3.8-27b", api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            candidate_keys = self._get_api_keys()
            if candidate_keys:
                self.api_key = candidate_keys[0]
            else:
                raise ValueError("Thiếu biến môi trường GROQ_API_KEY hoặc key chuyên dụng tương ứng")

        self.client = Groq(api_key=self.api_key)
        self.model = model_name
        self._clients = {self.api_key: self.client}
    
    def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 2000, response_format = None) -> str:
        """Convenience method to generate text from a prompt with optional system prompt."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens, response_format=response_format)

    def chat(self, messages, temperature=0.7, max_tokens=2000, response_format=None):
        """Send message to Groq LLM with multi-model and multi-key rate-limit resilience"""
        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        keys_to_try = self._get_api_keys()
        last_error = None

        for model_candidate in models_to_try:
            model_cap = self.MODEL_LIMITS.get(model_candidate, 4096)
            safe_max_tokens = self._safe_max_tokens(messages, max_tokens, model_name=model_candidate)
            budgets = self._retry_budgets(safe_max_tokens, model_cap=model_cap)

            for key in keys_to_try:
                if key == getattr(self, "api_key", None) and hasattr(self, "client"):
                    groq_client = self.client
                else:
                    if not hasattr(self, "_clients"):
                        self._clients = {}
                    if key not in self._clients:
                        self._clients[key] = Groq(api_key=key)
                    groq_client = self._clients[key]

                for index, budget in enumerate(budgets):
                    params = {
                        "model": model_candidate,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": budget,
                    }
                    if response_format:
                        params["response_format"] = response_format
                    try:
                        response = groq_client.chat.completions.create(**params)
                        return response.choices[0].message.content
                    except Exception as error:
                        last_error = error
                        err_msg = str(error).lower()
                        # If rate limit or token quota exceeded, try next API key immediately!
                        if ("rate_limit" in err_msg or "429" in err_msg or "tokens per day" in err_msg or "tpd" in err_msg or "tpm" in err_msg):
                            break
                        if self._is_request_too_large(error):
                            if index < len(budgets) - 1:
                                time.sleep(0.15)
                                continue
                            break
                        if index == len(budgets) - 1:
                            break
                        time.sleep(0.15)
        if last_error:
            raise last_error
        raise RuntimeError("Không thể kết nối đến bất kỳ mô hình AI nào.")

    def chat_stream(self, messages, temperature=0.7, max_tokens=2000):
        """Stream the completion with multi-model fallback resilience and resume once or twice if needed."""
        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_error = None

        for model_candidate in models_to_try:
            original_messages = list(messages)
            request_messages = original_messages
            generated_text = ""
            continuation_count = 0
            candidate_emitted_anything = False

            model_cap = self.MODEL_LIMITS.get(model_candidate, 4096)

            try:
                while True:
                    safe_max_tokens = self._safe_max_tokens(request_messages, max_tokens, model_name=model_candidate)
                    budgets = self._retry_budgets(safe_max_tokens, model_cap=model_cap)
                    should_continue = False
                    finish_reason = None

                    for index, budget in enumerate(budgets):
                        emitted_this_request = False
                        try:
                            response = self.client.chat.completions.create(
                                model=model_candidate,
                                messages=request_messages,
                                temperature=temperature,
                                max_tokens=budget,
                                stream=True
                            )
                            for chunk in response:
                                if not chunk.choices:
                                    continue
                                choice = chunk.choices[0]
                                finish_reason = getattr(choice, "finish_reason", None) or finish_reason
                                content = getattr(choice.delta, "content", None)
                                if content:
                                    emitted_this_request = True
                                    candidate_emitted_anything = True
                                    generated_text += content
                                    yield content
                            break
                        except Exception as error:
                            last_error = error
                            err_msg = str(error).lower()
                            is_quota_or_rate = (
                                "rate_limit" in err_msg
                                or "429" in err_msg
                                or "tokens per day" in err_msg
                                or "tpd" in err_msg
                                or "tpm" in err_msg
                            )

                            if not emitted_this_request:
                                # If request hit rate limit or size limit, try smaller budget if available
                                if (self._is_request_too_large(error) or is_quota_or_rate) and index < len(budgets) - 1:
                                    time.sleep(0.25)
                                    continue
                                break

                            if generated_text and continuation_count < self.MAX_STREAM_CONTINUATIONS:
                                continuation_count += 1
                                should_continue = True
                                break
                            raise error

                    if not candidate_emitted_anything:
                        # Candidate failed on first request without yielding anything; try next model
                        break

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
            except Exception as candidate_err:
                last_error = candidate_err
                if candidate_emitted_anything:
                    raise candidate_err
                time.sleep(0.2)
                continue

            if candidate_emitted_anything:
                return

        if last_error:
            raise last_error
        raise RuntimeError("Tất cả các mô hình AI đều không thể phản hồi.")

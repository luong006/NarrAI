import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from llm.groq_client import GroqClient


def _chunk(content=None, finish_reason=None):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content=content),
                finish_reason=finish_reason,
            )
        ]
    )


class TestGroqClientStreamResume(unittest.TestCase):
    def setUp(self):
        self.client = GroqClient.__new__(GroqClient)
        self.client.model = "test-model"
        self.client.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=MagicMock())
            )
        )

    def test_resumes_when_provider_finishes_due_to_token_limit(self):
        create = self.client.client.chat.completions.create
        create.side_effect = [
            iter([_chunk("The story "), _chunk("continues", "length")]),
            iter([_chunk(" here.", "stop")]),
        ]

        chunks = list(self.client.chat_stream(
            [{"role": "user", "content": "Write a story"}],
            max_tokens=1000,
        ))

        self.assertEqual("".join(chunks), "The story continues here.")
        self.assertEqual(create.call_count, 2)
        resumed_messages = create.call_args_list[1].kwargs["messages"]
        self.assertEqual(resumed_messages[-2]["content"], "The story continues")
        self.assertIn("Không lặp lại", resumed_messages[-1]["content"])

    def test_resumes_after_stream_transport_fails_mid_response(self):
        def interrupted_response():
            yield _chunk("The beginning ")
            raise ConnectionError("stream interrupted")

        create = self.client.client.chat.completions.create
        create.side_effect = [
            interrupted_response(),
            iter([_chunk("continues safely.", "stop")]),
        ]

        chunks = list(self.client.chat_stream(
            [{"role": "user", "content": "Write a story"}],
            max_tokens=1000,
        ))

        self.assertEqual("".join(chunks), "The beginning continues safely.")
        self.assertEqual(create.call_count, 2)

    def test_raises_instead_of_silently_returning_truncated_output(self):
        self.client.MAX_STREAM_CONTINUATIONS = 0
        create = self.client.client.chat.completions.create
        create.return_value = iter([_chunk("partial draft", "length")])
        yielded = []
        stream = self.client.chat_stream(
            [{"role": "user", "content": "Write a story"}],
            max_tokens=1000,
        )

        with self.assertRaisesRegex(RuntimeError, "partial draft was preserved"):
            while True:
                yielded.append(next(stream))

        self.assertEqual(yielded, ["partial draft"])


if __name__ == "__main__":
    unittest.main()

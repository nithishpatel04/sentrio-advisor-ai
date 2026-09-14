import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "briefing-service"))

import bedrock_client


class FakeClient:
    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"output": {"message": {"content": [{"text": self.text}]}}}


class BedrockClientTests(unittest.TestCase):
    def call_with(self, text=None, error=None):
        client = FakeClient(text=text, error=error)
        with patch.object(bedrock_client.boto3, "client", return_value=client) as factory:
            result = bedrock_client.generate_briefing({})
        return result, client, factory

    def test_valid_response_is_parsed(self):
        result, _, _ = self.call_with('{"executive_summary": []}')
        self.assertEqual(result, {"executive_summary": []})

    def test_json_fences_are_parsed(self):
        for text in (
            '```json\n{"executive_summary": []}\n```',
            '```\n{"executive_summary": []}\n```',
        ):
            result, _, _ = self.call_with(text)
            self.assertEqual(result, {"executive_summary": []})

    def test_invalid_json_raises_safe_error(self):
        with self.assertRaises(bedrock_client.BedrockResponseError):
            self.call_with("not json")

    def test_missing_text_raises_safe_error(self):
        client = FakeClient()
        client.converse = lambda **kwargs: {"output": {"message": {"content": [{}]}}}
        with patch.object(bedrock_client.boto3, "client", return_value=client):
            with self.assertRaises(bedrock_client.BedrockResponseError):
                bedrock_client.generate_briefing({})

    def test_invocation_error_is_handled(self):
        with self.assertRaises(bedrock_client.BedrockResponseError):
            self.call_with(error=RuntimeError("service failure"))

    def test_request_uses_model_prompts_and_conservative_settings(self):
        _, client, factory = self.call_with('{"executive_summary": []}')
        factory.assert_called_once_with("bedrock-runtime", region_name="us-east-1")
        request = client.calls[0]
        self.assertEqual(request["modelId"], "amazon.nova-2-lite-v1:0")
        self.assertTrue(request["system"])
        self.assertEqual(request["messages"][0]["role"], "user")
        self.assertTrue(request["messages"][0]["content"])
        self.assertEqual(request["inferenceConfig"], {"temperature": 0.1, "maxTokens": 3000})


if __name__ == "__main__":
    unittest.main()
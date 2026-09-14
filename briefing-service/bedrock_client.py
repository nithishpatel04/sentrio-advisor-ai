import json
import importlib
import os

from prompt_builder import build_system_prompt, build_user_prompt


MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-2-lite-v1:0")
REGION_NAME = os.getenv("AWS_REGION", "us-east-1")


class _Boto3Proxy:
    def client(self, *args, **kwargs):
        try:
            boto3 = importlib.import_module("boto3")
        except ImportError:
            raise BedrockResponseError(
                "The AWS SDK is unavailable in this runtime."
            ) from None
        return boto3.client(*args, **kwargs)


class BedrockResponseError(Exception):
    """Raised when Bedrock does not return a valid JSON briefing."""


boto3 = _Boto3Proxy()


def _strip_optional_markdown_fences(text):
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):]
    elif cleaned.startswith("```"):
        cleaned = cleaned[len("```"):]

    if cleaned.rstrip().endswith("```"):
        cleaned = cleaned.rstrip()[:-3]

    return cleaned.strip()


def _extract_json(response):
    try:
        content = response["output"]["message"]["content"]
        text = "".join(part["text"] for part in content if "text" in part)
    except (KeyError, TypeError):
        raise BedrockResponseError(
            "Bedrock returned an invalid response format."
        ) from None

    if not text:
        raise BedrockResponseError(
            "Bedrock returned an empty response."
        )

    cleaned = _strip_optional_markdown_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise BedrockResponseError(
            "Bedrock returned invalid JSON."
        ) from None


def generate_briefing(ai_evidence):
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(ai_evidence)

    try:
        client = boto3.client(
            "bedrock-runtime",
            region_name=REGION_NAME
        )

        response = client.converse(
            modelId=MODEL_ID,
            system=[
                {
                    "text": system_prompt
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": user_prompt
                        }
                    ],
                }
            ],
            inferenceConfig={
                "temperature": 0.1,
                "maxTokens": 3000,
            },
        )

    except BedrockResponseError:
        raise
    except Exception:
        print("Bedrock Converse API error")
        raise BedrockResponseError(
            "Bedrock briefing generation failed."
        ) from None

    return _extract_json(response)
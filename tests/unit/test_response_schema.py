from app.models.anthropic import AnthropicResponse
from app.models.openai import ChatCompletionResponse


def test_anthropic_response_schema():
    response = AnthropicResponse(
        id="test-id",
        model="claude-3-opus",
        content=[{"type": "text", "text": "hello"}],
        usage={"input_tokens": 10, "output_tokens": 10},
    )
    assert response.id == "test-id"
    assert response.content[0]["text"] == "hello"


def test_openai_response_schema():
    # Basic check for OpenAI response structure
    response_data = ChatCompletionResponse(
        id="chatcmpl-123",
        created=1234567890,
        model="gpt-4",
        choices=[{"message": {"role": "assistant", "content": "hello"}}],
        usage={"prompt_tokens": 10, "completion_tokens": 10},
    )
    assert response_data.id == "chatcmpl-123"
    assert response_data.choices[0]["message"]["content"] == "hello"

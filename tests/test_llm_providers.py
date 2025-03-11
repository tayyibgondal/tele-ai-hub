import pytest
import openai
from unittest.mock import patch, MagicMock
from src.llm_providers import (
    BaseLLM,
    OllamaLLMClass,
    OpenAILLM,
    get_llm_instance
)


def test_base_llm_invoke_not_implemented():
    base_llm = BaseLLM("test_model")
    with pytest.raises(NotImplementedError):
        base_llm.invoke("hello")


@patch("src.llm_providers.OllamaLLM")
def test_ollama_llm_invoke(mock_ollama_llm):
    mock_model = MagicMock()
    mock_model.invoke.return_value = " response  "
    mock_ollama_llm.return_value = mock_model

    ollama = OllamaLLMClass("my_model", "http://fake-url")
    resp = ollama.invoke("Hi")
    mock_ollama_llm.assert_called_once_with(model="my_model", base_url="http://fake-url")
    mock_model.invoke.assert_called_once_with("Hi")
    assert resp == "response"


@patch("src.llm_providers.OpenAI")
def test_openai_llm_invoke(mock_openai_class, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake_api_key")

    mock_openai_instance = MagicMock()
    mock_completion_response = MagicMock()
    mock_completion_response.choices = [
        MagicMock(message=MagicMock(content="Mocked response"))
    ]
    mock_openai_instance.chat.completions.create.return_value = mock_completion_response
    mock_openai_class.return_value = mock_openai_instance

    openai_llm = OpenAILLM("test-model")
    result = openai_llm.invoke("Hello world")
    assert result == "Mocked response"

def test_get_llm_instance_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake_api_key")
    llm = get_llm_instance("some_model", service="openai")
    assert isinstance(llm, OpenAILLM)


def test_get_llm_instance_ollama():
    llm = get_llm_instance("another_model", service="ollama")
    assert isinstance(llm, OllamaLLMClass)


def test_get_llm_instance_unknown_service():
    llm = get_llm_instance("model", service="blah")
    assert llm is None

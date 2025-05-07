from openai import OpenAI
import openai
from langchain_ollama import OllamaLLM 
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env if present

OLLAMA_SERVER = os.getenv("OLLAMA_SERVER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class BaseLLM:
    def __init__(self, model_name):
        self.model_name = model_name  

    def invoke(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses should implement this method.")

class OllamaLLMClass(BaseLLM):
    def __init__(self, model_name, base_url):
        super().__init__(model_name)
        self.base_url = base_url

    def invoke(self, prompt: str) -> str:
        print(f"Invoking Ollama model: {self.model_name}")
        print("base_url: ", self.base_url)
        model = OllamaLLM(model=self.model_name, base_url=self.base_url) 
        response = model.invoke(prompt)
        return response.strip()

class OpenAILLM(BaseLLM):
    def __init__(self, model_name):
        # Strip " Telecom Agent" suffix for actual API calls
        clean_model_name = model_name.replace(" Telecom Agent", "")
        super().__init__(clean_model_name)
        openai.api_key = OPENAI_API_KEY
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(
                        api_key=OPENAI_API_KEY, 
                    )

    def invoke(self, prompt: str) -> str:
        print(f"Invoking OpenAI model: {self.model_name}")
        chat_completion = self.client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=self.model_name,
    )
        return chat_completion.choices[0].message.content

def get_llm_instance(model_name, service=None):
    """
    Factory function to return an instance of the chosen LLM based on config.
    """
    if service == "openai":
        return OpenAILLM(model_name)
    elif service == "ollama":
        return OllamaLLMClass(model_name, OLLAMA_SERVER)


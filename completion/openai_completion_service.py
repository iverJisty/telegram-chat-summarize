import openai
from completion_service import CompletionService


class OpenAICompletionService(CompletionService):
    api_key = None

    def __init__(self, api_key):
        if api_key is not None:
            self.api_key = api_key
        else:
            raise Exception("OpenAI API key is required")

    def get_completion(self, model="gpt-3.5-turbo", temperature=0.8, messages=None):

        prompt = [{"role": "user", "content": messages}]

        response = openai.ChatCompletion.create(
            model=model,
            messages=prompt,
            temperature=temperature,
        )
        return response.choices[0].message["content"]

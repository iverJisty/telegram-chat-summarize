from abc import ABC, abstractmethod


class CompletionService(ABC):
    @abstractmethod
    def get_completion(self, model, temperature, messages):
        pass

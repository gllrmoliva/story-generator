from abc import ABC, abstractmethod

class LLM(ABC):
    """
    clase abstracta wrapper de una API LLM.
    """

    def __init__(self, model_name: str, api_key: str):
        """
        inicializa el wrapper LLM.
        """
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None):
        """
        método para la generación de texto.

        Args:
            prompt: prompt del usuario.
            system_prompt: instrucción de sistema.
        Returns:
            respuesta de LLM.
        """
        pass

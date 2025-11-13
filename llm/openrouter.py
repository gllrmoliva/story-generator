import requests
from .base import LLM

class OpenRouter(LLM):
    """
    LLM para la API de OpenRouter.
    """
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name, api_key)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Fantasy Generator"
        }

    def generate(self, prompt: str, system_prompt: str = None, tools_schema: list = None, tool_choice: list = None, messages: list = []):

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "model": self.model_name,
            "messages": messages,
            "tools": tools_schema,
            "tool_choice": tool_choice
        }
        
        try:
            response = requests.post(self.API_URL, headers=self.headers, json=body, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data['choices'][0]['message']
            else:
                raise ValueError("La respuesta de la API no contiene 'choices' válidos.")
                
        # errores de red o API
        except requests.RequestException as e:
            print(f"Error en la solicitud a OpenRouter: {e}")
            return f"[Error de API: {e}]"
        # errores de parseo de respuesta
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error al parsear la respuesta de OpenRouter: {e}")
            print(data)
            return f"[Error de formato de respuesta: {e}]"

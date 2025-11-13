from llm.openrouter import OpenRouter
from config import OPENROUTER_API_KEY, GENERATOR_MODEL, COHERENCE_MODEL, TEST_MODEL
from pprint import pprint

if __name__ == "__main__":

    # Test de Openrouter básico 

    # Este es su esquema de formato deseado
    # Este es el esquema de UN personaje (lo moveremos adentro)
    character_schema = {
        "type": "object",
        "properties": {
            "nombre": {
                "type": "string",
                "description": "El nombre completo del personaje.",
            },
            "clase": {
                "type": "string",
                "description": "La clase o arquetipo del personaje (ej. 'Guerrero', 'Mago').",
            },
            "sexo": {
                "type": "string",
                "enum": ["Masculino", "Femenino", "No Binario", "Indefinido"],
            },
            "descripcion": {
                "type": "string",
                "description": "Una breve descripción de la apariencia y trasfondo del personaje.",
            }
        },
        "required": ["nombre", "clase", "descripcion"]
    }
    
    # --- NUEVO ESQUEMA DE HERRAMIENTAS (PARA LISTAS) ---
    tools_definition = [
        {
            "type": "function",
            "function": {
                "name": "register_character_list", # Nuevo nombre de función
                "description": "Formatea y registra una LISTA de nuevos personajes de fantasía.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        # El único argumento de esta función es la lista
                        "character_list": {
                            "type": "array",
                            "description": "Una lista de los personajes a generar.",
                            # 'items' define la estructura de cada objeto EN la lista
                            "items": character_schema 
                        }
                    },
                    "required": ["character_list"] # La lista es obligatoria
                },
            },
        }
    ]

    forced_tool_choice = {
        "type": "function",
        "function": {"name": "register_character_list"}
    }

    text_generator = OpenRouter(model_name = TEST_MODEL,
                                api_key = OPENROUTER_API_KEY
                                )
    backlog = []
    user_prompt = input()
    while (user_prompt != "q"):

        backlog.append(user_prompt)

        system_response = text_generator.generate(prompt = user_prompt,
                                                  system_prompt = str(backlog),
                                                  tools_schema = tools_definition,
                                                  tool_choice = forced_tool_choice
                                                  )["tool_calls"][0]["function"]["arguments"]
        pprint(system_response)

        backlog.append(system_response)

        user_prompt = input()

        while(len(backlog) > 10):
            backlog.pop(0)

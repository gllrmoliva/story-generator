import json
import time
from typing import Dict, Any, Optional, List, Callable
from pprint import pprint

from core.models import Synopsis
from core.graph_manager import CharactersGraph, WorldbuildingGraph
from llm.base import LLM

from core.tools import (
    CHARACTER_TOOL_SCHEMA, CHARACTER_FORCE_TOOL,
    RELATION_TOOL_SCHEMA, RELATIONS_FORCE_TOOL,
    WORLD_BUILDING_TOOL_SCHEMA, WORLD_BUILDING_FORCE_TOOL,
    SYNOPSIS_TOOL_SCHEMA, SYNOPSIS_FORCE_TOOL
)

from core.prompts import (
    CHAR_GEN_INSTRUCTION,
    WORLD_GEN_INSTRUCTION,
    SYNOPSIS_GEN_INSTRUCTION,
    RELATIONS_GEN_INSTRUCTION
)

from llm.openrouter import OpenRouter
from config import TEST_MODEL, OPENROUTER_API_KEY


# Definitions
WB_CATEGORY_DEFINITION = {
    "ontological": "Ontological entities define the fundamental nature of existence within the fictional world. the “why” and “how” of reality itself. They describe the metaphysical and conceptual framework that determines what can exist, how it exists, and why it follows certain rules.",
    "material": "Material entities refer to the tangible, physical structure of the world. Its geography, climate, ecosystems, and the distribution of natural resources. They define where and how life unfolds.",
    "sociocultural": "Sociocultural entities define how societies organize themselves, what they believe in, and how they act collectively. They encompass systems of power, social hierarchies, belief systems, as well as arts, traditions, and languages.",
    "historical": "Historical entities represent the temporal dimension of the world. Its origins, evolution, turning points, and collective memory. They describe the narrative of change."
}


class InitialGenerator:
    """
    Generador inicial de la estructura base de la historia
    """

    def __init__(self, llm: LLM, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries
        self.character_graph = CharactersGraph()
        self.world_graph = WorldbuildingGraph()
        self.synopsis = Synopsis()

    def generate(self, user_prompt: str):
        """
        generación completa de los componentes iniciales.
        """
        
        print("\nINITIAL GENERATOR: Creación de World Graph...")
        for category, definition in WB_CATEGORY_DEFINITION.items():
            print(f"  > Generando Entidades para: {category}...")
            
            #Generar Entidades
            args = self._generate_with_retry(
                prompt=user_prompt,
                system_prompt=definition + WORLD_GEN_INSTRUCTION,
                schema=WORLD_BUILDING_TOOL_SCHEMA,
                tool_choice=WORLD_BUILDING_FORCE_TOOL,
                context_desc=f"World Building Entities ({category})"
            )

            current_entities_context = ""
            
            if args and "entity_list" in args:

                for entity in args["entity_list"]:

                    self.world_graph.add_foundation(
                        name=entity["name"],
                        category=category,
                        description=entity["description"]
                    )

                    current_entities_context += f"- {entity['name']}: {entity['description']}\n"

                # Generar Relaciones
                print(f"  > Generando Relaciones para: {category}...")
                
                relations_prompt = (
                    f"Based on the following entities defined for the '{category}' category:\n\n"
                    f"{current_entities_context}\n"
                    f"Create logical relationships/connections between them. "
                    f"How do they influence each other? (e.g., A implies B, A contradicts B, A is located in B)."
                )

                rel_args = self._generate_with_retry(
                    prompt=relations_prompt,
                    system_prompt=RELATIONS_GEN_INSTRUCTION,
                    schema=RELATION_TOOL_SCHEMA,
                    tool_choice=RELATIONS_FORCE_TOOL,
                    context_desc=f"World Building Relations ({category})"
                )

                if rel_args and "relations_list" in rel_args:
                    count_rels = 0
                    for rel in rel_args["relations_list"]:
                        self.world_graph.add_relation(
                            category=category,
                            source=rel["source"],
                            target=rel["target"],
                            relation_type=rel["relation_type"],
                            explanation=rel["description"]
                        )
                        count_rels += 1
                    print(f"    -> Se crearon {count_rels} relaciones en '{category}'.")

        # Generación de Personajes
        print("\nINITIAL GENERATOR: Creación de personajes...")
        char_prompt = f"{user_prompt}\n\nCONTEXTO MUNDO:\n{self.world_graph.to_llm_context_string()}"
        
        def validate_characters(data):
            if "character_list" not in data: return False
            if not isinstance(data["character_list"], list) or len(data["character_list"]) == 0: return False
            for char in data["character_list"]:
                if "name" not in char or "description" not in char or "backstory" not in char: return False
            return True

        args = self._generate_with_retry(
            prompt=char_prompt,
            system_prompt=CHAR_GEN_INSTRUCTION,
            schema=CHARACTER_TOOL_SCHEMA,
            tool_choice=CHARACTER_FORCE_TOOL,
            context_desc="Character Generation",
            validator=validate_characters 
        )

        if args:
            count = 0
            for character in args["character_list"]:
                self.character_graph.add_character(
                    name=character["name"],
                    description=character["description"],
                    backstory=character["backstory"]
                )
                count += 1
            print(f"    > Se añadieron {count} personajes al grafo.")


        # Relaciones de Personajes
        print("\nINITIAL GENERATOR: Creación de relaciones entre personajes...")
        args = self._generate_with_retry(
            prompt=self.character_graph.to_llm_context_string(),
            system_prompt=RELATIONS_GEN_INSTRUCTION,
            schema=RELATION_TOOL_SCHEMA,
            tool_choice=RELATIONS_FORCE_TOOL,
            context_desc="Character Relations"
        )

        if args and "relations_list" in args:
            for relation in args["relations_list"]:
                self.character_graph.add_relationship(
                    char_a_name=relation["source"],
                    char_b_name=relation["target"],
                    relation_type=relation["relation_type"],
                    description=relation["description"]
                )

        # Generación de Sinopsis
        print("\nINITIAL GENERATOR: Creación de sinopsis...")
        synopsis_prompt = (
            f"{user_prompt}\n"
            f"{self.world_graph.to_llm_context_string()}\n"
            f"{self.character_graph.to_llm_context_string()}"
        )

        args = self._generate_with_retry(
            prompt=synopsis_prompt,
            system_prompt=SYNOPSIS_GEN_INSTRUCTION,
            schema=SYNOPSIS_TOOL_SCHEMA,
            tool_choice=SYNOPSIS_FORCE_TOOL,
            context_desc="Synopsis Generation"
        )

        if args:
            self.synopsis.premise = args.get("premise", "")
            self.synopsis.summary = args.get("story", "")

        return self.world_graph, self.character_graph, self.synopsis

    def _generate_with_retry(self, 
                             prompt: str, 
                             system_prompt: str, 
                             schema: dict, 
                             tool_choice: dict, 
                             context_desc: str,
                             validator: Callable[[dict], bool] = None) -> Optional[Dict[str, Any]]:
        """
        Intenta generar, parsear y validar la respuesta del LLM
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # Llamada al LLM
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools_schema=schema,
                    tool_choice=tool_choice
                )
                
                # Parseo de JSON
                parsed_data = self._parse_tool_response(response)
                
                if not parsed_data:
                    raise ValueError("Respuesta vacía o no se pudo parsear el tool call.")

                # Validación de Estructura
                if validator:
                    if not validator(parsed_data):
                        raise ValueError(f"El JSON es válido pero no cumple la validación lógica para {context_desc}.")

                return parsed_data
            
            except Exception as e:
                print(f"    [Warning] Intento {attempt}/{self.max_retries} fallido para '{context_desc}': {e}")
            
            if attempt < self.max_retries:
                time.sleep(1) # esto por open router

        print(f"    [Critical] Fallo total generando '{context_desc}' tras {self.max_retries} intentos.")
        return None

    def _parse_tool_response(self, response: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(response, dict):
            return None

        tool_calls = response.get("tool_calls")
        if not tool_calls:
            return None

        try:
            args_str = tool_calls[0]['function']['arguments']
            return json.loads(args_str)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
            print(f"    [Parser Error] Fallo al decodificar JSON de herramienta: {e}")
            return None

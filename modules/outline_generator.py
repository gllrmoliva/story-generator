import json
import time
from typing import List, Optional, Dict, Any
from pprint import pprint

from llm.base import LLM
from core.models import Synopsis, ChapterOutline
from core.tools import OUTLINE_TOOL_SCHEMA, OUTLINE_FORCE_TOOL
from core.prompts import OUTLINES_GEN_INSTRUCTION

from llm.openrouter import OpenRouter
from config import TEST_MODEL, OPENROUTER_API_KEY


class OutlineGenerator:
    """
    genera el outline (titulo, resumen) por capitulo
    """

    def __init__(self, llm: LLM, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    def generate(self, world_graph_llm: str, char_graph_llm: str, synopsis: Synopsis) -> List[ChapterOutline]:

        
        # Preparar el Prompt
        user_prompt = (
            f"## WORLD GRAPH ##\n{world_graph_llm}\n\n"
            f"## CHARACTERS GRAPH ##\n{char_graph_llm}\n\n"
            f"## PREMISE ##\n{synopsis.premise}\n\n"
            f"## SUMMARY ##\n{synopsis.summary}"
        )

        print("\nOUTLINE GENERATOR: Generando títulos y resumen de capítulos...")

        # Ejecutar con reintentos
        args = self._generate_with_retry(
            prompt=user_prompt,
            system_prompt=OUTLINES_GEN_INSTRUCTION,
            schema=OUTLINE_TOOL_SCHEMA,
            tool_choice=OUTLINE_FORCE_TOOL,
            context_desc="Chapter Outlines"
        )

        outlines_list = []

        # Procesar resultados
        if args and "outlines" in args:
            raw_outlines = args["outlines"]
            print(f"  > Se han recibido {len(raw_outlines)} capítulos crudos.")

            for index, outline_data in enumerate(raw_outlines, 1): # Start chapters at 1
                try:
                    chapter = ChapterOutline(
                        chapter_number=index,
                        title=outline_data.get("title", f"Chapter {index}"),
                        resume=outline_data.get("resume", "")
                    )
                    outlines_list.append(chapter)
                except KeyError as e:
                    print(f"  [Error] Falta campo requerido en capítulo {index}: {e}")

        else:
            print("  [Error] No se pudieron generar outlines válidos.")

        return outlines_list

    def _generate_with_retry(self, prompt: str, system_prompt: str, schema: dict, tool_choice: dict, context_desc: str) -> Optional[Dict[str, Any]]:
        """
        retrys de generador porsiacaso entrega resultados mal parseados
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools_schema=schema,
                    tool_choice=tool_choice
                )
                
                parsed_data = self._parse_tool_response(response)
                
                if parsed_data:
                    return parsed_data
                
                print(f"    [Warning] Intento {attempt}/{self.max_retries} fallido para '{context_desc}'.")
            
            except Exception as e:
                print(f"    [Error] Intento {attempt}/{self.max_retries} excepción en '{context_desc}': {e}")
            
            if attempt < self.max_retries:
                time.sleep(1)

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
            print(f"    [Parser Error] Fallo al decodificar JSON: {e}")
            return None


if __name__ == "__main__":
    print("--- INICIANDO TEST DE OUTLINE GENERATOR ---")
    
    mock_synopsis = Synopsis()
    mock_synopsis.premise = "A cybernetic ninja seeks revenge in Neo-Tokyo."
    mock_synopsis.summary = "The ninja wakes up, finds his sword, fights a robot, and defeats the boss."

    mock_world_info = "Context: Cyberpunk city, high tech, low life. Acid rain is common."
    mock_char_info = "Protagonist: Ryu (Cyber-Ninja). Antagonist: Lord Z (AI Overlord)."

    llm_client = OpenRouter(model_name=TEST_MODEL, api_key=OPENROUTER_API_KEY)
    
    generator = OutlineGenerator(llm=llm_client, max_retries=2)

    generated_chapters = generator.generate(
        world_graph_llm=mock_world_info,
        char_graph_llm=mock_char_info,
        synopsis=mock_synopsis
    )

    print("\n" + "="*40)
    print("RESULTADOS DEL TEST")
    print("="*40)
    
    if generated_chapters:
        for chap in generated_chapters:
            print(f"\nChapter {chap.chapter_number}: {chap.title}")
            print(f"Resume: {chap.resume[:100]}...") 
    else:
        print("No se generaron capítulos.")

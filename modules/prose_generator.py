import json
import os
from typing import List, Optional, Any
from dataclasses import dataclass, asdict, is_dataclass

from llm.base import LLM
from core.models import ChapterOutline, StorylineNode

from config import TEST_MODEL, OPENROUTER_API_KEY
from llm.openrouter import OpenRouter

@dataclass
class Chapter:
    chapter_number: int
    title: str
    outline: ChapterOutline
    storyline_nodes: List[StorylineNode]
    prose: str

class ProseGenerator:
    """
    Convierte grafos, outlines y nodos de eventos en prosa.
    """

    def __init__(self, llm: LLM, retries: int = 3):
        self.llm = llm
        self.retries = retries

    def generate_chapter(self, 
                         outline: ChapterOutline, 
                         nodes: List[StorylineNode], 
                         world_context: str, 
                         char_context: str, 
                         previous_context: str = "") -> Chapter:
        """
        Genera el texto completo de un capítulo.
        """
        
        # Formatear los nodos para el Prompt
        nodes_text = self._format_nodes(nodes)
        
        system_prompt = (
            "### IDENTITY ###\n"
            "You are an Epic Fantasy Novelist known for rich, immersive, and highly detailed storytelling. "
            "Your writing style is characterized by deep atmospheric immersion, complex internal monologues, "
            "and sensory-rich descriptions. You adhere strictly to 'Show, Don't Tell'.\n\n"

            "### OBJECTIVE ###\n"
            "Your task is to transmute a list of structural 'Event Nodes' into a FULL-LENGTH, high-word-count chapter prose. "
            "You must weave the provided 'World Context' and 'Character Context' seamlessly into the narrative.\n\n"

            "### EXPANSION PROTOCOLS (CRITICAL - MAXIMIZE LENGTH) ###\n"
            "1. **Dilate Time**: Do not rush. Treat every single Event Node not as a sentence, but as a potential scene or detailed paragraph. "
            "Expand on the micro-movements, the hesitation, and the immediate aftermath of every action.\n"
            "2. **Sensory Saturation**: Describe the texture, smell, sound, and lighting of the environment constantly. "
            "How does the magic feel on the skin? How does the ruin smell?\n"
            "3. **Internal Depth**: Dive deep into the protagonist's psyche. Between physical actions (nodes), explore their memories, fears, "
            "doubts, and immediate emotional reactions based on the 'Character Context'.\n"
            "4. **Lore Integration**: Actively use the 'World Context'. If a node mentions a sword, describe its history based on the lore provided. "
            "Make the world feel ancient and lived-in.\n\n"

            "### EXECUTION CONSTRAINTS ###\n"
            "1. **Node Fidelity**: You MUST execute every single node in the exact order provided. Do not merge, skip, or reorder them.\n"
            "2. **Continuity**: The story must flow organically from the 'Previous Chapter Ending'. Match the tone and narrative state.\n"
            "3. **No Summarizing**: Never summarize an event (e.g., do not write 'He fought the guard'). Instead, choreograph the fight blow-by-blow.\n"
            "4. **Format**: Output RAW PROSE only. No markdown headers, no 'Chapter 1', no comments. Just the story text."
        )

        user_prompt = (
            f"### CONTEXT ###\n{world_context}\n\n"
            f"### CHARACTERS ###\n{char_context}\n\n"
            f"### PREVIOUS CHAPTER ENDING ###\n...{previous_context}\n\n"
            f"### CURRENT CHAPTER PLAN ###\n"
            f"Title: {outline.title}\n"
            f"Summary: {outline.resume}\n\n"
            f"### EVENT NODES (Execute these in order) ###\n{nodes_text}\n\n"
            f"### START WRITING ###"
        )

        print(f"PROSE GENERATOR: Escribiendo capítulo {outline.chapter_number}: '{outline.title}'...")

        #  generar texto
        prose = self._generate_text_with_retry(user_prompt, system_prompt)

        return Chapter(
            chapter_number=outline.chapter_number,
            title=outline.title,
            outline=outline,
            storyline_nodes=nodes,
            prose=prose
        )

    def save_to_markdown(self, chapters: List[Chapter], filename: str, output_folder: str = "output"):
        """ todos los capítulos a un solo archivo md."""
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        filepath = os.path.join(output_folder, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            for chap in chapters:
                f.write(f"# Chapter {chap.chapter_number}: {chap.title}\n\n")
                f.write(f"{chap.prose}\n\n")
                f.write("---\n\n")
        
        print(f"    [Export] Novela exportada a Markdown: {filepath}")

    def save_to_json(self, chapters: List[Chapter], filename: str, output_folder: str = "output"):
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            
        filepath = os.path.join(output_folder, filename)
        
        class ComplexEncoder(json.JSONEncoder):
            def default(self, obj):
                if is_dataclass(obj):
                    return asdict(obj)
                return super().default(obj)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(chapters, f, indent=4, cls=ComplexEncoder, ensure_ascii=False)
            
        print(f"    [Export] Datos completos exportados a JSON: {filepath}")

    def _format_nodes(self, nodes: List[StorylineNode]) -> str:
        """Convierte la lista de nodos a un formato de texto claro para el LLM."""
        formatted = ""
        for i, node in enumerate(nodes, 1):
            formatted += f"{i}. {node.subject} -> {node.verb} -> {node.object}\n"
        return formatted

    def _generate_text_with_retry(self, prompt: str, system_prompt: str) -> str:
        """Reintenta la generación si falla la conexión."""
        import time
        
        for attempt in range(1, self.retries + 1):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools_schema=None,
                    tool_choice=None
                )
                
                if isinstance(response, dict):
                    if "content" in response:
                        return response["content"]
                    elif "choices" in response:
                        return response["choices"][0]["message"]["content"]
                elif isinstance(response, str):
                    return response
                
                raise ValueError("Formato de respuesta desconocido")

            except Exception as e:
                print(f"    [Warning] Intento {attempt} fallido al generar prosa: {e}")
                if attempt < self.retries:
                    time.sleep(2)
        
        return "[ERROR: No se pudo generar el texto del capítulo]"

if __name__ == "__main__":
    
    outline_mock = ChapterOutline(1, "The Awakening", "Kael finds the sword.")
    nodes_mock = [
        StorylineNode("Kael", "wakes up", "in the ruins"),
        StorylineNode("Kael", "sees", "a glimmering light"),
        StorylineNode("Kael", "approaches", "the ancient pedestal"),
        StorylineNode("Kael", "grasps", "the Shadow Sword"),
        StorylineNode("Shadow Sword", "whispers", "to Kael")
    ]
    
    llm_client = OpenRouter(model_name=TEST_MODEL, api_key=OPENROUTER_API_KEY)
    generator = ProseGenerator(llm_client)

    print("--- Generando Capítulo de Prueba ---")
    chapter_obj = generator.generate_chapter(
        outline=outline_mock,
        nodes=nodes_mock,
        world_context="World: Ancient ruins of Arkania, magical atmosphere.",
        char_context="Character: Kael, young thief, curious but cautious.",
        previous_context=""
    )

    print("\n--- Resultado ---")
    print(chapter_obj.prose[:500] + "...")

    generator.save_to_markdown([chapter_obj], "test_novel.md")
    generator.save_to_json([chapter_obj], "test_novel.json")

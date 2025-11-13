from llm.base import LLM
from core.models import Synopsis, ChapterOutline, StorylineNode, Chapter
from core.graph_manager import CharactersGraph, WorldRulesGraph
from modules.initial_generator import InitialGenerator
from modules.outline_generator import OutlineGenerator
from modules.storyline_generator import StorylineGenerator
from modules.coherence_checker import CoherenceChecker
from modules.text_generator import TextGenerator
from typing import List


class FantasyGenerator:
    """
    lleva a cabo todo el proceso de generación de historias.
    """

    def __init__(self, llm: LLM):
        self.llm = llm

        # componentes
        self.initial_gen = InitialGenerator(self.llm)
        self.outline_gen = OutlineGenerator(self.llm)
        self.storyline_gen = StorylineGenerator(self.llm)
        self.text_gen = TextGenerator(self.llm)

        # información relevante de generación
        self.char_graph: CharactersGraph = None
        self.world_graph: WorldRulesGraph = None
        self.synopsis: Synopsis = None
        self.checker: CoherenceChecker = None

        self.complete_story: List[Chapter] = []

    def run(self, user_prompt: str) -> str:
        """
        ejecuta todo el ciclo
        """

        # ========== generación inicial ==========
        print("Iniciando generación...")

        # generación inicial
        self.world_graph, self.char_graph, self.synopsis = self.initial_gen.generate(user_prompt)

        # se crea el Coherence Checker
        # self.checker = CoherenceChecker(self.char_graph, self.world_graph)

        # ========== generar esquema básico (información por cápitulo) ==========
        # esquema
        print("Generando esquema...")
        chapter_outlines: List[ChapterOutline] = self.outline_gen.generate(self.world_graph, self.char_graph, self.synopsis)

        # guardamos el contexto
        previous_context = self.synopsis.summary

        # ========== generación por capitulo ==========
        print(f"Iniciando bucle de generación para {len(chapter_outlines)} capítulos...")
        for outline in chapter_outlines:
            print(f"  Generando Capítulo {outline.chapter_number}: {outline.title}...")

            # generar nodos
            nodes: List[StorylineNode] = self.storyline_gen.generate(
                outline, previous_context
            )

            # checar coherencia
            coherent_nodes: List[StorylineNode] = self.checker.check_nodes(
                nodes, previous_context
            )

            # generar texto a partir de nodos
            chapter_prose = self.text_gen.generate(
                coherent_nodes, outline, previous_context
            )

            # almacenar capitulo
            chapter = Chapter(
                title=outline.title,
                outline=outline,
                storyline_nodes=coherent_nodes,
                prose=chapter_prose
            )
            self.complete_story.append(chapter)

            # contexto para el siguiente capítulo
            previous_context += f"\n\n[Resumen Capítulo {outline.chapter_number}: {outline.resume}]\n" + chapter_prose

        # ========== juntar toda la historia ==========
        print("Generación completada.")
        return self._format_final_story()

    def _format_final_story(self) -> str:
        """historia en formato .MD"""
        final_text = f"# Historia Generada\n\n## Sinopsis\n{self.synopsis.summary}\n\n"
        for chapter in self.complete_story:
            final_text += f"## {chapter.title}\n\n{chapter.prose}\n\n"
        return final_text

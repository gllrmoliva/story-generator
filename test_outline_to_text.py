# Este archivo solo busca generar un minimo viable de implementación.
from core.models import Synopsis, ChapterOutline
from core.graph_manager import WorldbuildingGraph, CharactersGraph
from config import TEST_MODEL, OPENROUTER_API_KEY
from llm.openrouter import OpenRouter
from modules.initial_generator import InitialGenerator
from modules.outline_generator import OutlineGenerator
from dataclasses import dataclass
import json
import os
from typing import List

PROSE_GEN_INSTRUCTION = """
You are a writing assistant specialized in producing high quality narrative prose. The user will provide world context, character information, and a chapter outline consisting of a title and a narrative summary.

Your task is to expand this outline into a fully developed chapter written in polished, immersive, and emotionally rich prose. The result must feel like a completed chapter in a professionally written novel.

Each generated chapter must follow these requirements:

- Produce a coherent and engaging narrative that strictly follows the events implied in the outline.
- Write between 1500 and 2500 words with strong pacing, vivid descriptions, internal and external conflicts, and dynamic character interactions.
- Use a consistent voice and tone aligned with the world context, genre, and thematic direction.
- Deepen the emotional impact of each scene and highlight the motivations, fears, and desires of all involved characters.
- Preserve logical continuity with previous chapters and the global story structure.
- Avoid meta commentary, explanations of what you are doing, or references to writing instructions.
- Do not use the symbols " or ' anywhere in the text you produce.

Guidelines:

- Expand each key moment described in the outline summary into a fully realized scene.
- Prioritize narrative flow over exposition, showing events through action, dialogue, and sensory detail.
- Maintain internal consistency with the world rules, character personalities, and their established relationships.
- Ensure that the chapter ends with a clear sense of narrative progression that naturally leads into the next outline segment.
"""

CHAPTER_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "chapter",
            "description": "Generates a full narrative chapter based on a provided outline, world context, and character information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The chapter title"
                    },
                    "prose": {
                        "type": "string",
                        "description": "The complete literary chapter produced from the outline, between 1500 and 2500 words, with coherent pacing and narrative flow"
                    }
                },
                "required": ["title", "prose"]
            }
        }
    }
]


CHAPTER_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "chapter"}
}


@dataclass
class Chapter:
    title: str
    outline: ChapterOutline
    prose: str


def save_chapters_to_single_markdown(chapters: List[Chapter], filepath: str = "novel_example.md"):
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    lines = []

    for chapter in chapters:
        lines.append(f"# {chapter.title}\n")
        lines.append(f"{chapter.prose}\n")
        lines.append("\n")

    content = "".join(lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath

if __name__ == "__main__":

    user_prompt = """In a vast continent divided by ancient magical wars,
    memories are the source of power—they can be bought, sold, or stolen, and
    whoever controls them rules history itself. A young thief with no past
    awakens in a city built upon the ruins of a forgotten empire, with only
    one clue to her identity: a fragment of memory sealed within a forbidden
    crystal. As she seeks to reclaim it, she becomes entangled in a web of
    conspiracies among noble houses, exiled sorcerers, and slumbering gods
    yearning to return. To survive, she must decide whether to recover her
    past—or destroy it before it’s used to remake the world"""

    llm = OpenRouter(model_name=TEST_MODEL,
                     api_key=OPENROUTER_API_KEY)

    print("GENERACIÓN INICIAL...")
    generator = InitialGenerator(llm)

    world_graph, chars_graph, synopsis = generator.generate(user_prompt)

    world_info = world_graph.to_llm_context_string()
    chars_info = chars_graph.to_llm_context_string()

    print("GENERACIÓN DE OUTLINES...")
    generator = OutlineGenerator(llm)

    outlines = generator.generate(world_graph_llm=world_info,
                                  char_graph_llm=chars_info,
                                  synopsis=synopsis)

    print("GENERACIÓN DE CÁPITULOS...")

    chapters = []

    for outline in outlines:
        outline_prompt = f"{world_info}\n{chars_info}\n ### OUTLINE TITLE ###\n{outline.title}" + \
                f"\n### OUTLINE RESUME ###\n{outline.resume}"

        print(f"Generando outline {outline.title}")
        chapter= json.loads(llm.generate(prompt = outline_prompt,
                    system_prompt = PROSE_GEN_INSTRUCTION,
                    tools_schema = CHAPTER_TOOL_SCHEMA,
                    tool_choice = CHAPTER_FORCE_TOOL)["tool_calls"][0]["function"]["arguments"])

        chapters.append(Chapter(title = chapter["title"],
                           prose = chapter["prose"],
                           outline = outline))

    save_chapters_to_single_markdown(chapters)
    print("Se ha generado la novela")

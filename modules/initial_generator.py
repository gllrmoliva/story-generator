from llm.base import LLM
from core.models import Synopsis
from core.graph_manager import CharactersGraph, WorldbuildingGraph

from core.tools import (CHARACTER_TOOL_SCHEMA,
                        RELATION_TOOL_SCHEMA,
                        CHARACTER_FORCE_TOOL,
                        RELATIONS_FORCE_TOOL,
                        WORLD_BUILDING_TOOL_SCHEMA,
                        WORLD_BUILDING_FORCE_TOOL,
                        SYNOPSIS_TOOL_SCHEMA,
                        SYNOPSIS_FORCE_TOOL
                        )


from core.prompts import (CHAR_GEN_INSTRUCTION,
                          WORLD_GEN_INSTRUCTION,
                          SYNOPSIS_GEN_INSTRUCTION,
                          RELATIONS_GEN_INSTRUCTION
                          )
import json

# modulos para testing
from llm.openrouter import OpenRouter
from config import TEST_MODEL, OPENROUTER_API_KEY
from pprint import pprint


# definiciones de las categorias del world graph
WB_CATEGORY_DEFINITION = {
        "ontological" : "Ontological entities define the fundamental nature of existence within the fictional world. the “why” and “how” of reality itself. They describe the metaphysical and conceptual framework that determines what can exist, how it exists, and why it follows certain rules. This includes physical laws (e.g., gravity, time flow), magical systems (e.g., energy sources, ritual mechanics), divine principles (e.g., gods as ontological forces), or metaphysical constructs (e.g., parallel planes, reincarnation cycles).",
        "material" : "Material entities refer to the tangible, physical structure of the world. Its geography, climate, ecosystems, and the distribution of natural resources. They define where and how life unfolds. This dimension covers continents, oceans, mountains, cities, flora, fauna, and the interaction between the environment and its inhabitants. Material entities establish spatial logic, environmental challenges, and the resource-based motivations that shape civilizations.",
        "sociocultural" : "Sociocultural entities define how societies organize themselves, what they believe in, and how they act collectively. They encompass systems of power (governments, empires, clans), social hierarchies (classes, castes, races), belief systems (religions, philosophies), as well as arts, traditions, and languages. They represent the moral, ideological, and symbolic life of a civilization",
        "historical" : "Historical entities represent the temporal dimension of the world. Its origins, evolution, turning points, and collective memory. They describe the narrative of change: wars, cataclysms, migrations, discoveries, revolutions, and myths that define continuity or rupture. History provides meaning to the present and foreshadows possible futures."
        }


class InitialGenerator:

    def __init__(self, llm: LLM):
        self.llm = llm
        self.character_graph = CharactersGraph()
        self.world_graph = WorldbuildingGraph()
        self.synopsis = Synopsis()

    def generate(self, user_prompt: str):

        print("INITIAL GENERATOR: Creación de World Graph...")
        # generar el world graph
        # guardamos en este las entidades por categoria
        for category, definition in WB_CATEGORY_DEFINITION.items():
            print(f"INITIAL GENERATOR: Creación de World Graph {category}...")
            entitys_generated = self.llm.generate(prompt         = user_prompt,
                                            system_prompt   = definition + WORLD_GEN_INSTRUCTION,
                                            tools_schema    = WORLD_BUILDING_TOOL_SCHEMA,
                                            tool_choice     = WORLD_BUILDING_FORCE_TOOL
                                            )["tool_calls"][0]["function"]["arguments"]

            for entity in json.loads(entitys_generated)["entity_list"]:
                self.world_graph.add_foundation(name = entity["name"], 
                                                category = category,
                                                description = entity["description"]
                                                )

        #print(self.world_graph.to_llm_context_string())

        # generar al los personajes
        print("INITIAL GENERATOR: Creación de personajes...")
        chars_generated = self.llm.generate(prompt = str(user_prompt + "\n" + \
                                       self.world_graph.to_llm_context_string()),
                                       system_prompt = CHAR_GEN_INSTRUCTION,
                                       tools_schema = CHARACTER_TOOL_SCHEMA,
                                       tool_choice = CHARACTER_FORCE_TOOL)

        for character in json.loads(chars_generated["tool_calls"][0]["function"]\
                ["arguments"])["character_list"]:
            # FIXME: El transformar a json puede fallar, hay que ver una forma de evitar eso
            self.character_graph.add_character(name         = character["name"],
                                               description  = character["description"],
                                               backstory    = character["backstory"])

         
        print("INITIAL GENERATOR: Creación de relaciones entre personajes...")
        # generar relaciones entre personajes
        relations = self.llm.generate(prompt = self.character_graph.to_llm_context_string(),
                                 system_prompt = RELATIONS_GEN_INSTRUCTION,
                                 tools_schema = RELATION_TOOL_SCHEMA,
                                 tool_choice = RELATIONS_FORCE_TOOL)

        for relation in json.loads(relations["tool_calls"][0]["function"]["arguments"])["relations_list"]:
            self.character_graph.add_relationship(char_a_name   = relation["source"],
                                                  char_b_name   = relation["target"],
                                                  relation_type = relation["relation_type"],
                                                  description   = relation["description"]
                                                  )

        print("INITIAL GENERATOR: Creación de sinopsis ...")
        gen_synopsis = self.llm.generate(prompt = user_prompt\
                                    + self.world_graph.to_llm_context_string()\
                                    + self.character_graph.to_llm_context_string(),
                                    system_prompt = SYNOPSIS_GEN_INSTRUCTION,
                                    tools_schema = SYNOPSIS_TOOL_SCHEMA,
                                    tool_choice = SYNOPSIS_FORCE_TOOL)["tool_calls"][0]["function"]["arguments"]

        self.synopsis.premise = json.loads(gen_synopsis)["premise"]
        self.synopsis.summary = json.loads(gen_synopsis)["story"]

        #self.character_graph.to_png()
        return self.world_graph, self.character_graph, self.synopsis


if __name__ == "__main__":

    user_prompt = """In a vast continent divided by ancient magical wars, memories
    are the source of power—they can be bought, sold, or stolen, and whoever controls
    them rules history itself. A young thief with no past awakens in a city built
    upon the ruins of a forgotten empire, with only one clue to her identity: a
    fragment of memory sealed within a forbidden crystal. As she seeks to reclaim
    it, she becomes entangled in a web of conspiracies among noble houses, exiled
    sorcerers, and slumbering gods yearning to return. To survive, she must decide
    whether to recover her past—or destroy it before it’s used to remake the world"""

    llm = OpenRouter(model_name = TEST_MODEL,
                     api_key = OPENROUTER_API_KEY)

    generator = InitialGenerator(llm)

    world, chars, syn = generator.generate(user_prompt)

    print(world.to_llm_context_string())
    print(chars.to_llm_context_string())
    print("### PREMISA ###\n")
    print(syn.premise)
    print("### RESUMEN ###\n")
    print(syn.summary)
    pass

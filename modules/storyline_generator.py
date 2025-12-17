from core.models import ChapterOutline, StorylineNode
from core.tools import STORYLINE_TOOL_SCHEMA
from llm.openrouter import OpenRouter
from config import OPENROUTER_API_KEY, TEST_MODEL

import json


class StorylineGenerator:
    def __init__(self, llm_client):
        """
        :param llm_client: Instance of the provided OpenRouter class.
        """
        self.llm = llm_client

    def convert_chapter_to_nodes(self, chapter: ChapterOutline):

        system_prompt = (
            "You are a High-Granularity Narrative Event Extractor. "
            "Your critical objective is to generate the MAXIMUM number of logical nodes possible from the text.\n\n"
            "### DENSITY PROTOCOLS:\n"
            "1. **Micro-Segmentation**: Never summarize. Break every sentence into multiple atomic steps. (e.g., 'He entered the room' becomes -> 'He approaches door' -> 'He opens door' -> 'He steps inside' -> 'He looks around').\n"
            "2. **Unpack Implied Actions**: Explicitly generate nodes for actions that are logically necessary but not explicitly written (e.g., if a character moves from A to B, generate: departure, travel, and arrival nodes).\n"
            "3. **Separate Internal & External**: Treat thoughts, emotions, and physical actions as separate nodes. A character feeling fear while running constitutes at least two distinct nodes.\n"
            "4. **Dialogue as Action**: Every exchange in a conversation is a separate node (Subject: Speaker, Verb: says/whispers/shouts, Object: Message Content).\n"
            "5. **Entity Rigor**: Continue to strictly resolve all pronouns to proper names. No 'he', 'she', or 'it'."
        )

        user_prompt = (
            f"Analyze the following chapter and extract the storyline nodes:\n"
            f"Chapter {chapter.chapter_number}: {chapter.title}\n"
            f"Summary: {chapter.resume}"
        )

        tool_choice = {
            "type": "function",
            "function": {"name": "generate_storyline_nodes"}
        }

        response_payload = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            tools_schema=[STORYLINE_TOOL_SCHEMA],
            tool_choice=tool_choice
        )
        result_nodes = self._parse_response(response_payload)

        return result_nodes

    def _parse_response(self, response_payload):

        if isinstance(response_payload, str):

            if response_payload.startswith("[Error"):
                print(f"LLM Generation Failed: {response_payload}")
                return []
            else:
                print("LLM returned plain text instead of JSON structure.")
                return []

        tool_calls = response_payload.get("tool_calls")
        if not tool_calls:
            print("No tool calls found in response.")
            return []

        try:
            function_args_str = tool_calls[0]['function']['arguments']
            function_args = json.loads(function_args_str)
            
            nodes_data = function_args.get("nodes", [])
            
            result_nodes = [
                StorylineNode(
                    subject=node["subject"],
                    verb=node["verb"],
                    object=node["object"]
                )
                for node in nodes_data
            ]
            return result_nodes

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Failed to parse LLM response structure: {e}")
            return []


if __name__ == "__main__":

    client = OpenRouter(model_name=TEST_MODEL, api_key=OPENROUTER_API_KEY)
    service = StorylineGenerator(client)

    chapter_one = ChapterOutline(
        chapter_number=0,
        title="The Echo of the Past",
        resume=(
            """
            The story opens with sweeping vistas of a realm marred by the ongoing Divine War. Glimpses of the Shattered Plains and the vibrant, chaotic energies surrounding the Rift of Aeterna introduce the reader to a landscape scarred by divine conflict. The chapter is narrated from the perspective of Elara Stormwind, whose silver hair glints in the sunlight as she witnesses a rally of mortals gathered to celebrate the Festival of Fallen Stars. The festival, filled with song and dance, serves as a stark contrast to the haunted memories of battles past. Amidst the festivities, Elara feels a weight on her shoulders—a burden as the Divine Mediator—to foster peace among realms still rife with conflict. She reflects on her purpose and the heavy decisions to be made as she contemplates her role as a bridge between deities and mortals.
            """
        )
    )

    nodes = service.convert_chapter_to_nodes(chapter_one)

    print(f"--- Nodes for Chapter {chapter_one.chapter_number} ---")
    for node in nodes:
        print(f"S: {node.subject} | V: {node.verb} | O: {node.object}")


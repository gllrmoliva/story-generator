import json
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass, asdict, fields

from core.models import StorylineNode, ChapterOutline

REFINEMENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "rewrite_storyline_nodes",
        "description": "Returns the corrected list of storyline nodes after checking for consistency and world rules.",
        "parameters": {
            "type": "object",
            "properties": {
                "nodes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string"},
                            "verb": {"type": "string"},
                            "object": {"type": "string"}
                        },
                        "required": ["subject", "verb", "object"]
                    }
                }
            },
            "required": ["nodes"]
        }
    }
}

VALIDATION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "validate_storyline_alignment",
        "description": "Validates if the generated nodes match the chapter outline.",
        "parameters": {
            "type": "object",
            "properties": {
                "is_valid": {
                    "type": "boolean",
                    "description": "True if the nodes logically follow the outline. False if there are major hallucinations or contradictions."
                },
                "feedback": {
                    "type": "string",
                    "description": "Explanation of why the validation passed or failed."
                }
            },
            "required": ["is_valid", "feedback"]
        }
    }
}


class CoherenceChecker:
    """
    checkea coherencia de nodos
    """

    def __init__(self, llm_client, char_graph, world_graph):
        self.llm = llm_client
        self.char_graph = char_graph
        self.world_graph = world_graph

    def check_nodes(self,
                    past_nodes: List[StorylineNode],
                    past_nodes_window: int, 
                    current_nodes: List[StorylineNode], 
                    outline: ChapterOutline) -> Tuple[bool, List[StorylineNode]]:
        
        recent_history = past_nodes[-past_nodes_window:] if past_nodes else []
        
        context_data = {
            "world_rules": str(self.world_graph.to_llm_context_string()),
            "characters": str(self.char_graph.to_llm_context_string())
        }

        print(f"    (Checker: Received {len(current_nodes)} nodes. Context Window: {len(recent_history)})")

        refined_nodes = self._refine_nodes(recent_history, current_nodes, context_data)
        
        is_valid, validation_msg = self._validate_alignment(refined_nodes, outline)

        if not is_valid:
            print(f"    (Checker Warning: Validation Failed - {validation_msg})")
        else:
            print("    (Checker: Validation Passed)")

        return is_valid, refined_nodes

    def _refine_nodes(self, history: List[StorylineNode], current: List[StorylineNode], context: Dict) -> List[StorylineNode]:
        """
        usa LLM para reescribir nodos.
        """
        
        history_dicts = [asdict(n) for n in history]
        current_dicts = [asdict(n) for n in current]

        system_prompt = (
            "You are a Continuity Editor and Lore Master. "
            "Your task is to REWRITE the 'Current Nodes' to ensure they are consistent with "
            "the 'World Rules', 'Character Profiles', and 'Recent History'.\n"
            "GUIDELINES:\n"
            "1. Fix contradictions (e.g., if a character is dead in history, they cannot act now).\n"
            "2. Enforce magic/physics rules defined in World Rules.\n"
            "3. If nodes are too simple or repetitive, merge them into a more significant event node.\n"
            "4. Maintain the High-Granularity format (Subject, Verb, Object).\n"
            "5. Return the cleaned, corrected list of nodes."
        )

        user_prompt = (
            f"### CONTEXT\n{json.dumps(context, indent=2)}\n\n"
            f"### RECENT HISTORY\n{json.dumps(history_dicts, indent=2)}\n\n"
            f"### CURRENT NODES (Draft)\n{json.dumps(current_dicts, indent=2)}\n\n"
            f"Fix inconsistencies and return the refined nodes."
        )

        tool_choice = {"type": "function", "function": {"name": "rewrite_storyline_nodes"}}

        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            tools_schema=[REFINEMENT_SCHEMA],
            tool_choice=tool_choice
        )

        return self._parse_nodes_response(response)

    def _validate_alignment(self, nodes: List[StorylineNode], outline: ChapterOutline) -> Tuple[bool, str]:
        """
        LLM checkea si los nodos están alucinando o no 

        """
        nodes_summary = "\n".join([f"- {n.subject} {n.verb} {n.object}" for n in nodes])

        system_prompt = (
            "You are a Narrative Granulator and Continuity Engine. "
            "Your task is to REWRITE and EXPAND the 'Current Nodes' sequence.\n"
            "You must transform high-level summaries into detailed, atomic chains of events "
            "while strictly enforcing World Rules and Character Status.\n\n"
            "### EXPANSION PROTOCOLS (MANDATORY):\n"
            "1. **Atomize Actions**: Never allow abstract verbs like 'travels', 'fights', or 'convinces'. Break them down.\n"
            "   - Example: 'Kael fights the Orc' -> BECOMES -> 'Kael draws sword' -> 'Orc roars' -> 'Kael dodges attack' -> 'Kael strikes Orc'.\n"
            "2. **Insert Logical Bridges**: If there is a gap between Node A and Node B, insert intermediate nodes to explain HOW the transition happened.\n"
            "3. **Stimulus-Response Cycle**: For every significant action, insert a reaction node (emotional or physical) for the affected entities.\n"
            "4. **Enforce World Logic**: Check 'World Rules'. If magic requires energy, insert a node for 'gathering energy' before 'casting'. Fix contradictions (e.g., dead characters acting).\n"
            "5. **Environmental Integration**: Insert nodes where characters interact with the setting described in 'World Rules' (e.g., struggling with terrain, reacting to weather).\n"
            "6. **Format**: Maintain the strict (Subject, Verb, Object) structure."
        )

        user_prompt = (
            f"### CHAPTER OUTLINE\nTitle: {outline.title}\nResume: {outline.resume}\n\n"
            f"### GENERATED NODES\n{nodes_summary}\n\n"
            f"Evaluate validity."
        )

        tool_choice = {"type": "function", "function": {"name": "validate_storyline_alignment"}}

        response = self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            tools_schema=[VALIDATION_SCHEMA],
            tool_choice=tool_choice
        )

        # parsing manual para el esquema de validación
        try:
            tool_calls = response.get("tool_calls")
            if tool_calls:
                args = json.loads(tool_calls[0]['function']['arguments'])
                return args.get("is_valid", False), args.get("feedback", "No feedback provided.")
        except Exception as e:
            print(f"Validation parsing error: {e}")
            
        return False, "Error parsing validation response"

    def _parse_nodes_response(self, response: Any) -> List[StorylineNode]:
        """
        parsear nodos de respuesta json de llm
        """
        if not isinstance(response, dict):
            print(f"Error: La respuesta del LLM no es un dict válido. Recibido: {type(response)}")
            return []

        tool_calls = response.get("tool_calls")
        if not tool_calls:
            content = response.get("content", "")
            if content:
                print(f"Warning: El LLM no usó tools. Contenido raw: {content[:50]}...")
            return []

        try:
            args_str = tool_calls[0]['function']['arguments']
            args = json.loads(args_str)
            raw_nodes = args.get("nodes", [])

            valid_nodes = []
            
            valid_fields = {f.name for f in fields(StorylineNode)}

            for i, raw_node in enumerate(raw_nodes):
                try:
                    clean_node_data = {k: v for k, v in raw_node.items() if k in valid_fields}
                    
                    if "subject" not in clean_node_data or "verb" not in clean_node_data:
                        print(f"Node {i} skipped: Falta subject o verb.")
                        continue

                    node = StorylineNode(**clean_node_data)
                    valid_nodes.append(node)

                except TypeError as e:
                    print(f"Error instanciando nodo {i}: {e} | Data: {raw_node}")
                except Exception as e:
                    print(f"Error inesperado en nodo {i}: {e}")

            return valid_nodes

        except json.JSONDecodeError as e:
            print(f"Error crítico: El LLM devolvió un JSON inválido en arguments: {e}")
            # print(f"Raw arguments: {tool_calls[0]['function']['arguments']}")
            return []
        except Exception as e:
            print(f"Error crítico parsing response: {e}")
            return []

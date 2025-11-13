from core.graph_manager import CharactersGraph, WorldRulesGraph
from core.models import StorylineNode
from typing import List

# TODO: Puede que sea necesario hacer un merger de nodos, para que sean más
# complejos y no tan sencillos. Esto para aprovechar mejor los tokens de inicio
# por ahora solo se descartan
# TODO: Posiblemente usar LLM igual jejeje


class CoherenceChecker:
    """
    verifica que los nodos de la historia tengan sentido
    """

    def __init__(self, char_graph: CharactersGraph, world_graph: WorldRulesGraph):
        self.char_graph = char_graph
        self.world_graph = world_graph

    def check_nodes(self, nodes: List[StorylineNode], context: str) -> List[StorylineNode]:
        """
        corregir nodos basándose en los grafos.
        """
        print(f"    (Checker: Recibidos {len(nodes)} nodos para revisión)")

        coherent_nodes = []
        for node in nodes:
            # Lógica de validación (simplificada)
            # 1. Validar contra Grafo de Personajes
            char_is_consistent = self.char_graph.validate_action(
                node.subject, node.verb, node.object
            )

            # 2. Validar contra Grafo de Reglas
            world_is_consistent = self.world_graph.validate_action(
                node.subject, node.verb, node.object
            )

            if char_is_consistent and world_is_consistent:
                coherent_nodes.append(node)
            else:
                # El diagrama indica "add corrected nodes".
                # Esto implica una corrección, no solo un filtrado.
                # Esta lógica es compleja (podría requerir otro LLM call).
                # Por simplicidad aquí, se filtran.
                print(f"    (Checker: Nodo DESCARTADO por inconsistencia: {node})")

        print(f"    (Checker: {len(coherent_nodes)} nodos coherentes)")
        return coherent_nodes

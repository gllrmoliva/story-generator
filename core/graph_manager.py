import networkx as nx
import json
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Optional, Union, Any

class CharactersGraph:
    def __init__(self):
        # Se usa digrafo, ya que relaciones no siempre son simétricas
        self.graph = nx.DiGraph()

    def add_character(self, name: str, description: Dict[str, Any], backstory: str):
        """
        Añade un personaje al grafo.
        """
        self.graph.add_node(
            name, 
            description=description, 
            backstory=backstory
        )

    def add_relationship(self, char_a_name: str, char_b_name: str, relation_type: str, description: str = ""):
        """
        Añade relación dirigida entre dos personajes.
        """
        if not self.graph.has_node(char_a_name) or not self.graph.has_node(char_b_name):
            print(f"Warning: Intento de relacionar personajes inexistentes ({char_a_name} -> {char_b_name}).")
            return
            
        self.graph.add_edge(
            char_a_name, 
            char_b_name, 
            type=relation_type,
            details=description
        )

    def get_character_info(self, name: str) -> Optional[Dict]:
        """Obtener información de un nodo de personaje."""
        if self.graph.has_node(name):
            return self.graph.nodes[name]
        return None

    def to_llm_context_string(self) -> str:
        """Transforma toda la información del grafo a un string legible por LLM."""
        context = "### Character Knowledge Base ###\n\n"
        
        context += "== Characters ==\n"
        if not self.graph.nodes:
            context += "(No characters defined yet)\n"

        for node, data in self.graph.nodes(data=True):
            context += f"-- Character: {node} --\n"
            context += "Description:\n"
            for key, val in data.get('description', {}).items():
                context += f"  - {key.capitalize()}: {val}\n"
            context += f"Back History: {data.get('backstory', 'N/A')}\n\n"
        
        context += "== Relationships ==\n"
        if not self.graph.edges:
            context += "(No relationships defined)\n"

        for u, v, data in self.graph.edges(data=True):
            relation = data.get('type', 'related to')
            details = f" ({data['details']})" if data.get('details') else ""
            context += f"[{u}] --{relation}--> [{v}]{details}\n"
            
        return context

    def to_dict(self) -> Dict:
        """Retorna el grafo en formato diccionario (compatible con JSON)."""
        return nx.node_link_data(self.graph)

    def to_json(self) -> str:
        """Retorna string JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_png(self, output_path: str = "characters_graph.png"):
        """
        Guarda el grafo como PNG.
        Args:
            output_path: Puede ser un nombre de archivo (ej: "mi_grafo.png") 
                         o un directorio existente.
        """
        if self.graph.number_of_nodes() == 0:
            print("Graph is empty, skipping PNG generation.")
            return

        # Lógica inteligente para determinar la ruta
        if os.path.isdir(output_path):
            # Si es un directorio, añadimos el nombre por defecto
            filepath = os.path.join(output_path, "characters_graph.png")
        else:
            # Si no, asumimos que es el path completo del archivo
            filepath = output_path
            # Aseguramos que el directorio padre exista
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        plt.figure(figsize=(10, 8))
        
        # Seed para que el grafo no "baile" cada vez que se genera
        pos = nx.spring_layout(self.graph, k=0.9, seed=42)

        nx.draw(
            self.graph, pos, 
            with_labels=True, 
            node_color='lightblue', 
            edge_color='gray', 
            node_size=3000,
            font_size=9,
            font_weight='bold',
            arrows=True
        )

        edge_labels = { (u, v): data.get("type", "") for u, v, data in self.graph.edges(data=True) }
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8, label_pos=0.5)

        plt.title("Character Relationships Map")
        plt.savefig(filepath, format="png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    [Graph] Characters Graph guardado en: {filepath}")


class WorldbuildingGraph:
    def __init__(self):
        # Definimos los grafos internos
        self.graphs = {
            "ontological": nx.Graph(),
            "material": nx.Graph(),
            "sociocultural": nx.Graph(),
            "historical": nx.Graph()
        }

    def add_foundation(self, name: str, category: str, description: str):
        if category not in self.graphs:
            print(f"Error: Categoría '{category}' desconocida.")
            return

        g = self.graphs[category]
        if g.has_node(name):
            # Actualizar si existe (opcional) o ignorar
            pass

        g.add_node(
            name,
            category=category,
            description=description
        )

    def add_relation(self, category: str, source: str, target: str, relation_type: str, explanation: str = ""):
        if category not in self.graphs:
            return
        
        g = self.graphs[category]
        # Crear nodos si no existen para evitar crashes,
        # aunque lo ideal es que existan.
        if not g.has_node(source):
            g.add_node(source, description="Unknown entity")
        if not g.has_node(target):
            g.add_node(target, description="Unknown entity")

        g.add_edge(
            source,
            target,
            type=relation_type,
            explanation=explanation
        )

    def to_llm_context_string(self) -> str:
        context = "### Worldbuilding Context ###\n\n"
        for category, g in self.graphs.items():
            context += f"== {category.upper()} DOMAIN ==\n"
            if g.number_of_nodes() == 0:
                context += "(Empty)\n\n"
                continue

            for node, data in g.nodes(data=True):
                context += f"* {node}: {data.get('description', 'No description')}\n"
            
            if g.number_of_edges() > 0:
                context += "  Relationships:\n"
                for u, v, data in g.edges(data=True):
                    expl = f" ({data.get('explanation')})" if data.get('explanation') else ""
                    context += f"    - {u} is {data.get('type')} {v}{expl}\n"
            context += "\n"
        return context

    def to_dict(self) -> Dict:
        """Exporta todos los subgrafos a un diccionario."""
        return {
            category: nx.node_link_data(g)
            for category, g in self.graphs.items()
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_png(self, output_dir: str = ".", layout: str = "spring"):
        """
        Genera imágenes PNG para cada sub-grafo.
        
        Args:
            output_dir: Directorio donde se guardarán las imágenes.
            layout: Algoritmo de distribución (para distribuir nodos).
        """
        # Asegurar que el directorio existe
        os.makedirs(output_dir, exist_ok=True)

        layouts = {
            "spring": lambda G: nx.spring_layout(G, k=0.8, seed=42), # Seed para consistencia
            "circular": nx.circular_layout,
            "shell": nx.shell_layout
        }
        
        layout_func = layouts.get(layout, layouts["spring"])

        for category, g in self.graphs.items():
            if g.number_of_nodes() == 0:
                continue

            plt.figure(figsize=(8, 6))
            try:
                pos = layout_func(g)
                
                nx.draw(
                    g, pos,
                    with_labels=True,
                    node_color="#98FB98", # PaleGreen
                    edge_color="#555555",
                    node_size=2000,
                    font_size=8,
                    font_weight="bold"
                )

                edge_labels = { (u, v): data.get("type", "") for u, v, data in g.edges(data=True) }
                nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, font_size=7)

                # Construir ruta
                filename = f"{category}_graph.png"
                filepath = os.path.join(output_dir, filename)
                
                plt.title(f"World: {category.capitalize()}")
                plt.savefig(filepath, format="png", dpi=300, bbox_inches="tight")
                print(f"    [Graph] {category.capitalize()} guardado en: {filepath}")
                
            except Exception as e:
                print(f"    [Error] Fallo dibujando grafo {category}: {e}")
            finally:
                plt.close() #LIBERAR!!!!

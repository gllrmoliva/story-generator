import networkx as nx
import json
import matplotlib.pyplot as plt

# TODO
# - Implemetar función load y save, puede ser util para no gastar tantos tokens.
# Habría que guardar datos en una carpeta distinta por generación probablemente.
# - agregar relaciones a grafo del mundo

class CharactersGraph:
    def __init__(self):
        # se usa digrafo, ya que relaciones no siempre son simétricas
        self.graph = nx.DiGraph()

    def add_character(self, name, description, backstory):
        """
        añadir un personaje al grafo.
        
        Args:
            name (str): nombre. (no se repiten entre personajes)
            description (dict): diccionario con claves como 'clase', 'edad', 'raza', etc.
            backstory (str): historia del personaje.
        """

        self.graph.add_node(
            name, 
            description=description, 
            backstory=backstory
        )

    def add_relationship(self, char_a_name, char_b_name, relation_type, description=""):
        """
        añadir relación entre dos personajes.
        
        Args:
            char_a_name (str): personaje de origen.
            char_b_name (str): personaje de destino.
            relation_type (str): relación.
            description (str, optional): información extra.
        """
        if not self.graph.has_node(char_a_name) or not self.graph.has_node(char_b_name):
            print("ERROR: uno o ambos personajes no existen. No se puede crear relación.")
            return
            
        self.graph.add_edge(
            char_a_name, 
            char_b_name, 
            type=relation_type,
            details=description
        )

    def get_character_info(self, name):
        """obtener información de un nodo de personaje."""
        if self.graph.has_node(name):
            return self.graph.nodes[name]
        return None

    def get_relationships(self, name):
        """obtener las relaciones de un personaje."""
        if not self.graph.has_node(name):
            return None
        
        outgoing = [(v, data) for u, v, data in self.graph.out_edges(name, data=True)]
        incoming = [(u, data) for u, v, data in self.graph.in_edges(name, data=True)]
        
        return {"outgoing": outgoing, "incoming": incoming}

    def to_llm_context_string(self):
        """
        Transforma toda la información del grafo a un string que un LLM puede entender.
        """
        context = "### Character Knowledge Base ###\n\n"
        
        context += "== Characters ==\n"
        for node, data in self.graph.nodes(data=True):
            context += f"-- Character: {node} --\n"
            context += "Description:\n"
            for key, val in data.get('description', {}).items():
                context += f"  - {key.capitalize()}: {val}\n"
            context += f"Back History: {data.get('backstory', 'N/A')}\n\n"
        
        context += "== Relationships between characters ==\n"
        for u, v, data in self.graph.edges(data=True):
            relation = data.get('type', 'relationed with')
            details = f" (Details: {data['details']})" if data.get('details') else ""
            context += f"[{u}] --({relation})--> [{v}]{details}\n"
            
        return context

    def to_json(self):
        """Convertir grafo a JSON."""

        data = nx.node_link_data(self.graph)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def to_png(self):

        pos = nx.spring_layout(self.graph, k=0.8)

        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size = 2500)

        edge_labels = { (u, v): data.get("type", "") for u, v, data in self.graph.edges(data=True) }

        nx.draw_networkx_edge_labels(self.graph,pos, edge_labels=edge_labels, font_size=8, label_pos=0.5)

        plt.savefig("characters_graph.png", format="png", dpi=300, bbox_inches='tight')
        plt.close()
        print("Se ha guardado el Grafo de Personajes en .png correctamente!")


class WorldbuildingGraph:
    def __init__(self):
        self.graphs = {
            "ontological": nx.Graph(),
            "material": nx.Graph(),
            "sociocultural": nx.Graph(),
            "historical": nx.Graph()
        }

        """
        - ontological: Cómo y por qué existe el mundo. Sus leyes internas: físicas, mágicas o metafísicas. 
        - material: La configuración física del entorno y sus recursos. Geografía, clima, ecosistemas y su relación con la vida que los habita.
        - sociocultural: Cómo se estructura la vida colectiva: poder, creencias, costumbres, valores. Instituciones, jerarquías, religión, arte, lenguaje.
        - historical: El pasado y la memoria del mundo: origen, evolución, conflictos y mitos. La tensión entre lo que fue, lo que es y lo que podría ser.
        """

    def add_foundation(self, name, category, description):

        if category not in self.graphs:
            print(f"ERROR: categoria inválida'{category}'.")
            return

        g = self.graphs[category]
        if g.has_node(name):
            print(f"WARNING: elemento '{name}' ya existe en '{category}'.")
            return

        g.add_node(
            name,
            category=category,
            description=description
        )

    def add_relation(self, category, source, target, relation_type, explanation=""):
        if category not in self.graphs:
            print(f"ERROR: categoria inválida'{category}'.")
            return
        
        g = self.graphs[category]
        if not g.has_node(source) or not g.has_node(target):
            print("ERROR: al menos uno de los elementos no existe en el grafo.")
            return

        g.add_edge(
            source,
            target,
            type=relation_type,
            explanation=explanation
        )

    def get_foundation_info(self, category, name):
        g = self.graphs.get(category)
        if not g or not g.has_node(name):
            return None
        return g.nodes[name]

    def get_relations(self, category, name):
        g = self.graphs.get(category)
        if not g or not g.has_node(name):
            return None

        outgoing = [(v, data) for u, v, data in g.out_edges(name, data=True)]
        incoming = [(u, data) for u, v, data in g.in_edges(name, data=True)]
        
        return {"outgoing": outgoing, "incoming": incoming}

    def to_llm_context_string(self):
        context = "### Worldbuilding Multi-Graph ###\n\n"

        for category, g in self.graphs.items():
            context += f"== {category.upper()} ==\n"
            if not g.nodes:
                context += "(no foundations defined)\n\n"
                continue

            for node, data in g.nodes(data=True):
                context += f"-- Foundation: {node} --\n"
                context += f"Description: {data.get('description')}\n"
                if data.get('details'):
                    context += "Details:\n"
                    for k, v in data['details'].items():
                        context += f"  - {k.capitalize()}: {v}\n"
                context += "\n"

            context += "Relations:\n"
            for u, v, data in g.edges(data=True):
                relation = data.get('type', 'related to')
                expl = f" (Explanation: {data['explanation']})" if data.get('explanation') else ""
                context += f"[{u}] --({relation})--> [{v}]{expl}\n"
            context += "\n"
        return context

    def to_json(self):
        """Export all subgraphs into a structured JSON file."""

        all_data = {
            category: nx.node_link_data(g)
            for category, g in self.graphs.items()
        }
        return json.dumps(all_data, indent=2, ensure_ascii=False)


if __name__ == "__main__":

    char_graph = CharactersGraph()
    
    juanito_desc= {
        "class": "Caballero",
        "age": 27,
        "race": "Humano",
        "sex": "Masculino",
        "physical_description": "Alto, cabello oscuro, ojos grises, aspecto rudo pero noble."
    }
    
    juanita_desc = {
        "class": "Princesa",
        "age": 2778,
        "race": "Medioelfa",
        "sex": "Femenino",
        "physical_description": "Belleza etérea, cabello oscuro, ojos claros."
    }
    
    char_graph.add_character("Juanito", juanito_desc, "Es un caballero muy valiente.")
    char_graph.add_character("Juanita", juanita_desc, "Es una elfa muy bonita.")
    char_graph.add_character("Pedrito", {"clase": "Mago", "raza": "Medioelfo"}, "El magordito")
    
    char_graph.add_relationship("Juanito", "Juanita", "ama_a", "Están prometidos.")
    char_graph.add_relationship("Juanita", "Juanito", "ama_a", "Renunciará a su herencia por él.")
    char_graph.add_relationship("Pedrito", "Juanito", "mentor_de", "Actuó como su mentor.")
    char_graph.add_relationship("Pedrito", "Juanita", "padre_de")
    
    char_graph.to_png()

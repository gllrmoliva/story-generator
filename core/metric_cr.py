import json
import time
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from llm.openrouter import OpenRouter
from config import OPENROUTER_API_KEY, TEST_MODEL

COHERENCE_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "report_coherence_conflicts",
            "description": "Analyze a narrative sequence and report logical, causal, or physical contradictions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conflict_count": {
                        "type": "integer",
                        "description": "The numeric count of contradictions found in the text batch."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "A concise explanation of the conflicts found, citing node IDs."
                    }
                },
                "required": ["conflict_count", "reasoning"]
            }
        }
    }
]

COHERENCE_FORCE_TOOL = {
    "type": "function", 
    "function": {"name": "report_coherence_conflicts"}
}

COHERENCE_SYSTEM_PROMPT = """
You are an expert Narrative Continuity Supervisor. 
Your task is to analyze a sequential list of narrative nodes (events) and detect **Coherence Conflicts**.

Look for:
1. **Physical Impossibilities:** A character is in two places at once.
2. **State Errors:** A character acts alive after dying, or wakes up without sleeping.
3. **Causal Failures:** Reacting to an event that hasn't happened yet in the sequence.

Analyze the provided batch of nodes. Return the count of distinct conflicts found.
"""


class CRMetric:
    """
    Calcula la métrica de Coherencia (CR) procesando nodos narrativos
    a través de un LLM para detectar contradicciones (m).
    """

    def __init__(self, llm: OpenRouter, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    def load_and_flatten_nodes(self, json_path: Path) -> List[str]:
        """
        parsear nodos
        """
        try:
            content = json_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as e:
            print(f"[CRMetric Error] No se pudo leer el JSON: {e}")
            sys.exit(1)

        flat_nodes = []
        global_id = 1

        # Aplanar la estructura: ignoramos capítulos, solo nos importa la secuencia lineal
        for chapter in data:
            nodes = chapter.get("storyline_nodes", [])
            for node in nodes:
                # Formateamos el nodo para que el LLM lo entienda
                node_text = (
                    f"[ID:{global_id}] "
                    f"Subject: {node.get('subject', '?')} | "
                    f"Verb: {node.get('verb', '?')} | "
                    f"Object: {node.get('object', '?')}"
                )
                flat_nodes.append(node_text)
                global_id += 1
        
        return flat_nodes

    def calculate(self, json_path: Path, batch_size: int = 20):
        """
        Obtener la métrica.
        """

        print(f"--- [CRMetric] Cargando archivo: {json_path.name} ---")
        all_nodes = self.load_and_flatten_nodes(json_path)
        total_nodes_N = len(all_nodes)
        
        if total_nodes_N == 0:
            print("[CRMetric Error] No se encontraron nodos (N=0).")
            return 0.0

        print(f"Total Nodos (N): {total_nodes_N}")
        print(f"Tamaño de Batch: {batch_size}")
        print("Iniciando detección de conflictos (m)...\n")

        total_conflicts_m = 0
        
        for i in range(0, total_nodes_N, batch_size):
            batch = all_nodes[i : i + batch_size]
            batch_text = "\n".join(batch)
            
            print(f" > Analizando batch {i//batch_size + 1}...", end=" ", flush=True)

            prompt = f"## NARRATIVE SEQUENCE BATCH ##\n{batch_text}"
            
            result = self._generate_with_retry(
                prompt=prompt,
                system_prompt=COHERENCE_SYSTEM_PROMPT,
                context_desc=f"Batch {i//batch_size + 1}"
            )

            if result:
                count = result.get("conflict_count", 0)
                reasoning = result.get("reasoning", "")
                total_conflicts_m += count
                print(f"OK. Conflictos detectados: {count}")
                if count > 0:
                    print(f"   [Detalle]: {reasoning}")
            else:
                print("FALLO. Se asumen 0 conflictos.")

        cr_percentage = (total_conflicts_m / total_nodes_N) * 100
        
        self._print_report(total_nodes_N, total_conflicts_m, cr_percentage)
        
        return cr_percentage

    def _print_report(self, N, m, cr):
        print("\n" + "="*40)
        print(" REPORTE FINAL: CR Metric")
        print("="*40)
        print(f"Total Tuplas (N):     {N}")
        print(f"Total Conflictos (m): {m}")
        print("-" * 40)
        print(f"CR Score:             {cr:.2f}%")
        print("="*40)

    def _generate_with_retry(self, prompt: str, system_prompt: str, context_desc: str) -> Optional[Dict[str, Any]]:
        """
        Reintentos por si el sistema falla.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools_schema=COHERENCE_TOOL_SCHEMA,
                    tool_choice=COHERENCE_FORCE_TOOL
                )
                
                parsed = self._parse_tool_response(response)
                if parsed:
                    return parsed
                
                print(f"[Warn] Intento {attempt} formato inválido.")

            except Exception as e:
                print(f"[Error] Intento {attempt} excepción: {e}")
            
            if attempt < self.max_retries:
                time.sleep(1)

        return None

    def _parse_tool_response(self, response: Any) -> Optional[Dict[str, Any]]:
        """
        Extrae JSON de la respuesta del tool.
        """
        if not isinstance(response, dict):
            return None
        
        tool_calls = response.get("tool_calls")
        if not tool_calls:
            return None

        try:
            args_str = tool_calls[0]['function']['arguments']
            return json.loads(args_str)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecuta la métrica CR (Coherence Rate) sobre un JSON.")
    parser.add_argument("filepath", type=str, help="Ruta al archivo .json")
    parser.add_argument("--batch", type=int, default=20, help="Tamaño del batch de nodos (Defecto: 20)")
    parser.add_argument("--model", type=str, default=TEST_MODEL, help="Modelo a usar")
    
    args = parser.parse_args()
    
    file_path = Path(args.filepath)
    if not file_path.exists():
        print(f"Error: No existe el archivo '{file_path}'")
        sys.exit(1)

    if not OPENROUTER_API_KEY:
        print("Error: Falta OPENROUTER_API_KEY")
        sys.exit(1)

    # Instanciar LLM
    llm_client = OpenRouter(model_name=args.model, api_key=OPENROUTER_API_KEY)

    # Instanciar Métrica
    metric = CRMetric(llm=llm_client)

    # Calcular
    metric.calculate(file_path, batch_size=args.batch)

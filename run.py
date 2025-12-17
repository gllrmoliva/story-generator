import os
import json
import time
import yaml
from datetime import datetime
from dataclasses import asdict, is_dataclass
from typing import List, Any, Dict

from config import OPENROUTER_API_KEY
from llm.openrouter import OpenRouter

from core.models import Synopsis, ChapterOutline, StorylineNode
from core.graph_manager import WorldbuildingGraph, CharactersGraph

from modules.initial_generator import InitialGenerator
from modules.outline_generator import OutlineGenerator
from modules.storyline_generator import StorylineGenerator
from modules.coherence_checker import CoherenceChecker
from modules.prose_generator import ProseGenerator


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, 'to_dict'): 
            return obj.to_dict()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)


def save_json(data: Any, filename: str, folder: str):
    if not os.path.exists(folder):
        os.makedirs(folder)
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, cls=ComplexEncoder, ensure_ascii=False)
    print(f"    [Saved] {filename}")


def load_requests(filename="requests.yml") -> List[Dict]:
    """Carga la lista de requests desde el YAML."""
    if not os.path.exists(filename):
        print(f"[Error] No se encontró {filename}")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("requests", [])


def get_llm(model_name: str) -> OpenRouter:
    """Factory para crear instancias de LLM según el modelo."""
    return OpenRouter(model_name=model_name, api_key=OPENROUTER_API_KEY)


def run_pipeline(config: Dict):
    req_name = config.get("name", "Untitled")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = config.get("output_folder", "output")
    output_dir = os.path.join(base_output, f"{req_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    comps = config["components"]
    
    print(f"\n=== EJECUTANDO: {req_name} ===")
    print(f"=== SALIDA: {output_dir} ===")

    conf_init = comps["initial_generator"]
    print(f"\n[1/5] GENERANDO WORLD & CHARACTERS ({conf_init['model']})...")
    
    llm_init = get_llm(conf_init["model"])
    init_gen = InitialGenerator(llm_init, max_retries=conf_init.get("retries", 3))
    
    world_graph, chars_graph, synopsis = init_gen.generate(config["prompt"])

    graphs_dir = os.path.join(output_dir, "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    
    print(f"    Guardando gráficos...")
    world_graph.to_png(graphs_dir) 
    
    try:
        chars_graph.to_png(os.path.join(graphs_dir, "characters_graph.png"))
    except TypeError:
        chars_graph.to_png()
        import shutil
        if os.path.exists("characters_graph.png"):
            shutil.move("characters_graph.png", os.path.join(graphs_dir, "characters_graph.png"))

    context_data = {
        "synopsis": synopsis,
        "world_context": world_graph.to_llm_context_string(),
        "chars_context": chars_graph.to_llm_context_string()
    }
    save_json(context_data, "01_foundations.json", output_dir)

    conf_outline = comps["outline_generator"]
    print(f"\n[2/5] GENERANDO OUTLINES ({conf_outline['model']})...")
    
    llm_outline = get_llm(conf_outline["model"])
    outline_gen = OutlineGenerator(llm_outline, max_retries=conf_outline.get("retries", 3))
    
    outlines = outline_gen.generate(
        world_graph_llm=context_data["world_context"],
        char_graph_llm=context_data["chars_context"],
        synopsis=synopsis
    )
    save_json(outlines, "02_outlines.json", output_dir)

    print("\n[3/5] INICIANDO MOTOR DE NARRATIVA...")

    conf_story = comps["storyline_generator"]
    llm_story = get_llm(conf_story["model"])
    storyline_gen = StorylineGenerator(llm_story)

    conf_checker = comps["coherence_checker"]
    use_checker = conf_checker.get("enabled", True)
    
    if use_checker:
        llm_checker = get_llm(conf_checker["model"])
        coherence_checker = CoherenceChecker(llm_checker, chars_graph, world_graph)
        print(f"    [Info] Coherence Checker ACTIVO ({conf_checker['model']})")
    else:
        print(f"    [Info] Coherence Checker DESACTIVADO")

    conf_prose = comps["prose_generator"]
    llm_prose = get_llm(conf_prose["model"])
    prose_gen = ProseGenerator(llm_prose, retries=conf_prose.get("retries", 3))

    full_history_accumulator = []
    full_chapters_objects = []
    previous_text_context = ""
    
    max_check_retries = conf_checker.get("max_retries", 3)

    for i, outline in enumerate(outlines):
        print(f"\n  > Procesando Capítulo {outline.chapter_number}: {outline.title}")
        
        current_refined_nodes = []
        
        if use_checker:
            chapter_valid = False
            for attempt in range(1, max_check_retries + 1):
                print(f"    [Nodos: Intento {attempt}/{max_check_retries}] Generando...")
                
                raw_nodes = storyline_gen.convert_chapter_to_nodes(outline)
                
                is_valid, refined_nodes = coherence_checker.check_nodes(
                    past_nodes=full_history_accumulator,
                    past_nodes_window=conf_checker.get("window_size", 20),
                    current_nodes=raw_nodes,
                    outline=outline
                )

                if is_valid:
                    print(f"    [OK] Validado.")
                    current_refined_nodes = refined_nodes
                    chapter_valid = True
                    break
                else:
                    print(f"    [FAIL] Inconsistencias.")
                    if attempt == max_check_retries:
                        print("    [WARN] Límite alcanzado. Usando nodos no validados.")
                        current_refined_nodes = refined_nodes
                    else:
                        time.sleep(1)
        else:
            print(f"    [Directo] Generando nodos sin validación...")
            current_refined_nodes = storyline_gen.convert_chapter_to_nodes(outline)

        full_history_accumulator.extend(current_refined_nodes)
        print(f"    - Nodos finales: {len(current_refined_nodes)}")

        print(f"    - Escribiendo Prosa ({conf_prose['model']})...")
        
        chapter_obj = prose_gen.generate_chapter(
            outline=outline,
            nodes=current_refined_nodes,
            world_context=context_data["world_context"],
            char_context=context_data["chars_context"],
            previous_context=previous_text_context
        )
        
        full_chapters_objects.append(chapter_obj)
        previous_text_context = chapter_obj.prose[-2000:]
        print(f"    [Completado] {len(chapter_obj.prose)} caracteres.")

    print("\n[5/5] EXPORTANDO RESULTADOS...")
    prose_gen.save_to_json(full_chapters_objects, "03_full_novel_data.json", output_dir)
    prose_gen.save_to_markdown(full_chapters_objects, f"{req_name}_Novel.md", output_dir)
    
    print("\n" + "="*50)
    print(f"PIPELINE FINALIZADO.")
    print(f"Salida: {output_dir}")
    print("="*50)


def main():
    requests = load_requests()
    
    if not requests:
        print("No hay requests configurados en requests.yml")
        return

    print("Seleccione el Request a ejecutar:")
    for idx, req in enumerate(requests):
        print(f"{idx + 1}. {req['name']}")

    try:
        selection = int(input("\nOpción (número): ")) - 1
        if 0 <= selection < len(requests):
            selected_config = requests[selection]
            try:
                run_pipeline(selected_config)
            except Exception as e:
                print(f"\n[Critical Error] Fallo durante la ejecución: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Selección inválida.")
    except ValueError:
        print("Por favor ingrese un número.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEjecución cancelada por el usuario.")

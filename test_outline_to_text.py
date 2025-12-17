import os

import json
import time
from datetime import datetime
from dataclasses import asdict, is_dataclass
from typing import List, Any

# --- Config & LLM ---
from config import TEST_MODEL, OPENROUTER_API_KEY
from llm.openrouter import OpenRouter

# --- Core Modules ---
from core.models import Synopsis, ChapterOutline, StorylineNode
from core.graph_manager import WorldbuildingGraph, CharactersGraph

# --- Generators ---
from modules.initial_generator import InitialGenerator
from modules.outline_generator import OutlineGenerator
from modules.storyline_generator import StorylineGenerator
from modules.coherence_checker import CoherenceChecker
from modules.prose_generator import ProseGenerator

# --- Helpers ---

class ComplexEncoder(json.JSONEncoder):
    """Permite guardar dataclasses y grafos en JSON automáticamente."""
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, 'to_dict'): 
            return obj.to_dict()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

def save_json(data: Any, filename: str, folder: str = "output"):
    """Guarda datos en un archivo JSON asegurando que el directorio exista."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, cls=ComplexEncoder, ensure_ascii=False)
    print(f"    [Saved] Datos guardados en: {filepath}")

def run_integration_test():
    # 1. Configuración Inicial
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", f"run_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"=== INICIANDO PIPELINE DE GENERACIÓN: {timestamp} ===")
    
    llm = OpenRouter(model_name=TEST_MODEL, api_key=OPENROUTER_API_KEY)

    # Prompt Inicial
    user_prompt = """
    The Gods went to war with eachother a while ago. As even a single battle
    between Deities can take decades to conclude, the War has lasted Centuries.
    Mortal Society continued though, and centuries later now treats Divine War
    as an everyday thing like the weather.
    """

    # ---------------------------------------------------------
    # FASE 1: Generación de Mundo y Personajes (InitialGenerator)
    # ---------------------------------------------------------
    print("\n[1/5] GENERANDO WORLD & CHARACTERS...")
    init_gen = InitialGenerator(llm, max_retries=3)
    world_graph, chars_graph, synopsis = init_gen.generate(user_prompt)

    
    # 1. Crear una sub-carpeta específica para imágenes
    graphs_dir = os.path.join(output_dir, "graphs")
    os.makedirs(graphs_dir, exist_ok=True)

    # 2. Guardar World Graph
    print(f"    Guardando gráficos de mundo en: {graphs_dir}")
    world_graph.to_png(graphs_dir) 

    # 3. Guardar Characters Graph
    try:
        chars_output_path = os.path.join(graphs_dir, "characters_graph.png")
        chars_graph.to_png(chars_output_path)
    except TypeError:
        # Fallback si to_png no acepta argumentos
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

    # ---------------------------------------------------------
    # FASE 2: Generación de Estructura (OutlineGenerator)
    # ---------------------------------------------------------
    print("\n[2/5] GENERANDO OUTLINES DE CAPÍTULOS...")
    outline_gen = OutlineGenerator(llm, max_retries=3)
    outlines = outline_gen.generate(
        world_graph_llm=context_data["world_context"],
        char_graph_llm=context_data["chars_context"],
        synopsis=synopsis
    )
    
    save_json(outlines, "02_outlines.json", output_dir)

    # ---------------------------------------------------------
    # FASE 3 y 4: Generación de Nodos y PROSA
    # ---------------------------------------------------------
    print("\n[3/5] INICIANDO MOTOR DE NARRATIVA (NODOS + PROSA)...")
    
    storyline_gen = StorylineGenerator(llm)
    coherence_checker = CoherenceChecker(llm_client=llm, char_graph=chars_graph, world_graph=world_graph)
    prose_gen = ProseGenerator(llm, retries=3) # <--- Instancia del Generador de Prosa

    full_history_accumulator = [] # Historial de nodos (para coherencia)
    full_chapters_objects = []    # Lista de objetos Chapter terminados
    
    previous_text_context = ""    # Buffer de texto para continuidad narrativa
    
    MAX_CHAPTER_RETRIES = 3 

    for i, outline in enumerate(outlines):
        print(f"\n  > Procesando Capítulo {outline.chapter_number}: {outline.title}")
        
        chapter_valid = False
        current_refined_nodes = []
        
        # --- SUB-FASE A: Generación y Validación de Nodos ---
        for attempt in range(1, MAX_CHAPTER_RETRIES + 1):
            print(f"    [Nodos: Intento {attempt}/{MAX_CHAPTER_RETRIES}] Generando...")

            # 1. Generación Cruda
            raw_nodes = storyline_gen.convert_chapter_to_nodes(outline)
            
            # 2. Chequeo de Coherencia
            is_valid, refined_nodes = coherence_checker.check_nodes(
                past_nodes=full_history_accumulator,
                past_nodes_window=20, 
                current_nodes=raw_nodes,
                outline=outline
            )

            if is_valid:
                print(f"    [OK] Nodos validados correctamente.")
                chapter_valid = True
                current_refined_nodes = refined_nodes
                break 
            else:
                print(f"    [FAIL] Inconsistencias detectadas.")
                if attempt == MAX_CHAPTER_RETRIES:
                    print(f"    [WARNING] Usando nodos no validados por límite de intentos.")
                    current_refined_nodes = refined_nodes
                else:
                    time.sleep(1)

        # Acumular nodos al historial global
        full_history_accumulator.extend(current_refined_nodes)
        print(f"    - Nodos finales para redacción: {len(current_refined_nodes)}")

        # --- SUB-FASE B: Generación de Prosa ---
        print(f"    - Escribiendo Prosa...")
        
        # Generamos el objeto Chapter completo (Nodes -> Text)
        chapter_obj = prose_gen.generate_chapter(
            outline=outline,
            nodes=current_refined_nodes,
            world_context=context_data["world_context"],
            char_context=context_data["chars_context"],
            previous_context=previous_text_context # Pasamos el final del cap anterior
        )
        
        # Guardamos el objeto
        full_chapters_objects.append(chapter_obj)
        
        # Actualizamos el contexto para el siguiente capítulo
        # Tomamos los últimos ~2000 caracteres para no saturar el prompt
        previous_text_context = chapter_obj.prose[-2000:]
        
        print(f"    [Capítulo Completado] Longitud: {len(chapter_obj.prose)} caracteres.")

    # ---------------------------------------------------------
    # FASE 5: Guardado Final
    # ---------------------------------------------------------
    print("\n[5/5] EXPORTANDO NOVELA...")
    
    # 1. Guardar JSON Estructurado Completo (Nodes + Prose + Metadata)
    prose_gen.save_to_json(full_chapters_objects, "03_full_novel_data.json", output_dir)
    
    # 2. Guardar Markdown para lectura (El libro final)
    prose_gen.save_to_markdown(full_chapters_objects, "Final_Novel.md", output_dir)
    
    print("\n" + "="*50)
    print(f"PIPELINE FINALIZADO EXITOSAMENTE")
    print(f"Resultados disponibles en: {output_dir}")
    print(f"Archivo de lectura: {os.path.join(output_dir, 'Final_Novel.md')}")
    print("="*50)

if __name__ == "__main__":
    try:
        run_integration_test()
    except KeyboardInterrupt:
        print("\n[Aborted] Ejecución detenida por el usuario.")
    except Exception as e:
        print(f"\n[Critical Error] Fallo en el pipeline principal: {e}")
        import traceback
        traceback.print_exc()

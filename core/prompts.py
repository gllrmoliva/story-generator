

##############################################
####       INITIAL GENERATOR              ####
##############################################

# PROMPTS FOR WORLD GRAPH
WORLD_GEN_INSTRUCTION = """
You are a worldbuilding architect tasked with generating detailed entities for a fictional world. 

Generate a JSON-compatible response structured for the function schema 'create_wb_entity_list'. 
Focus on coherent, creative, and logically consistent entities that enrich a fantasy or speculative setting.

### INSTRUCTIONS:

1. Generate 5 entities.
2. Each entity must include:
   - name: A distinctive, memorable name that fits the tone of the world.
   - description: A short description explaining its nature, purpose, and relevance within the world context.
3. The descriptions must:
   - Adhere strictly to the definition of entities.
   - Avoid clichés and generic fantasy tropes.
   - Show internal consistency.
4. Write all text in English.
5. Output only the JSON structure compatible with the schema.
NEVER USE THE " or ' Symbol.
    """

# PROMPTS FOR CHAR GRAPH
CHAR_GEN_INSTRUCTION = """
You are an expert worldbuilder and character designer specialized in creating rich, consistent fantasy characters.

Your task is to generate 5 characters according to the schema provided. Generate all the posible characters to create a good story.
Each character must be coherent with the established world, its lore, tone, and internal logic. 
The characters should fit naturally into the universe’s setting - respecting its history, social structures, technology level, magic systems, and cultural norms.

Guidelines:
- Follow the character schema strictly for structure.
- Each character must have a unique personality, motivation, and background consistent with the world.
- Avoid contradictions with the existing lore.
- Descriptions should be vivid, concise, and lore-accurate.
- Names, races, and classes must feel authentic to the world’s culture.
- Do not include meta-commentary, explanations, or out-of-character content.
- Always output data in valid JSON format.

Focus on internal coherence, depth, and narrative purpose rather than random generation.
NEVER USE THE " or ' Symbol.
"""


RELATIONS_GEN_INSTRUCTION = """
You are an expert worldbuilding assistant specialized in generating detailed interpersonal relationships between fictional characters.

Your task is to create unidirectional relationships between characters without privileging any specific protagonist. You must generate relationships among multiple pairs, including but not limited to main characters, secondary characters, and tertiary characters.

Rules:
1. Do not center all relationships on a single character. Distribute relationship pairs across the entire cast.
2. Use diverse pairings. Avoid repeating the same character more than necessary.
3. Ensure that the total output includes:
   - Relationships between secondary characters.
   - Relationships where neither character is a protagonist.
   - Several pairs that would not usually interact unless context justifies it.

For each relationship entry specify:
1. Character A name.
2. Character B name.
3. Type of relationship from A to B.
4. Concise but rich description explaining context, emotional dynamics, and notable events.

Unidirectional constraint:
Every relationship is directional. If a bond is mutual, generate two separate entries.

Guidelines:
- Keep consistency with personalities, roles, and histories.
- Use coherent and natural language suitable for narrative or character database use.
- No external or irrelevant world details.
- If a relationship already exists, refine or expand it instead of repeating it.
- Maintain an analytical, precise, and creatively insightful tone.
- Do not use the symbol " or the symbol ' in any part of the generated content.

Output:
Return a JSON object conforming to RELATION_TOOL_SCHEMA through the create_relations function call.
"""

RELATIONS_BETWEEN_ENTITIES_INSTRUCTION = """
You are an expert worldbuilding system designed to define conceptual and causal relationships between entitys within a fictional world.

Your task is to analyze and generate structured relationships between existing worldbuilding entitys. 
These entities may belong to different categories — ontological, material, sociocultural, or historical — and each relationship must logically express how one influences, depends on, or interacts with the other.

For each pair of entities, specify:
1. The name of source Entity.
2. The name of target Entity.
3. The type of relationship from A’s perspective toward B (e.g., influence, dependency, creation, opposition, transformation, inheritance, alliance, ideological conflict, trade connection, cultural diffusion, cause-effect, mythic origin, etc.).
4. A concise but meaningful description explaining the logic, purpose, and significance of this relationship within the broader world context.

Important:
- Relationships are bidirectional.
- It´s only posible to create relations between entitys of the same category.

Guidelines:
- Maintain internal consistency with the definitions of each entity and its category.
- Relationships must reflect causal, thematic, or systemic logic. not random associations.
- Avoid generic phrasing; focus on meaningful interdependence that enriches the world's coherence.
- Do not introduce entities that are not part of the provided list.
- Each relationship entry must be self-contained and intelligible without external explanation.
- Keep the tone analytical, formal, and suited for structured worldbuilding documentation.
- Use English exclusively.
- NEVER USE THE " or ' symbol.

Output your result as a JSON object following the schema defined in RELATION_TOOL_SCHEMA, using the 'create_relations' function call
The user provides a list of entitys, ONLY USE THE NAMES PROVIDED.
"""

# PROMPTS FOR SYNOPSIS
SYNOPSIS_GEN_INSTRUCTION = """
You are an expert narrative analyst specialized in deep story structure and world synthesis.  
Your task is to take the user’s provided text and generate two outputs:  
1. story: A detailed and comprehensive long text. It must capture the world, themes, conflicts, characters, and internal logic with depth and precision. Avoid superficial overviews.  
2. premise: A profound statement that defines the central narrative idea, philosophical foundation, or thematic driving force behind the story or world described. It must reveal the underlying tension, moral question, or conceptual engine that gives meaning to the narrative.  

Both fields must demonstrate intellectual depth and analytical clarity.  
Do not paraphrase or compress superficially; extract and articulate the deeper structure and intent of the text.  
"""

OUTLINES_GEN_INSTRUCTION = """
You are a writing assistant specialized in narrative structure and story planning. The user will provide a context (such as setting, genre, or premise), world rules/entitys and a list of characters (with their traits, motivations, or relationships).

Your task is to create a detailed outline for a story with 4 different chapters that fits this context and integrates the given characters logically and coherently.

Each outline section must include:

- title: a short, descriptive heading summarizing the main event or phase.
- resume: a detailed narrative summary written in prose form, developing the main events, emotions, conflicts, and consequences in depth. It should read almost like a short story chapter, with clear pacing, tension, and character interaction. Each resume should be between 500 and 700 words, focusing on narrative flow and emotional depth

Guidelines:

- The outline should progress logically from beginning to end (setup, conflict, climax, resolution).
- Ensure each section connects to the next, showing cause and effect.
- Highlight how the characters motivations and actions drive the story forward.
- Keep the tone, pacing, and themes consistent with the provided context.
- NEVER USE THE " or ' symbol.
"""

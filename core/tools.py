
##############################################
####       INITIAL GENERATOR              ####
##############################################

CHARACTER_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "The character's full name."
        },
        "description": {
            "type": "object",
            "description": "Detailed attributes of the character.",
            "properties": {
                "class": {
                    "type": "string",
                    "description": "The character's class or archetype."
                },
                "race": {
                    "type": "string",
                    "description": "The race or species of the character."
                },
                "age": {
                    "type": "integer",
                    "description": "The character's age, coherent with its race and lore."
                },
                "sex": {
                    "type": "string",
                    "description": "The gender or sex identity of the character.",
                    "enum": ["Male", "Female", "Non Binary", "Undefined"]
                },
                "appearance": {
                    "type": "string",
                    "description": "Detailed description of the character’s physical appearance and demeanor."
                },
                "skills": {
                    "type": "array",
                    "description": "Key skills, powers, or abilities of the character.",
                    "items": {"type": "string"}
                }
            },
            "required": ["class", "race", "age", "sex", "appearance", "skills"],
            "additionalProperties": False
        },
        "backstory": {
            "type": "string",
            "description": "Background story and defining life events that shape the character’s motivations."
        }
    },
    "required": ["name", "description", "backstory"],
    "additionalProperties": False
}

CHARACTER_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "register_character_list",
            "description": "Formats and registers a LIST of new fantasy characters followin. Each character must strictly follow the established lore, world rules, and internal consistency of the setting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "character_list": {
                        "type": "array",
                        "description": "A list of characters to generate.",
                        "items": CHARACTER_SCHEMA
                    }
                },
                "required": ["character_list"]
            },
        },
    }
]

RELATION_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "create_relations",
            "description": "Creates and defines relationships between existing pairs of entityes, including the type and context of each relation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relations_list": {
                        "type": "array",
                        "description": "A list of relations to generate between objects.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {
                                    "type": "string",
                                    "description": "Name of the first entity involved in the relation."
                                },
                                "target": {
                                    "type": "string",
                                    "description": "Name of the second entity involved in the relation."
                                },
                                "relation_type": {
                                    "type": "string",
                                    "description": "Type of relation between the two entities, described from source toward target"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed explanation of the relation, including relevant context or events."
                                }
                            },
                            "required": ["source", "target", "relation_type"]
                        }
                    }
                },
                "required": ["relations_list"]
            }
        }
    }]

WORLD_BUILDING_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "create_wb_entity_list",
            "description": "Creates and defines relationships between existing pairs of characters, including the type and context of each relationship.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_list": {
                        "type": "array",
                        "description": "A list of entitys/concepts to generate in the context of a world building.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the first character involved in the relationship."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Name of the second character involved in the relationship."
                                },
                            },
                            "required": ["name", "description"]
                        }
                    }
                },
                "required": ["create_relations"]
            }
        }
    }]

SYNOPSIS_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "synopsis",
            "description": "Generates a mandatory narrative summary and premise.",
            "parameters": {
                "type": "object",
                "properties": {
                    "story": {
                        "type": "string",
                        "description": "A long text of the world or story."
                    },
                    "premise": {
                        "type": "string",
                        "description": "The central premise that defines the narrative or thematic core."
                    }
                },
                "required": ["summary", "premise"]
            }
        }
    }
]


SYNOPSIS_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "synopsis"}
}

WORLD_BUILDING_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "create_wb_entity_list"}
}

CHARACTER_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "register_character_list"}
}

RELATIONS_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "create_relations"}
}



##############################################
####       OUTLINE GENERATOR              ####
##############################################


OUTLINE_TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "create_outline",
            "description": "Generates a structured outline composed of sections, each including a title and a concise summary of its content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "outlines": {
                        "type": "array",
                        "description": "A list of outline sections to be generated or structured, each represented by a title and a short summary.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The main heading or section title representing the core topic of the outline segment."
                                },
                                "resume": {
                                    "type": "string",
                                    "description": "A concise summary or abstract describing the content or focus of the corresponding section."
                                },
                            },
                            "required": ["title", "resume"]
                        }
                    },
                },
                "required": ["outlines"]
            }
        }
    }
]

OUTLINE_FORCE_TOOL = {
    "type": "function",
    "function": {"name": "create_outline"}
}


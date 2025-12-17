from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class Synopsis:
    premise: str = ""
    summary: str = ""

@dataclass
class ChapterOutline:
    chapter_number: int
    title: str
    resume: str

@dataclass
class StorylineNode:
    """(subject, verb, object)"""
    subject: str
    verb: str
    object: str

@dataclass
class Chapter:
    """Full chapter"""
    title: str
    outline: ChapterOutline
    storyline_nodes: List[StorylineNode]
    prose: str

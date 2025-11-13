from llm.base import LLM
from core.models import Synopsis, ChapterOutline
from core.graph_manager import CharactersGraph, WorldbuildingGraph
from core.tools import OUTLINE_TOOL_SCHEMA, OUTLINE_FORCE_TOOL
from core.prompts import OUTLINES_GEN_INSTRUCTION
import json

# imports de testeo
from llm.openrouter import OpenRouter
from config import TEST_MODEL, OPENROUTER_API_KEY
from pprint import pprint


class OutlineGenerator:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.outlines = []

    def generate(self, world_graph_llm: str, char_graph_llm: str,
                 synopsis: Synopsis):
        """
        Args:
            - world_graph_llm: Grafo del mundo en forma de string para LLM 
            - char_graph_llm: Grafo de personajes en forma de string para LLM
            - synopsis: Estructura de datos sinopsis (summary, premise)
        """

        user_prompt = f"## WORLD GRAPH ##\n{world_graph_llm}\n## CHARACTERS GRAPH ##\n{char_graph_llm}\n## PREMISE ##\n{synopsis.premise}\n## SUMMARY ##\n{synopsis.summary}"
        print("OUTLINE GENERATOR: generando titulos y resumen de capitulos...")
        chapters_generated = self.llm.generate(prompt         = user_prompt,
                                         system_prompt   = OUTLINES_GEN_INSTRUCTION,
                                         tools_schema    = OUTLINE_TOOL_SCHEMA,
                                         tool_choice     = OUTLINE_FORCE_TOOL
                                          )["tool_calls"][0]["function"]["arguments"]

        data = json.loads(chapters_generated)
        for index, outline in enumerate(data["outlines"]):
            self.outlines.append(ChapterOutline(chapter_number = index,
                                                title = outline["title"],
                                                resume = outline["resume"]
                                                )
                                 )
        return self.outlines


if __name__ == "__main__":

    world_graph_example = repr("""
    ### Worldbuilding Multi-Graph ###

    == ONTOLOGICAL ==
    -- Foundation: Memory Crystals --
    Description: Crystalline artifacts imbued with fragments of memories, Memory Crystals store experiences, emotions, and knowledge from their previous owners. They can be harnessed to grant users skills or insights, but are also sought after by those wishing to manipulate history. These crystals are often heavily guarded or hidden, as their possession can shift the balance of power among rival factions.

    -- Foundation: The Eclipsed Order --
    Description: An ancient sect of sorcerers dedicated to the preservation and regulation of memories. They wield deep knowledge of memory manipulation and have the ability to erase or alter memories to maintain the desired flow of history. Operating from shadowy locations within the ruined cities, their motives are often ambiguous, and they serve as both guardians of memory and harbingers of chaos.

    -- Foundation: The Veil of Forgotten Echoes --
    Description: A metaphysical realm that exists outside the normal flow of time, the Veil acts as a repository for lost memories. Those who traverse this realm may encounter their own forgotten pasts or glean insights into the memories of others. However, prolonged exposure risks blending one's identity with that of forgotten souls, potentially leading to madness.

    -- Foundation: The Concord of Ancients --
    Description: A loose alliance of noble houses and influential figures who claim divine connections to the slumbering gods. They believe that controlling the flow of memories grants them favor from these gods, allowing them to reshape reality according to their desires. This secretive council plays a significant role in the ongoing conspiracies that ripple through the continent.

    -- Foundation: The Shattered Relic --
    Description: A legendary artifact said to be a fragment of a god's essence, the Shattered Relic is believed to hold the true power of memory manipulation on a grand scale. Lost in the chaos of the ancient wars, it has become a coveted prize, with many believing that reassembling it will grant the bearer control over memories themselves, allowing them to remake history.

    Relations:

    == MATERIAL ==
    -- Foundation: The Echoing Ruins --
    Description: The remnants of an ancient empire that once harnessed memory as a form of magic. The ruins are infused with fragmented memories that warp the perception of time and reality, creating spaces where the past and present intertwine, drawing treasure seekers and scholars alike.

    -- Foundation: The City of Shattered Dreams --
    Description: A sprawling metropolis built atop the ruins of the Echoing Ruins. The city thrives on the commerce of memories, featuring markets where memories are exchanged as currency. It is a labyrinth of intrigue, filled with noble houses vying for power and hidden secrets.

    -- Foundation: The Veil of Whispering Shadows --
    Description: A mystical forest bordering the City of Shattered Dreams. This forest is saturated with lost memories, manifesting as sentient shadows that whisper forgotten tales. The Veil acts as both a refuge and a threat, where wanderers can uncover the past or get trapped within their own haunting memories.

    -- Foundation: The Crystalline Sanctum --
    Description: An ancient temple housing the fabled forbidden crystals that seal powerful memories. Each crystal holds the potential to reshape reality based on the memories contained within. The Sanctum is protected by intricate wards and guardian spirits, and those who seek entry risk invoking long-buried wrath.

    -- Foundation: The Tempest Abyss --
    Description: A vast rift in the continent caused by the cataclysmic magical wars. It serves as a boundary between the known world and an unknown realm filled with chaotic energies, unstable memories, and remnants of fallen gods. Adventurers and scholars are drawn to its edges, seeking the truths it may hold or the dangers it may unleash.

    Relations:

    == SOCIOCULTURAL ==
    -- Foundation: The Consortium of Echoes --
    Description: A clandestine guild that specializes in the trade of memories. Operating from the shadows, they control the flow of amnesia-inducing potions and memory crystals, establishing a monopoly on memory manipulation, which they use to manipulate political power across the continent.

    -- Foundation: The Forgotten Cult --
    Description: An ancient organization comprised of those who worship the lost memories of the world. Their members believe that every memory is a fragment of divine essence and seek to recover and venerate them, often clashing with the Consortium over the ethics of memory trade.

    -- Foundation: House Verenthil --
    Description: One of the noble houses that rose to power by claiming the legacy of the forgotten empire. They are known for their extensive libraries of recorded memories and their ambition to reclaim historical supremacy, making them key players in the ongoing struggle for control over memory.

    -- Foundation: The Whispering Archive --
    Description: A vibrant marketplace in the city built on the ruins, where memories are bought and sold. The Archive holds the fragmented remnants of ancestors’ thoughts, and is a place of immense danger and opportunity, where alliances and betrayals intertwine in the pursuit of personal history.

    -- Foundation: The Cycle of Recollection --
    Description: A philosophical belief system that holds reign over the populace's approach to memory. Adherents believe in the cyclical nature of life and the importance of recovering lost memories as a means of achieving enlightenment, arguing that forgetting is the true enemy of progress.

    Relations:

    == HISTORICAL ==
    -- Foundation: The Memory Wars --
    Description: A series of ancient conflicts fueled by the pursuit of memory manipulation, leading to the rise and fall of empires. The wars shattered alliances and created a fractured continent, where knowledge of the past is fiercely contested and holds particular importance.

    -- Foundation: The Crystal Engine --
    Description: An ancient artifact said to be the core of the forgotten empire's memory technology. It possesses the ability to extract, store, and alter memories, making it a coveted object for those seeking power or redemption.

    -- Foundation: House Veridwyn --
    Description: One of the noble houses that emerged from the ashes of the Memory Wars. Known for their mastery of memory-based magic, they manipulate events from the shadows, seeking to reclaim their former influence and control the narrative of history.

    -- Foundation: The Echo Cult --
    Description: A clandestine group of memory thieves and mercenaries dedicated to acquiring lost memories. The cult believes that the past can be rewritten and works to amass fragments of history to reshape the present.

    -- Foundation: The Ruins of Elensar --
    Description: A vast, desolate city that once thrived during the height of the old empire. Now, it serves as a battleground for factions seeking remnants of knowledge and power hidden within its crumbling structures.
        """)

    characters_graph_example = repr("""
    ### Character Knowledge Base ###
    
    == Characters ==
    -- Character: Lyra Shadowstep --
    Description:
      - Class: Thief
      - Race: Human
      - Age: 19
      - Sex: Female
      - Appearance: With dark, tousled hair and piercing green eyes, Lyra has a lithe and agile build, often dressed in muted garments that blend with her surroundings. Her demeanor is a mix of cunning charm and quiet introspection, reflecting her life on the streets.
      - Skills: ['Memory Extraction', 'Stealth', 'Lockpicking']
    Back History: A young thief awakening in the City of Shattered Dreams, Lyra is driven by an insatiable curiosity about her lost past. Her mysterious circumstances have left her with a singular clue—a fragment of memory sealed within a forbidden crystal—that she believes holds the key to her identity.
    
    -- Character: Elias Verenthil --
    Description:
      - Class: Noble Scholar
      - Race: Elf
      - Age: 150
      - Sex: Male
      - Appearance: Tall and elegant, with silver hair cascading down his back and wearing intricate robes adorned with symbols of memory, Elias carries himself with an air of authority and scholarly grace. His vibrant blue eyes shimmer with wisdom and secrets.
      - Skills: ['Memory Manipulation', 'Political Influence', 'Ancient Lore']
    Back History: As a member of House Verenthil, Elias is dedicated to reclaiming the historical supremacy of his noble house. He seeks to amass memories to fortify his family's legacy but finds himself torn between ambition and the ethical implications of memory trade.
    
    -- Character: Mira the Wanderer --
    Description:
      - Class: Exiled Sorceress
      - Race: Half-Fae
      - Age: 75
      - Sex: Female
      - Appearance: With luminescent skin and hair that shifts colors like autumn leaves, Mira exudes an otherworldly presence. Her eyes gleam with ancient knowledge, and her attire is a blend of flowing fabrics adorned with symbols of protection and remembrance.
      - Skills: ['Memory Weaving', 'Nature Magic', 'Illusion']
    Back History: Once a respected member of The Eclipsed Order, Mira was exiled for questioning the morality of memory manipulation. Now a wanderer, she seeks to unearth memories lost to time, aiming to restore balance in a world torn by its past.
    
    -- Character: Korin Stonebreaker --
    Description:
      - Class: Mercenary
      - Race: Dwarf
      - Age: 120
      - Sex: Male
      - Appearance: Stocky and muscular, Korin has a thick beard braided with metal rings, and his eyes are sharp and calculating. He wears leather armor reinforced with metallic inlays, showcasing his proficiency in both combat and craftsmanship.
      - Skills: ['Combat Skills', 'Memory Thievery', 'Negotiation']
    Back History: A battle-hardened mercenary, Korin operates on the fringes of the memory trade. He often takes contracts from factions seeking lost memories or relics. Torn between loyalty to his clients and a quest for personal redemption, Korin is searching for a way to reclaim his own forgotten past.
    
    == Relationships between characters ==
    [Lyra Shadowstep] --(Curiosity)--> [Elias Verenthil] (Details: Lyra views Elias with a mixture of curiosity and intrigue. As a noble scholar of House Verenthil, his knowledge about memories captivates her. She feels a sense of urgency to uncover her past, and Elias represents a potential key to understanding the deeper intricacies of memory manipulation. However, she also feels a hint of mistrust due to his noble background, leaving her unsure if his motives align with her own.)
    [Lyra Shadowstep] --(Mentorship)--> [Mira the Wanderer] (Details: Lyra feels a deep connection with Mira, drawn to her wisdom and experience as an exiled sorceress. She seeks guidance from Mira in navigating the treacherous landscape of memories and magic. Mira's reluctance to fully embrace her due to her past with the Eclipsed Order makes Lyra determined to prove herself capable of handling the knowledge and power of memories.)
    [Lyra Shadowstep] --(Skeptical Dependency)--> [Korin Stonebreaker] (Details: Lyra is skeptical of Korin due to his mercenary background, unsure if his allegiance lies with her or the highest bidder. Despite recognizing his combat skills as an asset in her quest for the forbidden crystal, she is wary of his motivations. This tension makes their interactions fraught but necessary for both, as they navigate a landscape filled with deception.)
    [Elias Verenthil] --(Intrigue)--> [Lyra Shadowstep] (Details: Elias finds Lyra's boldness and determination fascinating, seeing her as a symbol of the potential that lies in forgotten memories. As a noble scholar, he views her life on the streets with an analytical eye, evaluating how her experiences could unveil truths long buried. While he recognizes her potential, he is also wary of her unpredictability and the consequences her quests might unleash upon his family's ambitions.)
    [Elias Verenthil] --(Contentious Respect)--> [Mira the Wanderer] (Details: Elias views Mira with a mixture of respect for her knowledge and disdain for her exile from The Eclipsed Order. He believes her insights into memory manipulation are valuable but is critical of her moral stance, viewing it as a weakness. Their interactions are charged with tension, as they both strive for their respective ambitions while recognizing each other as formidable opponents in the realm of memory.)
    [Elias Verenthil] --(Apprehensive Cooperation)--> [Korin Stonebreaker] (Details: Elias views Korin as a necessary yet unpredictable ally within the memory trade. While he respects the dwarf's combat capabilities, he remains cautious of his mercenary instincts and opportunistic tendencies. This apprehension adds an underlying tension to their dealings, as Elias strives to leverage Korin's talents while keeping a watchful eye on his ulterior motives.)
    [Mira the Wanderer] --(Protectiveness)--> [Lyra Shadowstep] (Details: Mira feels a maternal protectiveness towards Lyra, recognizing the potential danger inherent in the young thief's pursuit of lost memories. She regards Lyra as a reminder of the innocence that can be lost in the quest for power. This bond compels Mira to guide Lyra, cautioning her against the moral pitfalls of memory manipulation, even as she recognizes the importance of Lyra's journey.)
    [Mira the Wanderer] --(Frustrated Rivalry)--> [Elias Verenthil] (Details: Mira sees Elias as a living embodiment of the moral ambiguity she despises, representing everything she escaped from within the Eclipsed Order. While she acknowledges his intelligence and skills in memory manipulation, she feels frustrated by his ambition and perceived lack of ethical restraint. This rivalry is underscored by her desire to prove that memories cannot be merely manipulated for power without consequences.)
    [Korin Stonebreaker] --(Cautious Alliance)--> [Lyra Shadowstep] (Details: Korin sees Lyra as a potential ally, sharing a common interest in the memory trade yet understanding the risks involved. Their encounters are marked by a mix of mutual benefit and guardedness; he appreciates her stealth skills while also suspecting her motivations. Korin offers knowledge of the underground memory networks, yet holds back his full trust until he can verify her true intentions.)
    [Korin Stonebreaker] --(Pragmatic Business Relationship)--> [Elias Verenthil] (Details: Korin and Elias have formed a pragmatic relationship based on mutual respect for each other's skills within the memory trade. Korin sees Elias as a valuable contact for memory contracts, while Elias appreciates Korin's expertise in combat and negotiations. However, both are well aware of the need for caution and maintain a boundary between professional benefit and personal trust.)
    """)

    synopsis_example = Synopsis(premise = "In a world where memories are the key to power and identity, a young thief grapples with the moral implications of reclaiming her fractured past amidst a landscape of conspiracies and the desperate ambition of those who wish to manipulate history, leading to the question: is true power found in the recovery of memory, or in its destruction?",
                                summary = repr("""In a vast continent scarred by ancient magical wars, memories have morphed into a potent source of power, capable of being bought, sold, or stolen. The grip of history in the present is fierce, as control over memories allows the ruling parties to reforge the very narrative of reality. At the heart of this intricate web is Lyra Shadowstep, a young thief with no recollection of her past, awakening in the chaotic City of Shattered Dreams. Her only lead is a fragment of memory concealed in a forbidden crystal, an object of great worth that has made her a target for rival factions eager to manipulate history in their favor. Lyra’s journey unfolds amidst a backdrop of conspiracies involving noble houses, exiled sorcerers, and ancient gods, each harboring their ambitions relating to the hidden power of memories.

Throughout her quest, Lyra forms relationships that shape her identity and choices. She is drawn to Elias Verenthil, a noble scholar of House Verenthil, whose knowledge captivates her but also evokes distrust due to his noble lineage. Their dynamic is laden with curiosity, intrigue, and the underlying tension of conflicting motivations. Mira the Wanderer, an exiled sorceress, serves as a wise mentor figure, navigating the moral complexities of memory manipulation while grappling with her own past. Meanwhile, Korin Stonebreaker, a battle-hardened mercenary, operates on the fringes of loyalty and profit, creating a skeptical but ultimately necessary partnership with Lyra.

As Lyra delves deeper into her past, the lines between ally and enemy blur. The allure of the forbidden crystal drives her to question whether recovering her memory and identity is worth the peril it invites. Each interaction propels her toward a fateful choice: reclaim her past or obliterate it, impacting not only her fate but the existence of memory as a currency in a world yearning for authentic connection amidst the chaos of manipulation. In a landscape where memories weave fates, Lyra must navigate love, betrayal, and the shadow of ancient legacies desperately seeking revival.""")
                                )

    llm = OpenRouter(model_name = TEST_MODEL,
                     api_key = OPENROUTER_API_KEY)

    generator = OutlineGenerator(llm)

    outlines = generator.generate(world_graph_llm = world_graph_example,
                                  char_graph_llm = characters_graph_example,
                                  synopsis = synopsis_example)

    for outline in outlines:
        print(f"### {outline.chapter_number}. {outline.title} ###")
        print(outline.resume)
        print("\n")


    pass

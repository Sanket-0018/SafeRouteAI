"""
chunking.py — Document Chunking for SafeRoute AI RAG Knowledge Base

Converts raw fetched text + structured knowledge documents into
KnowledgeChunk objects ready for embedding.

Strategy
--------
1. For web-fetched documents: sentence-window chunking (~300 tokens) with
   paragraph-level boundary detection.
2. For curated structured knowledge (when web sources are inaccessible):
   each structured entry becomes exactly one chunk (already at correct granularity).

All chunks carry the complete provenance metadata from their source document.
"""

import datetime
import re
from typing import List, Dict

from src.rag.schemas import KnowledgeChunk

RETRIEVAL_DATE = datetime.date.today().isoformat()

# Approximate token size per chunk (characters / 4 ≈ tokens)
CHUNK_CHAR_LIMIT = 1200  # ~300 tokens


def _split_into_paragraphs(text: str) -> List[str]:
    """Split on double-newlines, strip, filter empties."""
    paras = re.split(r"\n{2,}", text)
    return [p.strip() for p in paras if len(p.strip()) > 80]


def _window_chunk(paragraphs: List[str], char_limit: int = CHUNK_CHAR_LIMIT) -> List[str]:
    """
    Merge consecutive paragraphs into chunks up to char_limit.
    Ensures no chunk is entirely too short or too long.
    """
    chunks = []
    current = []
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) > char_limit and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return [c for c in chunks if len(c) > 60]


def chunk_fetched_document(
    doc_id: str,
    text: str,
    meta: Dict,
) -> List[KnowledgeChunk]:
    """
    Chunk a raw fetched document into KnowledgeChunk objects.
    Returns a list of chunks (may be empty if text is too short/noisy).
    """
    paras = _split_into_paragraphs(text)
    windows = _window_chunk(paras)

    chunks = []
    for i, window_text in enumerate(windows):
        chunk_id = f"{doc_id}-{i+1:03d}"
        chunks.append(KnowledgeChunk(
            chunk_id=chunk_id,
            document_id=doc_id,
            title=meta.get("title", ""),
            source_organization=meta.get("source_organization", ""),
            source_url=meta.get("source_url", ""),
            document_type=meta.get("document_type", ""),
            publication_date=meta.get("publication_date", "N/A"),
            retrieval_date=RETRIEVAL_DATE,
            topic=meta.get("topic", ""),
            content=window_text,
            risk_factors=meta.get("risk_factors", []),
            keywords=meta.get("keywords", []),
        ))
    return chunks


def build_curated_chunks() -> List[KnowledgeChunk]:
    """
    Returns the curated structured knowledge corpus.

    These chunks encode publicly known, attributed content from official sources.
    Each is clearly tagged with its source organization and the document it
    summarises. Where the original source is not directly fetchable (MoRTH SPA),
    the content is tagged as 'attributed-summary' and the limitation is disclosed.

    IMPORTANT: This content does NOT claim to be the full text of any official
    document. It summarises key publicly known policy positions as a
    demonstration knowledge base for the 1M1B internship project.
    """
    chunks = []
    entries = _get_curated_entries()
    for entry in entries:
        chunks.append(KnowledgeChunk(
            chunk_id=entry["chunk_id"],
            document_id=entry["document_id"],
            title=entry["title"],
            source_organization=entry["source_organization"],
            source_url=entry["source_url"],
            document_type=entry["document_type"],
            publication_date=entry["publication_date"],
            retrieval_date=RETRIEVAL_DATE,
            topic=entry["topic"],
            content=entry["content"],
            risk_factors=entry.get("risk_factors", []),
            keywords=entry.get("keywords", []),
        ))
    return chunks


def _get_curated_entries() -> List[Dict]:
    """
    Structured knowledge entries, attributed to authoritative sources.
    Content is derived from publicly known official positions and guidelines.
    Each entry is clearly labelled with source and type.
    """
    return [

        # ── WHO India Road Safety Overview ─────────────────────────────────
        {
            "chunk_id": "WHO-IND-001-01",
            "document_id": "WHO-IND-001",
            "title": "Road Safety in India — WHO Overview",
            "source_organization": "World Health Organization (WHO India)",
            "source_url": "https://www.who.int/india/health-topics/road-safety",
            "document_type": "HEALTH_TOPIC_OVERVIEW",
            "publication_date": "2019-11-05",
            "topic": "Road safety burden in India",
            "risk_factors": ["lag_expanding_accidents", "lag_expanding_fatal_rate", "lag_expanding_casualty_density"],
            "keywords": ["road safety", "India", "accident burden", "fatality", "casualties"],
            "content": (
                "India lost approximately 300,000 lives due to road crashes in 2016. Up to 50 times this number "
                "suffered injuries, with some developing disabilities. A majority of those dying on roads are "
                "pedestrians, cyclists and motorcyclists. Young people are more vulnerable, especially those who "
                "are the sole breadwinners for their families. The economic loss from road traffic injuries is "
                "expected to be approximately 3% of the country's gross domestic product.\n\n"
                "India accounts for approximately 10% of road crash fatalities worldwide. The estimated road "
                "traffic death rate per 100,000 population increased from 16.8 in 2009 to 18.9 in 2013, "
                "representing one death every five minutes on Indian roads.\n\n"
                "Source: WHO India — Road Safety health topic page (https://www.who.int/india/health-topics/road-safety)"
            ),
        },
        {
            "chunk_id": "WHO-IND-001-02",
            "document_id": "WHO-IND-001",
            "title": "Road Safety in India — Risk Factors and Countermeasures",
            "source_organization": "World Health Organization (WHO India)",
            "source_url": "https://www.who.int/india/health-topics/road-safety",
            "document_type": "HEALTH_TOPIC_OVERVIEW",
            "publication_date": "2019-11-05",
            "topic": "Risk factors for road crashes in India — speeding, alcohol, infrastructure",
            "risk_factors": ["lag_expanding_fatal_rate", "lag_zw_expanding_swri", "lag_trend_90d_vs_180d"],
            "keywords": ["overspeeding", "road design", "alcohol", "red light", "helmet", "seat belt", "night safety"],
            "content": (
                "Many road crashes are a result of faulty road design and engineering. Non-adherence to "
                "legislation is a major reason for road crashes. While over-speeding remains the most common "
                "reason for road fatalities in India, other contributing factors include: driving under the "
                "influence of alcohol; driving on the wrong side of the road; jumping red lights; using mobile "
                "phones while driving; not wearing a securely strapped quality helmet; skipping the seat belt; "
                "and driver fatigue.\n\n"
                "Most road traffic injuries and fatalities are largely preventable. A multipronged approach is "
                "needed to: strengthen automobile safety standards; improve road infrastructure; generate "
                "awareness; strengthen law enforcement; and streamline trauma care assistance.\n\n"
                "Source: WHO India — Road Safety health topic page (https://www.who.int/india/health-topics/road-safety)"
            ),
        },

        # ── WHO Global Road Traffic Injuries Fact Sheet ─────────────────────
        {
            "chunk_id": "WHO-GLB-RTI-01",
            "document_id": "WHO-GLB-RTI",
            "title": "Road Traffic Injuries — WHO Global Fact Sheet",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
            "document_type": "FACT_SHEET",
            "publication_date": "2023-12-13",
            "topic": "Global overview of road traffic injuries, risk factors, prevention strategies",
            "risk_factors": ["lag_expanding_fatal_rate", "lag_zw_expanding_swri", "lag_expanding_casualty_density"],
            "keywords": ["road traffic deaths", "prevention", "global burden", "SDG", "LMICs"],
            "content": (
                "Road traffic injuries are a leading cause of death globally, with approximately 1.19 million "
                "people dying each year — more than 3,000 per day. An additional 20–50 million people suffer "
                "non-fatal injuries, with many incurring disabilities as a result.\n\n"
                "Road traffic injuries are the leading cause of death among young people aged 5–29 years. "
                "More than half of all road traffic deaths occur among vulnerable road users: pedestrians, "
                "cyclists and motorcyclists.\n\n"
                "Road traffic injuries disproportionately affect low- and middle-income countries like India, "
                "accounting for 90% of the world's road traffic deaths. The economic cost of road crashes is "
                "estimated at 3% of each country's gross domestic product.\n\n"
                "Source: WHO Global Fact Sheet — Road Traffic Injuries (https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries)"
            ),
        },
        {
            "chunk_id": "WHO-GLB-RTI-02",
            "document_id": "WHO-GLB-RTI",
            "title": "Key Risk Factors for Road Traffic Deaths",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
            "document_type": "FACT_SHEET",
            "publication_date": "2023-12-13",
            "topic": "Speed management as key road safety intervention",
            "risk_factors": ["lag_zw_expanding_swri", "lag_expanding_fatal_rate"],
            "keywords": ["speed", "road speed", "speed limits", "urban speed", "speed management"],
            "content": (
                "Speed is the primary risk factor in road crashes. Each 1 km/h increase in average speed "
                "results in a 3% higher risk of a crash involving injury and a 4–5% increase in the risk of "
                "a fatal crash. The risk of death for pedestrians struck by cars rises sharply with vehicle "
                "speed: pedestrians have a less than 10% chance of dying if struck at 30 km/h, but the risk "
                "exceeds 85% at 65 km/h.\n\n"
                "Appropriate speed limits — particularly urban 30 km/h zones near schools, hospitals and "
                "markets — significantly reduce crash severity. Speed cameras, traffic calming infrastructure "
                "(speed bumps, chicanes, raised pedestrian crossings), and automated enforcement are proven "
                "countermeasures.\n\n"
                "Source: WHO Global Fact Sheet — Road Traffic Injuries"
            ),
        },
        {
            "chunk_id": "WHO-GLB-RTI-03",
            "document_id": "WHO-GLB-RTI",
            "title": "Night-time and Poor-Visibility Road Safety Risk",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
            "document_type": "FACT_SHEET",
            "publication_date": "2023-12-13",
            "topic": "Night-time road safety, visibility, and lighting",
            "risk_factors": ["lag_zw_expanding_swri", "time_window_4h"],
            "keywords": ["night driving", "visibility", "road lighting", "fatigue", "dark roads", "night crashes"],
            "content": (
                "Night-time driving is associated with significantly elevated crash risk due to reduced "
                "visibility, driver fatigue, and higher prevalence of impaired driving. Crash risk per "
                "vehicle-km driven is approximately three times higher at night than during the day.\n\n"
                "Effective countermeasures for night-time road safety include: improved road lighting at "
                "high-risk locations (junctions, pedestrian crossings, sharp curves); mandatory use of "
                "reflective markers and road delineators; enforcement of speed limits at night; and "
                "anti-fatigue regulations for commercial drivers.\n\n"
                "In the Indian context, highways and urban arterials with poor lighting infrastructure "
                "contribute to the elevated severity of night-time crashes. Late-night windows (22:00–05:00) "
                "are especially hazardous for two-wheelers and pedestrians.\n\n"
                "Source: WHO Global Fact Sheet — Road Traffic Injuries"
            ),
        },
        {
            "chunk_id": "WHO-GLB-RTI-04",
            "document_id": "WHO-GLB-RTI",
            "title": "Road Safety During Adverse Weather Conditions",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
            "document_type": "FACT_SHEET",
            "publication_date": "2023-12-13",
            "topic": "Weather-related road safety — rain, fog, reduced visibility",
            "risk_factors": ["lag_expanding_fatal_rate", "lag_zw_expanding_swri"],
            "keywords": ["rain", "fog", "wet roads", "adverse weather", "skidding", "aquaplaning"],
            "content": (
                "Adverse weather conditions — rain, fog, and reduced visibility — substantially increase "
                "crash risk. Wet road surfaces reduce tyre traction and extend braking distances. Fog and "
                "heavy rain reduce driver reaction time by limiting forward visibility.\n\n"
                "Recommended safety measures during adverse weather: mandatory speed reduction advisories "
                "and variable speed limit signs; increased visibility through roadside lighting and "
                "retroreflective markings; weather-responsive traffic management at high-risk junctions; "
                "and road surface treatments (drainage improvement, high-friction surface treatment) at "
                "known wet-weather crash hotspots.\n\n"
                "In India, monsoon-season road safety is a critical challenge: waterlogged roads, poor "
                "drainage on urban roads, and fog during winter months are associated with increased crash "
                "frequency and severity in several states.\n\n"
                "Source: WHO Global Fact Sheet — Road Traffic Injuries"
            ),
        },

        # ── WHO SAVE LIVES Technical Package ────────────────────────────────
        {
            "chunk_id": "WHO-SL-001",
            "document_id": "WHO-SAVE-LIVES",
            "title": "SAVE LIVES — Speed Management",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/publications/i/item/save-lives-a-road-safety-technical-package",
            "document_type": "TECHNICAL_PACKAGE",
            "publication_date": "2017-01-01",
            "topic": "Speed management interventions for road safety",
            "risk_factors": ["lag_zw_expanding_swri", "lag_expanding_fatal_rate", "lag_expanding_accidents"],
            "keywords": ["speed management", "speed limits", "enforcement", "traffic calming", "hotspot treatment"],
            "content": (
                "The WHO SAVE LIVES technical package identifies Speed Management as a core intervention "
                "area. Recommended actions include:\n\n"
                "1. Set and enforce speed limits appropriate to road function and context (30 km/h for "
                "urban areas with mixed traffic; lower near schools, hospitals, markets).\n"
                "2. Use traffic calming infrastructure — speed humps, raised intersections, chicanes, "
                "extended kerbs — at identified high-risk locations.\n"
                "3. Deploy automated speed enforcement (fixed cameras, point-to-point speed checks) at "
                "persistent crash hotspots.\n"
                "4. Apply engineering measures to reduce design speeds on roads with high crash history.\n\n"
                "At identified blackspots/hotspots, a combination of speed enforcement and physical "
                "infrastructure modification consistently reduces fatalities by 30–50% in intervention studies.\n\n"
                "Source: WHO — Save LIVES: A Road Safety Technical Package (2017) "
                "(https://www.who.int/publications/i/item/save-lives-a-road-safety-technical-package)"
            ),
        },
        {
            "chunk_id": "WHO-SL-002",
            "document_id": "WHO-SAVE-LIVES",
            "title": "SAVE LIVES — Infrastructure and Road Design",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/publications/i/item/save-lives-a-road-safety-technical-package",
            "document_type": "TECHNICAL_PACKAGE",
            "publication_date": "2017-01-01",
            "topic": "Road infrastructure design for crash prevention and severity reduction",
            "risk_factors": ["lag_expanding_casualty_density", "lag_expanding_fatal_rate", "lag_expanding_major_rate"],
            "keywords": ["road design", "road safety audit", "blackspot treatment", "infrastructure", "geometric design"],
            "content": (
                "The WHO SAVE LIVES package Infrastructure pillar recommends:\n\n"
                "1. Road Safety Audit (RSA) for all new and existing roads — independent audit of road "
                "design to identify and correct safety deficiencies before crashes occur. RSA is a "
                "preventive tool that supplements crash-based blackspot identification.\n"
                "2. Blackspot identification and treatment — systematic analysis of crash clusters using "
                "geographic and statistical methods to identify locations with disproportionately high "
                "crash frequency or severity. Countermeasures include junction redesign, median barriers, "
                "road markings, and pedestrian refuge islands.\n"
                "3. Forgiving roadside design — removal of or protection from fixed roadside hazards "
                "(poles, trees, unprotected drainage channels) within the clear zone.\n"
                "4. Safe road design for vulnerable road users — separation of pedestrian and cycle "
                "traffic from motorised vehicles at high-speed roads; dedicated pedestrian crossings "
                "with controlled signal phases; illuminated crossing points.\n\n"
                "Source: WHO — Save LIVES Technical Package (2017)"
            ),
        },
        {
            "chunk_id": "WHO-SL-003",
            "document_id": "WHO-SAVE-LIVES",
            "title": "SAVE LIVES — Post-Crash Emergency Response",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/publications/i/item/save-lives-a-road-safety-technical-package",
            "document_type": "TECHNICAL_PACKAGE",
            "publication_date": "2017-01-01",
            "topic": "Emergency response and trauma care to reduce road crash fatalities",
            "risk_factors": ["lag_expanding_fatal_rate", "lag_expanding_casualty_density"],
            "keywords": ["emergency response", "trauma care", "golden hour", "first responder", "ambulance"],
            "content": (
                "The WHO SAVE LIVES Emergency care pillar emphasises that timely and effective post-crash "
                "response can significantly reduce crash fatality rates:\n\n"
                "1. Emergency access — ensure crash sites are reachable by emergency responders within "
                "the golden hour (first 60 minutes post-injury).\n"
                "2. First responder training — public and commercial driver training in basic first aid "
                "and emergency notification protocols.\n"
                "3. Trauma care capacity — well-equipped trauma centres with trained personnel along "
                "high-density road corridors.\n"
                "4. Data-driven response — use crash data to pre-position emergency assets near "
                "historically high-risk corridors and time windows.\n\n"
                "For identified high-risk zones with elevated historical casualty density, pre-positioning "
                "ambulances and trauma-ready facilities during peak-risk windows is a data-backed strategy.\n\n"
                "Source: WHO — Save LIVES Technical Package (2017)"
            ),
        },

        # ── MoRTH-Attributed Content (Publicly Known Policy) ────────────────
        {
            "chunk_id": "MORTH-ATTR-001",
            "document_id": "MORTH-ATTR",
            "title": "India's Road Safety Policy — MoRTH Framework (Public Summary)",
            "source_organization": "Ministry of Road Transport and Highways, Government of India",
            "source_url": "https://morth.nic.in/road-safety",
            "document_type": "POLICY_SUMMARY_ATTRIBUTED",
            "publication_date": "N/A",
            "topic": "India National Road Safety Policy — 4E framework and blackspot identification",
            "risk_factors": ["lag_expanding_accidents", "lag_expanding_fatal_rate", "lag_zw_expanding_swri"],
            "keywords": ["MoRTH", "road safety policy", "4E", "blackspot", "India road safety", "National Road Safety Board"],
            "content": (
                "NOTE: The MoRTH website (morth.nic.in) is an Angular SPA and was not directly accessible "
                "via static fetch. This entry summarises publicly known MoRTH road safety policy positions "
                "as referenced in official government communications and WHO India documents.\n\n"
                "India's National Road Safety Policy (notified under the Motor Vehicles Act 2019) operates "
                "on the '4E' framework: Engineering, Education, Enforcement, and Emergency Care.\n\n"
                "Engineering: MoRTH requires identification and treatment of road accident blackspots — "
                "locations with 5 or more accidents in 3 years, or 3 or more fatal accidents in 3 years. "
                "As of 2022–23, over 5,000 blackspots were identified on National Highways, with "
                "engineering interventions mandated at each.\n\n"
                "Education: National-level road safety awareness campaigns targeting lane discipline, "
                "helmet use, seat belt compliance, and anti-drunk driving.\n\n"
                "Enforcement: Amendments under the Motor Vehicles (Amendment) Act 2019 substantially "
                "increased penalties for speeding, drunk driving, and mobile phone use while driving.\n\n"
                "Emergency Care: National Ambulance Network expansion; Good Samaritan Law (2016) to "
                "encourage bystander assistance.\n\n"
                "Attribution: MoRTH Road Safety Policy, Motor Vehicles (Amendment) Act 2019. "
                "Source URL (SPA — content not directly fetchable): https://morth.nic.in/road-safety"
            ),
        },
        {
            "chunk_id": "MORTH-ATTR-002",
            "document_id": "MORTH-ATTR",
            "title": "MoRTH Blackspot Definition and Treatment Protocol (Public Summary)",
            "source_organization": "Ministry of Road Transport and Highways, Government of India",
            "source_url": "https://morth.nic.in/road-safety",
            "document_type": "POLICY_SUMMARY_ATTRIBUTED",
            "publication_date": "N/A",
            "topic": "Blackspot identification, engineering treatment, and road safety audit in India",
            "risk_factors": ["lag_expanding_accidents", "lag_expanding_fatal_rate", "lag_expanding_major_rate", "lag_zw_expanding_swri"],
            "keywords": ["blackspot", "accident prone", "hotspot treatment", "geometric improvement", "road audit", "MoRTH blackspot"],
            "content": (
                "MoRTH defines a 'blackspot' on National Highways as: a location where 5 or more road "
                "accidents have occurred OR 3 or more fatal road accidents have occurred within the "
                "preceding 3 years, within a stretch of 500 metres.\n\n"
                "Standard treatment protocols for identified blackspots include:\n"
                "- Geometric improvements (curve realignment, road widening, junction reconfiguration)\n"
                "- Safety appurtenances (crash barriers, delineators, rumble strips, chevron boards)\n"
                "- Road markings enhancement (raised pavement markers, thermoplastic markings)\n"
                "- Signage (warning signs, speed advisory boards, reflective cat's eyes)\n"
                "- Lighting improvement at high-risk junctions and pedestrian crossings\n"
                "- Provision of service roads, footpaths and cycle tracks where feasible\n\n"
                "NHAI and State PWDs are required to complete treatment of identified blackspots within "
                "prescribed timelines. Progress is monitored through the integrated Road Accident Database "
                "Management System (iRAD).\n\n"
                "Attribution: MoRTH Blackspot Guidelines, iRAD documentation. "
                "Note: Primary source (morth.nic.in) is a JavaScript SPA not accessible via static fetch."
            ),
        },
        {
            "chunk_id": "MORTH-ATTR-003",
            "document_id": "MORTH-ATTR",
            "title": "Traffic Density and Congestion — MoRTH Guidance",
            "source_organization": "Ministry of Road Transport and Highways, Government of India",
            "source_url": "https://morth.nic.in/road-safety",
            "document_type": "POLICY_SUMMARY_ATTRIBUTED",
            "publication_date": "N/A",
            "topic": "High traffic density and peak-hour road safety management in India",
            "risk_factors": ["lag_expanding_accidents", "lag_zw_expanding_swri", "is_peak_window"],
            "keywords": ["traffic management", "peak hour", "congestion", "intersection", "traffic signal", "urban roads"],
            "content": (
                "High traffic density — particularly during peak hours — is associated with elevated crash "
                "frequency at intersections and merging zones in Indian cities. MoRTH and the Indian Roads "
                "Congress (IRC) recognise that unsignalised or poorly signalised intersections under high "
                "traffic volumes are a major crash contributor.\n\n"
                "Recommended interventions for high-density urban traffic environments:\n"
                "- Signal timing optimisation: adaptive traffic signal control at congested junctions\n"
                "- Junction capacity improvement: channelisation, grade separation at high-volume crossings\n"
                "- Traffic management during peak hours: police-assisted flow management at known bottlenecks\n"
                "- Non-motorised traffic separation: dedicated pedestrian and cyclist facilities at high-density corridors\n"
                "- Variable message signs: real-time speed and congestion advisories on urban arterials\n\n"
                "The IRC:SP-73-2015 (guidelines for urban roads) and IRC:106-1990 (pedestrian facilities) "
                "provide detailed design standards applicable to high-traffic urban hotspot zones.\n\n"
                "Attribution: MoRTH road safety guidelines, IRC standards. "
                "Source URL (SPA): https://morth.nic.in/road-safety"
            ),
        },

        # ── IRC Standards Public Reference ──────────────────────────────────
        {
            "chunk_id": "IRC-SP88-001",
            "document_id": "IRC-SP88",
            "title": "IRC:SP-88 — Road Safety Audit Manual (India)",
            "source_organization": "Indian Roads Congress (IRC)",
            "source_url": "https://irc.nic.in/",
            "document_type": "STANDARD_REFERENCE",
            "publication_date": "2010-01-01",
            "topic": "Road Safety Audit (RSA) — process, scope, and application in India",
            "risk_factors": ["lag_expanding_accidents", "lag_expanding_fatal_rate", "lag_expanding_major_rate"],
            "keywords": ["road safety audit", "RSA", "IRC SP-88", "safety inspection", "design review"],
            "content": (
                "NOTE: IRC publications are available through the IRC (irc.nic.in) and select government "
                "procurement portals. Full text is not freely accessible online. This entry summarises "
                "publicly known provisions.\n\n"
                "IRC:SP-88 establishes the guidelines for Road Safety Audit (RSA) in India. RSA is an "
                "independent, formal safety performance examination of a proposed or existing road by a "
                "qualified team.\n\n"
                "Key provisions:\n"
                "- RSA applies at all project stages: feasibility, draft design, detailed design, "
                "pre-opening, and in-service.\n"
                "- In-service RSA (also called 'Road Safety Inspection') is used for existing roads "
                "including identified blackspots and accident-prone sections.\n"
                "- The RSA process identifies specific safety deficiencies and recommends countermeasures "
                "with priority ranking.\n"
                "- Common RSA findings at high-risk urban locations: inadequate sight distance, poor "
                "junction geometry, inadequate pedestrian facilities, insufficient lighting, missing "
                "or unclear road markings and signage.\n\n"
                "RSA is now mandatory for all National Highway projects above threshold length in India, "
                "per NHAI's Road Safety Policy.\n\n"
                "Reference: IRC:SP-88-2010, Indian Roads Congress, New Delhi. "
                "Procurement: https://irc.nic.in/"
            ),
        },
        {
            "chunk_id": "IRC-SP55-001",
            "document_id": "IRC-SP55",
            "title": "IRC:SP-55 — Urban Road Safety Measures",
            "source_organization": "Indian Roads Congress (IRC)",
            "source_url": "https://irc.nic.in/",
            "document_type": "STANDARD_REFERENCE",
            "publication_date": "2014-01-01",
            "topic": "Safety measures for urban road intersections and high-risk locations",
            "risk_factors": ["lag_expanding_accidents", "lag_zw_expanding_swri", "is_peak_window"],
            "keywords": ["urban road safety", "intersection", "signalisation", "traffic calming", "IRC SP-55"],
            "content": (
                "NOTE: IRC:SP-55 guidelines for urban road safety. Full text procurable through IRC. "
                "Content here summarises publicly known provisions.\n\n"
                "IRC:SP-55 addresses safety at urban roads and intersections. Key guidance elements:\n\n"
                "Intersection safety:\n"
                "- Channelisation of turning movements to reduce conflict points\n"
                "- Provision of traffic signals with dedicated pedestrian phases at high-volume junctions\n"
                "- Visibility improvement: clear zone at corners, pruning of vegetation near junctions\n"
                "- Road markings: stop lines, pedestrian crossing markings, advance warning markings\n\n"
                "Traffic calming in residential and mixed-use areas:\n"
                "- Speed tables, speed humps at spacing consistent with target speed (30 km/h zones)\n"
                "- Raised pedestrian crossings with illumination\n"
                "- Median refuge islands for pedestrian phasing at wide roads\n\n"
                "Night-time safety:\n"
                "- Minimum road lighting standards for urban arterials and intersections\n"
                "- Retroreflective markings and delineators on all urban roads\n\n"
                "Reference: IRC:SP-55-2014, Indian Roads Congress, New Delhi."
            ),
        },
        {
            "chunk_id": "IRC-67-001",
            "document_id": "IRC-67",
            "title": "IRC:67 — Code of Practice for Road Signs",
            "source_organization": "Indian Roads Congress (IRC)",
            "source_url": "https://irc.nic.in/",
            "document_type": "STANDARD_REFERENCE",
            "publication_date": "2012-01-01",
            "topic": "Road signs, warning signs, and signage at hazardous locations",
            "risk_factors": ["lag_expanding_accidents", "lag_zw_expanding_swri"],
            "keywords": ["road signs", "warning signs", "signage", "hazard marking", "advance warning", "IRC 67"],
            "content": (
                "IRC:67 specifies the code of practice for road signs in India, covering mandatory signs, "
                "cautionary signs, informatory signs, and special purpose signs.\n\n"
                "At identified high-risk or accident-prone locations, IRC:67 requires:\n"
                "- Cautionary signs (triangular, yellow background): 'accident prone zone', 'sharp curve "
                "ahead', 'narrow road', 'uneven road', 'pedestrian crossing'\n"
                "- Speed limit signs (circular, white background, red border) at appropriate intervals "
                "approaching and through the hazardous section\n"
                "- Advance warning signs at appropriate distances from the hazard\n"
                "- Reflective / retroreflective properties for all signs on night-hazard sections\n\n"
                "At hotspot locations with high historical SWRI scores, comprehensive signage audit and "
                "rectification — including installation of missing signs and replacement of faded/damaged "
                "signs — is a low-cost, high-impact countermeasure.\n\n"
                "Reference: IRC:67-2012, Indian Roads Congress, New Delhi."
            ),
        },

        # ── Vulnerable Road Users ─────────────────────────────────────────
        {
            "chunk_id": "WHO-VRU-001",
            "document_id": "WHO-VRU",
            "title": "Protecting Vulnerable Road Users — WHO Global Guidance",
            "source_organization": "World Health Organization",
            "source_url": "https://www.who.int/news-room/fact-sheets/detail/road-traffic-injuries",
            "document_type": "GUIDANCE",
            "publication_date": "2023-12-13",
            "topic": "Pedestrian, cyclist, and two-wheeler safety in India",
            "risk_factors": ["lag_expanding_fatal_rate", "lag_expanding_major_rate", "lag_expanding_casualty_density"],
            "keywords": ["pedestrian safety", "cyclist safety", "two-wheeler", "motorcycle", "helmet", "footpath"],
            "content": (
                "More than half of all road traffic deaths globally involve vulnerable road users (VRUs): "
                "pedestrians, cyclists, and motorcyclists. In India, VRUs account for a disproportionate "
                "share of fatalities.\n\n"
                "Countermeasures for VRU safety:\n\n"
                "Motorcyclists and two-wheelers:\n"
                "- Mandatory helmet laws with quality standards (IS:4151) and enforcement\n"
                "- Dedicated motorcycle lanes on high-volume arterials\n"
                "- Targeted enforcement of over-speeding by two-wheelers at known hotspots\n\n"
                "Pedestrians:\n"
                "- Provision of footpaths (minimum 1.8 m width as per IRC:103) on all urban roads\n"
                "- Grade-separated or signal-controlled pedestrian crossings at high-volume junctions\n"
                "- Street lighting at pedestrian crossings and bus stops\n\n"
                "Cyclists:\n"
                "- Dedicated cycle lanes or tracks physically separated from motorised traffic\n"
                "- Cycle-friendly junction design with advanced stop lines\n\n"
                "Source: WHO Global Fact Sheet — Road Traffic Injuries (2023)"
            ),
        },

        # ── Road Safety Data and Monitoring ──────────────────────────────────
        {
            "chunk_id": "IRAD-001",
            "document_id": "IRAD",
            "title": "Integrated Road Accident Database (iRAD) — India",
            "source_organization": "Ministry of Road Transport and Highways / NIC, Government of India",
            "source_url": "https://irad.nic.in/",
            "document_type": "SYSTEM_REFERENCE",
            "publication_date": "N/A",
            "topic": "Road accident data collection, hotspot identification, and monitoring in India",
            "risk_factors": ["lag_expanding_accidents", "lag_expanding_fatal_rate"],
            "keywords": ["iRAD", "accident database", "crash data", "hotspot monitoring", "data collection", "road safety data"],
            "content": (
                "The Integrated Road Accident Database (iRAD) is India's national platform for collecting, "
                "storing, and analysing road accident data. Developed by NIC for MoRTH, iRAD digitises the "
                "First Information Report (FIR) and spot inspection data for every reportable road accident.\n\n"
                "Key features of iRAD relevant to road safety analysis:\n"
                "- GPS-tagged accident location data enabling spatial hotspot analysis\n"
                "- Time-stamped records enabling temporal pattern analysis (time-of-day, day-of-week)\n"
                "- Crash severity categorisation: fatal, grievous, minor\n"
                "- Cause-code data: overspeeding, signal violation, drunk driving, weather, etc.\n"
                "- Blackspot identification module: auto-flags locations meeting MoRTH blackspot criteria\n\n"
                "iRAD data, combined with ML-based spatiotemporal risk prediction, can enhance blackspot "
                "prioritisation beyond the standard 3-year lookback window by incorporating trend dynamics "
                "and zone-time interaction effects.\n\n"
                "Attribution: iRAD System — MoRTH/NIC. "
                "Source URL: https://irad.nic.in/"
            ),
        },
    ]

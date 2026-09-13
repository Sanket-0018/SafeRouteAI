"""
SafeRoute AI — IBM Bob Inference Service Layer
Integrates IBM Bob Generative AI to provide user-triggered,
evidence-grounded journey safety briefings based strictly on
SafeRouteAI deterministic pipeline findings.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

# Ensure .env is loaded from project root if not already loaded
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)

logger = logging.getLogger("saferoute.bob")

# Official IBM Bob Inference Gateway Configuration
IBM_BOB_GATEWAY_URL = os.getenv("BOB_GATEWAY_URL", "https://api.us-east.bob.ibm.com")
IBM_BOB_INFERENCE_PATH = "/inference/v1/chat/completions"
IBM_BOB_MODEL = os.getenv("BOB_MODEL", "premium-ide")
IBM_BOB_TIMEOUT_SECONDS = 25

RESPONSIBLE_AI_DISCLAIMER = (
    "AI-generated decision support based on available historical and official evidence. "
    "It does not guarantee safety."
)


def get_bob_api_key() -> Optional[str]:
    """Retrieve BOB_API_KEY from environment without logging or exposing it."""
    key = os.getenv("BOB_API_KEY")
    if key and key.strip():
        return key.strip()
    return None


def generate_bob_journey_brief(
    route: str,
    distance_km: float,
    duration: str,
    departure: Optional[str] = None,
    risk_window: Optional[str] = None,
    hazards: Optional[list] = None,
) -> dict:
    """
    Calls the official IBM Bob Inference API to generate a concise,
    decision-support safety briefing for an analyzed journey.
    """
    api_key = get_bob_api_key()
    if not api_key:
        logger.warning("IBM Bob API request attempted without BOB_API_KEY set.")
        raise HTTPException(
            status_code=503,
            detail="IBM Bob AI service is currently unconfigured. Set BOB_API_KEY in backend environment.",
        )

    # Filter/cap hazards to top 6 items to keep token payload minimal and cost-efficient
    hazard_items = []
    if hazards:
        for h in hazards[:6]:
            if isinstance(h, dict):
                h_type = h.get("type", "Hazard")
                h_name = h.get("name", "Unknown location")
                h_dist = h.get("distance_km", 0.0)
                h_eta = h.get("eta", "")
                item = {
                    "type": h_type,
                    "name": h_name,
                    "distance_km": round(float(h_dist), 1) if h_dist is not None else 0.0,
                    "eta": h_eta,
                }
                if h.get("risk_tier"):
                    item["risk_tier"] = h.get("risk_tier")
                if h.get("road_context"):
                    item["road_context"] = h.get("road_context")
                hazard_items.append(item)

    structured_evidence = {
        "route": route,
        "distance_km": round(float(distance_km), 1),
        "duration": duration,
        "departure": departure or "Not specified",
        "risk_window": risk_window or "Standard historical distribution",
        "hazards": hazard_items,
    }

    system_prompt = (
        "You are the SafeRoute AI Journey Safety Assistant powered by IBM Bob.\n"
        "Your role is STRICTLY to summarize and explain the supplied SafeRouteAI analysis evidence in a concise briefing (4 to 5 bullet points).\n"
        "SafeRouteAI analysis is the sole source of truth. You are an evidence summarizer, not a general-knowledge advice generator.\n\n"
        "STRICT EVIDENCE-GROUNDING RULES:\n"
        "1. SUMMARIZE ONLY SUPPLIED FACTS: You may summarize only facts explicitly supplied in the evidence payload. If a condition, factor, observation, or statistic is not present in the payload, OMIT IT ENTIRELY.\n"
        "2. SUPPLIED RISK WINDOW & TIMING: Mention the supplied historical risk window and compare the supplied departure time to that window.\n"
        "3. HAZARD DIFFERENTIATION & SELECTION: Strictly distinguish between:\n"
        "   - ML-predicted hotspot ('ML hotspot'): flagged by machine learning models based on historical pattern density.\n"
        "   - Official blackspot ('Official blackspot'): formally designated by government/police transport authorities.\n"
        "   - NEVER refer to an ML-predicted hotspot as an officially designated blackspot.\n"
        "   - Do not force mentioning every single hazard; summarize the most important supplied evidence only.\n"
        "4. ROAD/INFRASTRUCTURE CONTEXT: Mention supplied road context or observations ONLY when explicitly present in the hazard items.\n"
        "5. DO NOT INFER CAUSES OR INVENT CONDITIONS: You must NOT infer causes from general world knowledge, and must NOT add information simply because it sounds like common road-safety advice. Specifically:\n"
        "   - Do NOT invent weather, rain, monsoon, or fog conditions (even if the date falls in a season like monsoon).\n"
        "   - Do NOT invent visibility conditions, lighting, or glare.\n"
        "   - Do NOT invent driver fatigue, drowsiness, drunk driving, or speeding.\n"
        "   - Do NOT invent enforcement presence, police patrolling, or traffic violation rates.\n"
        "   - Do NOT invent traffic congestion, road defects, potholes, or surface grip conditions.\n"
        "   - Do NOT turn statistical correlation into claimed causation.\n"
        "6. PRACTICAL SAFETY GUIDANCE (FINAL BULLET): The final bullet should preferably be a short practical precaution based on the supplied journey evidence (e.g. maintaining safe following distance, adherence to posted corridor limits, remaining attentive). This guidance MUST be clearly framed as a general precaution, NEVER as a claimed cause of the specific hazard or stretch.\n"
        "7. CONCISENESS & COMPLETENESS RULES:\n"
        "   - Keep the response concise: target 4 to 5 bullet points rather than trying to fill 6 bullets.\n"
        "   - Each bullet must be a complete sentence. Never return a partial or truncated bullet.\n"
        "   - Return only complete bullets. If there is not enough output space to complete another bullet, omit that bullet entirely.\n"
        "   - Prefer concise wording so the model has enough output space.\n"
        "   - You may start with an optional single header: '🛡️ SafeRoute AI Journey Safety Brief'\n"
        "   - Do NOT output markdown heading symbols like '##' or '#'.\n"
        "   - Do NOT output divider lines like '---' or '--'.\n"
        "   - Do NOT output blank bullets or empty filler lines.\n"
        "   - Direct, grounded, and factual."
    )

    user_prompt = (
        f"SafeRouteAI Journey Analysis Evidence:\n"
        f"```json\n{json.dumps(structured_evidence, indent=2)}\n```\n"
        f"Generate the concise AI Journey Safety Brief based STRICTLY on this evidence."
    )

    target_url = f"{IBM_BOB_GATEWAY_URL.rstrip('/')}{IBM_BOB_INFERENCE_PATH}"
    headers = {
        "Authorization": f"apikey {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "SafeRouteAI/1.0 (bobshell/2.0.2)",
    }

    payload = {
        "model": IBM_BOB_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 500,
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            target_url,
            headers=headers,
            json=payload,
            timeout=IBM_BOB_TIMEOUT_SECONDS,
        )
    except requests.exceptions.Timeout:
        logger.error("IBM Bob inference API request timed out after %ds", IBM_BOB_TIMEOUT_SECONDS)
        raise HTTPException(
            status_code=504,
            detail="IBM Bob AI inference request timed out. Please try again.",
        )
    except requests.exceptions.RequestException as exc:
        logger.error("Network error communicating with IBM Bob: %s", str(exc))
        raise HTTPException(
            status_code=502,
            detail="Network error connecting to IBM Bob AI inference gateway.",
        )

    if response.status_code == 401 or response.status_code == 403:
        logger.error("IBM Bob authentication error (HTTP %d)", response.status_code)
        raise HTTPException(
            status_code=502,
            detail="IBM Bob API authentication failed. Verify API key validity.",
        )
    elif response.status_code == 402:
        logger.error("IBM Bob budget/Bobcoin error: %s", response.text[:200])
        raise HTTPException(
            status_code=502,
            detail="IBM Bob credit limit exceeded or account requires Bobcoins.",
        )
    elif response.status_code != 200:
        logger.error("IBM Bob returned HTTP %d: %s", response.status_code, response.text[:200])
        raise HTTPException(
            status_code=502,
            detail=f"IBM Bob API returned status {response.status_code}.",
        )

    try:
        result_data = response.json()
        raw_content = result_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as err:
        logger.error("Malformed response from IBM Bob: %s", str(err))
        raise HTTPException(
            status_code=502,
            detail="Malformed response payload received from IBM Bob AI.",
        )

    # Response handling: ensure briefing always ends at a complete sentence/bullet
    brief_content = clean_bob_brief_content(raw_content)

    return {
        "brief": brief_content,
        "model": f"IBM Bob ({IBM_BOB_MODEL})",
        "disclaimer": RESPONSIBLE_AI_DISCLAIMER,
    }


def clean_bob_brief_content(content: str) -> str:
    """
    Ensures that the brief ALWAYS ends at a complete sentence/bullet.
    If the last bullet or sentence was cut off without terminal punctuation,
    it is safely omitted rather than showing an unfinished thought to the user.
    """
    if not content or not content.strip():
        return ""

    lines = [line.strip() for line in content.split("\n")]
    terminal_punctuation = (".", "!", "?", '"', "'", "”", "’")

    # Filter empty lines
    clean_lines = [l for l in lines if l]

    # Inspect the trailing line. If it is a bullet or sentence that doesn't end with terminal punctuation,
    # strip it so the response always ends cleanly on a full sentence.
    while clean_lines:
        last = clean_lines[-1]
        is_bullet = last.startswith(("-", "*", "•")) or any(last.startswith(f"{i}.") for i in range(1, 10))
        if is_bullet:
            if not last.endswith(terminal_punctuation):
                logger.warning("Omitting trailing truncated bullet from Bob response: %s", last)
                clean_lines.pop()
                continue
        elif len(clean_lines) > 1 and not last.endswith(terminal_punctuation):
            logger.warning("Omitting trailing truncated line from Bob response: %s", last)
            clean_lines.pop()
            continue
        break

    return "\n".join(clean_lines).strip()


"""
Research paper analysis using Gemini.

One Gemini call per research paper.
Returns structured JSON for academic analysis.
"""

import json
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


_RESEARCH_PROMPT = """
You are an academic research assistant.

Analyze the supplied research paper carefully and return ONLY valid JSON.
Do not return Markdown, code fences, explanations, or text outside JSON.

Use this exact schema:
{
  "paper_info": {
    "title": "",
    "authors": [],
    "publication_year": "",
    "venue": "",
    "keywords": []
  },
  "research_problem": "",
  "objectives": [],
  "existing_approach": "",
  "proposed_methodology": "",
  "dataset": {
    "name": "",
    "description": "",
    "size": "",
    "source": ""
  },
  "technologies_and_algorithms": [],
  "evaluation_metrics": [],
  "results": [],
  "advantages": [],
  "limitations": [],
  "future_work": [],
  "key_contributions": [],
  "research_gap": ""
}

Rules:
- Only use information supported by the paper.
- Do not invent datasets, results, authors, algorithms, or claims.
- If information is unavailable, use an empty string or empty array.
- Keep technical terms accurate.
- Make the analysis useful for a college student preparing a literature survey.

RESEARCH PAPER:
{text}
"""


def _repair_json(raw: str) -> dict:
    """Parse Gemini JSON and repair common formatting issues."""

    text = raw.strip()

    # Remove Markdown code fences, if present.
    text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text).strip()

    # Try parsing the complete response.
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Extract the outermost JSON object.
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        raise ValueError(
            "Gemini did not return a JSON object. "
            f"Response preview: {raw[:300]}"
        )

    candidate = text[start : end + 1]

    # Try parsing the extracted object.
    try:
        result = json.loads(candidate)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Repair trailing commas before closing braces or brackets.
    fixed = re.sub(r",\s*([}\]])", r"\1", candidate)

    try:
        result = json.loads(fixed)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned malformed JSON that could not be repaired. "
            f"Parsing error: {exc}. "
            f"Response preview: {raw[:300]}"
        ) from exc

    raise ValueError("Gemini did not return a valid JSON object.")


def _normalize_analysis(data: dict) -> dict:
    """Ensure expected sections exist without inventing paper content."""

    defaults = {
        "paper_info": {
            "title": "",
            "authors": [],
            "publication_year": "",
            "venue": "",
            "keywords": [],
        },
        "research_problem": "",
        "objectives": [],
        "existing_approach": "",
        "proposed_methodology": "",
        "dataset": {
            "name": "",
            "description": "",
            "size": "",
            "source": "",
        },
        "technologies_and_algorithms": [],
        "evaluation_metrics": [],
        "results": [],
        "advantages": [],
        "limitations": [],
        "future_work": [],
        "key_contributions": [],
        "research_gap": "",
    }

    for key, default_value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_value

    if not isinstance(data["paper_info"], dict):
        data["paper_info"] = defaults["paper_info"].copy()
    else:
        for key, default_value in defaults["paper_info"].items():
            if key not in data["paper_info"] or data["paper_info"][key] is None:
                data["paper_info"][key] = default_value

    if not isinstance(data["dataset"], dict):
        data["dataset"] = defaults["dataset"].copy()
    else:
        for key, default_value in defaults["dataset"].items():
            if key not in data["dataset"] or data["dataset"][key] is None:
                data["dataset"][key] = default_value

    return data


def analyze_research_paper(
    text: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """Analyze one research paper with a single Gemini API call."""

    api_key = (
        st.secrets.get("GEMINI_API_KEY", "")
        or os.getenv("GEMINI_API_KEY", "")
    ).strip()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found. "
            "Add it to your local .env file or Streamlit secrets."
        )

    if not text or not text.strip():
        raise ValueError("No text was extracted from the research paper.")

    client = genai.Client(api_key=api_key)
    prompt = _RESEARCH_PROMPT.replace("{text}", text)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    except Exception as exc:
        raise ValueError(f"Gemini API call failed: {exc}") from exc

    raw = response.text or ""

    if not raw.strip():
        raise ValueError("Gemini returned an empty response.")

    analysis = _repair_json(raw)
    return _normalize_analysis(analysis)

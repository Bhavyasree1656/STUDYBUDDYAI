"""
Gemini AI integration — ONE call per document, structured JSON output.

Returns a validated dict with keys: summary, explanation, quiz, flashcards.
Includes multi-strategy JSON repair for malformed responses.
"""

import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Prompt ────────────────────────────────────────────────────────────────────

_PROMPT = """You are an expert educator. Analyse the following study material thoroughly and produce a complete study pack.

Return ONLY valid JSON — no markdown, no code fences, no preamble, no trailing text.
Use this EXACT schema (every key is required):

{{
  "summary": {{
    "short_summary": "<concise 2-3 sentence overview of the entire material>",
    "bullet_points": [
      "<key point 1>",
      "<key point 2>"
    ],
    "key_takeaways": [
      "<most important takeaway 1>",
      "<most important takeaway 2>"
    ]
  }},
  "explanation": {{
    "simple_explanation": "<plain-language explanation for a student — multiple paragraphs separated by \\n\\n>",
    "important_concepts": [
      {{"concept": "<term>", "definition": "<clear definition>"}}
    ],
    "real_life_examples": [
      "<specific real-world example 1>",
      "<specific real-world example 2>"
    ],
    "exam_tips": [
      "<actionable study or exam tip 1>",
      "<actionable study or exam tip 2>"
    ]
  }},
  "quiz": [
    {{
      "question": "<question text>",
      "options": ["A) <option>", "B) <option>", "C) <option>", "D) <option>"],
      "answer": "<exact matching option string, e.g. A) option text>",
      "explanation": "<why this answer is correct>"
    }}
  ],
  "flashcards": [
    {{
      "front": "<term or concept>",
      "back": "<clear definition or explanation>"
    }}
  ]
}}

Minimum requirements (exceed these when content allows):
- summary.bullet_points: 8+ items
- summary.key_takeaways: 5+ items
- explanation.important_concepts: 8+ items
- explanation.real_life_examples: 4+ items
- explanation.exam_tips: 5+ items
- quiz: 10+ questions, each with exactly 4 A/B/C/D options
- flashcards: 15+ cards

--- STUDY MATERIAL ---
{text}
"""


# ── JSON repair ───────────────────────────────────────────────────────────────

def _repair_json(raw: str) -> dict:
    """Try multiple strategies to extract valid JSON from Gemini output."""
    text = raw.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip code fences  (```json … ```)
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    stripped = re.sub(r"\s*```\s*$", "", stripped, flags=re.MULTILINE).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Extract first { … last }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # 4. Fix trailing commas + repair bare strings
        fixed = re.sub(r",(\s*[}\]])", r"\1", candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Gemini returned JSON that could not be repaired.\n"
        f"First 500 chars of raw response:\n{raw[:500]}"
    )


# ── Validation ────────────────────────────────────────────────────────────────

def _validate(data: dict) -> dict:
    """Ensure correct types; fill missing keys with safe defaults."""

    def _list_of_str(val) -> list:
        if isinstance(val, list):
            return [str(i) for i in val]
        return []

    def _list_of_dict(val) -> list:
        if isinstance(val, list):
            return [i for i in val if isinstance(i, dict)]
        return []

    # summary
    raw_s = data.get("summary", {})
    if not isinstance(raw_s, dict):
        raw_s = {"short_summary": str(raw_s)}
    data["summary"] = {
        "short_summary": str(raw_s.get("short_summary", "")),
        "bullet_points": _list_of_str(raw_s.get("bullet_points")),
        "key_takeaways": _list_of_str(raw_s.get("key_takeaways")),
    }

    # explanation
    raw_e = data.get("explanation", {})
    if not isinstance(raw_e, dict):
        raw_e = {"simple_explanation": str(raw_e)}
    data["explanation"] = {
        "simple_explanation": str(raw_e.get("simple_explanation", "")),
        "important_concepts": _list_of_dict(raw_e.get("important_concepts")),
        "real_life_examples": _list_of_str(raw_e.get("real_life_examples")),
        "exam_tips":          _list_of_str(raw_e.get("exam_tips")),
    }

    # quiz
    raw_q = data.get("quiz", [])
    data["quiz"] = [
        q for q in _list_of_dict(raw_q)
        if "question" in q and "options" in q and "answer" in q
    ]

    # flashcards
    raw_f = data.get("flashcards", [])
    data["flashcards"] = [
        f for f in _list_of_dict(raw_f)
        if "front" in f and "back" in f
    ]

    return data


# ── Public API ────────────────────────────────────────────────────────────────

def generate_study_pack(text: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Single Gemini call.
    Returns validated dict: {summary, explanation, quiz, flashcards}.
    Raises ValueError on bad API key or unrecoverable JSON.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set.\n"
            "Add it to your .env file:\n"
            "  GEMINI_API_KEY=your_key_here\n"
            "Get a free key at: https://aistudio.google.com/apikey"
        )

    client   = genai.Client(api_key=api_key)
    prompt   = _PROMPT.format(text=text)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
    except Exception as e:
        raise ValueError(f"Gemini API call failed: {e}") from e

    raw  = response.text or ""
    data = _repair_json(raw)
    return _validate(data)

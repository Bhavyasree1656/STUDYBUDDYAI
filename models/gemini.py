
"""
Gemini AI integration — one API call per document.
Returns validated JSON containing summary, explanation, quiz, and flashcards.
"""

import json
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv(Path(__file__).parent.parent / ".env")


_PROMPT = """
You are an expert educator. Analyze the study material thoroughly.

Return ONLY valid JSON. Do not include Markdown fences or extra text.

Use this exact schema:

{{
  "summary": {{
    "short_summary": "A concise 2-3 sentence overview",
    "bullet_points": ["Key point 1", "Key point 2"],
    "key_takeaways": ["Takeaway 1", "Takeaway 2"]
  }},
  "explanation": {{
    "simple_explanation": "A clear, student-friendly explanation",
    "important_concepts": [
      {{"concept": "Term", "definition": "Clear definition"}}
    ],
    "real_life_examples": ["Example 1", "Example 2"],
    "exam_tips": ["Tip 1", "Tip 2"]
  }},
  "quiz": [
    {{
      "question": "Question text",
      "options": [
        "A) Option one",
        "B) Option two",
        "C) Option three",
        "D) Option four"
      ],
      "answer": "A) Option one",
      "explanation": "Why the answer is correct"
    }}
  ],
  "flashcards": [
    {{
      "front": "Term or concept",
      "back": "Definition or explanation"
    }}
  ]
}}

Requirements:
- Summary: at least 8 bullet points and 5 key takeaways.
- Explanation: at least 8 important concepts, 4 real-life examples,
  and 5 exam tips.
- Quiz: at least 10 questions, each with exactly 4 options.
- The quiz answer must exactly match one of its options.
- Flashcards: at least 15 cards.
- Base all content on the supplied study material.
- Do not invent facts that the material does not support.
- If the material is too short to meet a requirement, provide the
  best possible result without inventing information.

STUDY MATERIAL:
{text}
"""


def _get_api_key() -> str:
    """Read the key from Streamlit secrets or the local environment."""

    api_key = ""

    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        # Local secrets.toml may not exist yet.
        pass

    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    return api_key.strip()


def _repair_json(raw: str) -> dict:
    """Parse Gemini JSON and repair common formatting issues."""

    text = (raw or "").strip()

    if not text:
        raise ValueError("Gemini returned an empty response.")

    # Try parsing the response directly.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove Markdown code fences.
    stripped = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    stripped = re.sub(r"\s*```\s*$", "", stripped).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Extract the first JSON object.
    start = stripped.find("{")
    end = stripped.rfind("}")

    if start != -1 and end > start:
        candidate = stripped[start:end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

        # Remove trailing commas before closing braces or brackets.
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)

        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Gemini returned a response that could not be parsed as JSON. "
        "Try a shorter document or review the response format."
    )


def _list_of_str(value) -> list:
    if not isinstance(value, list):
        return []

    return [
        item if isinstance(item, str) else str(item)
        for item in value
        if item is not None
    ]


def _list_of_dict(value) -> list:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


def _validate(data: dict) -> dict:
    """Normalize the generated study pack for the application."""

    if not isinstance(data, dict):
        raise ValueError("Gemini returned an invalid study-pack structure.")

    raw_summary = data.get("summary", {})
    if not isinstance(raw_summary, dict):
        raw_summary = {"short_summary": str(raw_summary)}

    raw_explanation = data.get("explanation", {})
    if not isinstance(raw_explanation, dict):
        raw_explanation = {"simple_explanation": str(raw_explanation)}

    quiz = []

    for question in _list_of_dict(data.get("quiz")):
        options = _list_of_str(question.get("options"))

        if (
            question.get("question")
            and len(options) == 4
            and question.get("answer") in options
        ):
            quiz.append({
                "question": str(question["question"]),
                "options": options,
                "answer": str(question["answer"]),
                "explanation": str(question.get("explanation", "")),
            })

    flashcards = [
        {
            "front": str(card["front"]),
            "back": str(card["back"]),
        }
        for card in _list_of_dict(data.get("flashcards"))
        if card.get("front") and card.get("back")
    ]

    return {
        "summary": {
            "short_summary": str(
                raw_summary.get("short_summary", "")
            ),
            "bullet_points": _list_of_str(
                raw_summary.get("bullet_points")
            ),
            "key_takeaways": _list_of_str(
                raw_summary.get("key_takeaways")
            ),
        },
        "explanation": {
            "simple_explanation": str(
                raw_explanation.get("simple_explanation", "")
            ),
            "important_concepts": _list_of_dict(
                raw_explanation.get("important_concepts")
            ),
            "real_life_examples": _list_of_str(
                raw_explanation.get("real_life_examples")
            ),
            "exam_tips": _list_of_str(
                raw_explanation.get("exam_tips")
            ),
        },
        "quiz": quiz,
        "flashcards": flashcards,
    }


def generate_study_pack(
    text: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """Generate a complete study pack with one Gemini API request."""

    if not text or not text.strip():
        raise ValueError("No text was extracted from the uploaded document.")

    api_key = _get_api_key()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured. "
            "Add it to .streamlit/secrets.toml before generating a study pack."
        )

    client = genai.Client(api_key=api_key)
    prompt = _PROMPT.format(text=text)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise ValueError(f"Gemini API request failed: {exc}") from exc

    try:
        data = _repair_json(response.text or "")
        return _validate(data)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            f"Could not process the generated study pack: {exc}"
        ) from exc

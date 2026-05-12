#!/usr/bin/env python3
"""Extract knowns / unknowns from a math problem using the DeepSeek API.

Two ways to set your API key (checked in order):
  1. Paste it in the DEEPSEEK_API_KEY variable below (line ~17)
  2. Set the environment variable:  export DEEPSEEK_API_KEY="sk-..."
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import List

from openai import OpenAI

# ── 1. PUT YOUR MATH PROBLEM & API KEY HERE ───────────────────────────────
MATH_PROBLEM = "Prove that no three positive integers a, b, and c can satisfy the equation a^n + b^n = c^n for any integer value of n greater than 2."

DEEPSEEK_API_KEY = ""  # <-- paste your DeepSeek API key here
# ───────────────────────────────────────────────────────────────────────────


PROMPT_TEMPLATE = (
    "You are a math reasoning assistant that extracts proof states.\n"
    "Given the following math problem statement, return only valid JSON "
    "with two fields: known and unknown.\n"
    "- known: list every condition or fact that is given or assumed.\n"
    "- unknown: list the item(s) that must be proved or found.\n"
    "Do not include any extra text, explanation, or metadata. "
    "Use short canonical statements where possible.\n"
    "Example output format:\n"
    '{{"known": ["p is prime", "a is integer"], "unknown": ["a^p = a mod p"]}}\n'
    "\nInput statement:\n{statement}\n"
)


def _get_api_key() -> str:
    key = DEEPSEEK_API_KEY.strip() or os.environ.get("DEEPSEEK_API_KEY", "sk-aaaa40fe4d7a49868d4f2f5e662cddcf")
    if not key:
        print("Error: no DeepSeek API key found.", file=sys.stderr)
        print("  Option 1: set DEEPSEEK_API_KEY in this file (line ~17)", file=sys.stderr)
        print("  Option 2: export DEEPSEEK_API_KEY='your-key'", file=sys.stderr)
        sys.exit(1)
    return key


def build_prompt(statement: str) -> str:
    return PROMPT_TEMPLATE.format(statement=statement.strip())


def call_deepseek(prompt: str, api_key: str) -> str:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def parse_response(raw: str) -> dict:
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse LLM response:\n{raw}")


def extract(problem: str, api_key: str) -> dict:
    prompt = build_prompt(problem)
    raw = call_deepseek(prompt, api_key)
    return parse_response(raw)


def render(problem: str, result: dict) -> str:
    knowns = result.get("known", [])
    unknowns = result.get("unknown", [])

    lines = [
        "=" * 60,
        "MATH PROBLEM",
        "=" * 60,
        problem,
        "",
        "=" * 60,
        "KNOWN (given / assumed)",
        "=" * 60,
    ]
    if knowns:
        for item in knowns:
            lines.append(f"  - {item}")
    else:
        lines.append("  (none)")

    lines.extend([
        "",
        "=" * 60,
        "UNKNOWN (to find / prove)",
        "=" * 60,
    ])
    if unknowns:
        for item in unknowns:
            lines.append(f"  - {item}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def main() -> None:
    api_key = _get_api_key()

    problem = MATH_PROBLEM
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])

    result = extract(problem, api_key)
    print(render(problem, result))


if __name__ == "__main__":
    main()

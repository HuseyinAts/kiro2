#!/usr/bin/env python
"""
Filter critical issues from cross-validation output.

Removes:
- exact_duplicate: Same question text with same answer appears multiple times
- generic_ai_text: AI-generated generic text that's too short

Usage:
    python filter_critical.py --input input.jsonl --output output.jsonl
"""
import json
import sys
from pathlib import Path
from collections import Counter

def normalize_text(text: str) -> str:
    """Normalize text for duplicate detection."""
    if not text:
        return ""
    # Remove extra whitespace and lowercase
    return " ".join(text.lower().split())

def find_exact_duplicates(questions):
    """Find questions with identical text and answer."""
    text_answer_map = {}
    duplicates = set()

    for idx, q in enumerate(questions):
        # Use question text + answer as key
        text = normalize_text(q.get("text", ""))
        answer = q.get("answer", "").upper()
        if not text or not answer:
            continue

        key = (text, answer)
        if key in text_answer_map:
            duplicates.add(idx)
            duplicates.add(text_answer_map[key])
        else:
            text_answer_map[key] = idx

    return duplicates

def find_generic_ai_text(questions):
    """Find questions with suspiciously short text (likely generic AI output)."""
    generic = set()

    for idx, q in enumerate(questions):
        text = q.get("text", "")
        # If text is very short (<30 chars) and has options, might be generic
        if len(text) < 30 and q.get("options"):
            generic.add(idx)

    return generic

def main():
    if len(sys.argv) < 4 or sys.argv[1] != "--input":
        print("Usage: python filter_critical.py --input input.jsonl --output output.jsonl")
        sys.exit(1)

    input_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    # Load questions
    print(f"Loading: {input_path}")
    questions = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    print(f"Total questions: {len(questions)}")

    # Find issues
    exact_dups = find_exact_duplicates(questions)
    print(f"Exact duplicates found: {len(exact_dups)}")

    generic = find_generic_ai_text(questions)
    print(f"Generic AI text found: {len(generic)}")

    # Combine critical issues
    critical = exact_dups | generic
    print(f"Total to remove: {len(critical)}")

    # Filter
    filtered = [q for idx, q in enumerate(questions) if idx not in critical]

    # Save
    print(f"Writing: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for q in filtered:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"Done! {len(filtered)} questions written")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Removed: {len(questions) - len(filtered)}")
    print(f"Kept: {len(filtered)}")

if __name__ == "__main__":
    main()

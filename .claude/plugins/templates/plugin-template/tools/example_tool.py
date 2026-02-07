"""
Example Tool

Plugin tool implementasyonu örneği.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def execute(
    input: str,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Example tool execution.

    Args:
        input: Input text to process
        options: Optional configuration
            - format: Output format (json, text, markdown)
            - verbose: Include extra information

    Returns:
        Tool result with processed data and metadata
    """
    options = options or {}
    output_format = options.get("format", "text")
    verbose = options.get("verbose", False)

    logger.info(f"Processing input: {input[:50]}...")

    # Process input
    result = process_input(input)

    # Format output
    if output_format == "json":
        formatted = format_as_json(result)
    elif output_format == "markdown":
        formatted = format_as_markdown(result)
    else:
        formatted = result

    # Build response
    response = {
        "result": formatted,
        "metadata": {
            "input_length": len(input),
            "output_length": len(formatted),
            "format": output_format,
        },
    }

    if verbose:
        response["metadata"]["details"] = {
            "processing_steps": ["parse", "transform", "format"],
            "options_used": options,
        }

    return response


def process_input(input: str) -> str:
    """
    Process input text.

    Args:
        input: Raw input text

    Returns:
        Processed text
    """
    # Example processing
    lines = input.strip().split("\n")
    processed_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(processed_lines)


def format_as_json(text: str) -> str:
    """Format as JSON string."""
    import json

    return json.dumps({"content": text}, ensure_ascii=False, indent=2)


def format_as_markdown(text: str) -> str:
    """Format as markdown."""
    lines = text.split("\n")
    formatted = []

    for line in lines:
        if line.startswith("#"):
            formatted.append(line)
        else:
            formatted.append(f"- {line}")

    return "\n".join(formatted)


# CLI entry point for testing
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python example_tool.py <input>")
            sys.exit(1)

        input_text = sys.argv[1]
        options = {"format": "text", "verbose": True}

        result = await execute(input_text, options)
        print(result)

    asyncio.run(main())

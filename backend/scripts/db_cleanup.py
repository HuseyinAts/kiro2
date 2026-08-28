import glob
import os
import re


def fix_syntax_errors():
    models_dir = os.path.join(os.path.dirname(__file__), "../models")
    model_files = glob.glob(os.path.join(models_dir, "*.py"))

    for filepath in model_files:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Replace:  , \n  , lazy="selectin" -> , \n lazy="selectin"
        # Or: ,, -> ,
        content = re.sub(
            r',\s*,\s*lazy="selectin"', ',\n        lazy="selectin"', content
        )
        # Handle cases where there might just be an extra comma
        content = re.sub(r",\s*,\s*deferred=True", ",\n        deferred=True", content)

        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)


if __name__ == "__main__":
    fix_syntax_errors()

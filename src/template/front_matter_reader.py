from pathlib import Path
import yaml


class FrontMatterReader:
    def __init__(self):
        pass

    def read_frontmatter(self, file_path: Path | str) -> tuple[dict | None, str]:
        """
        Return (frontmatter_dict or None, remaining_markdown_text).
        Expects YAML frontmatter fenced with '---' (start and end) at the top of the file.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        text = path.read_text(encoding="utf-8")
        # remove BOM if present
        if text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")

        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return None, text

        fm_lines = []
        i = 1
        while i < len(lines) and lines[i].strip() not in ("---", "..."):
            fm_lines.append(lines[i])
            i += 1

        # no closing fence => treat as no frontmatter
        if i >= len(lines) or lines[i].strip() not in ("---", "..."):
            return None, text

        frontmatter_text = "".join(fm_lines)
        content = "".join(lines[i + 1 :])

        try:
            fm = yaml.safe_load(frontmatter_text) or {}
        except Exception:
            fm = None

        return fm, content

from pathlib import Path
import yaml


class ObsidianEditor:
    def __init__(self):
        pass

    def read_template(self, file_path: Path | str) -> tuple[dict | None, str]:
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

    def write_template(
        self, file_path: Path | str, frontmatter: dict, content: str
    ) -> Path:
        """
        Write the given frontmatter dict and content string to the specified file.
        The frontmatter is written as YAML fenced with '---' at the top of the file.

        Args:
            file_path (Path | str): The path to the file where the template will be written.
            frontmatter (dict): The frontmatter data to write as YAML.
            content (str): The markdown content to write after the frontmatter.

        Returns:
            Path: The path to the file that was written.
        """
        path = Path(file_path)
        fm_text = yaml.dump(frontmatter, Dumper=yaml.Dumper, sort_keys=False)
        full_text = f"---\n{fm_text}---\n{content}"
        path.write_text(full_text, encoding="utf-8")
        return path

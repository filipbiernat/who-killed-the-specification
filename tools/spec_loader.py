"""Read the requirements in ``spec/`` as plain files.

There is no AI here and nothing is generated. A requirement is a Markdown
file with a YAML header, so reading one is: split on the ``---`` fence,
parse the header, keep the prose.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

SPEC_DIR = Path(__file__).resolve().parent.parent / "spec"


@dataclass
class Requirement:
    uid: str
    heading: str
    text: str
    normative: bool = True
    active: bool = True
    risk: str = "medium"
    tags: list[str] = field(default_factory=list)
    references: list[dict] = field(default_factory=list)
    path: Path | None = None


def load_all(spec_dir: Path = SPEC_DIR) -> list[Requirement]:
    """Every requirement in the document, ordered by UID."""
    return [load(path) for path in sorted(spec_dir.glob("REQ-*.md"))]


def load(path: Path) -> Requirement:
    header, body = _split_front_matter(path.read_text(encoding="utf-8"))
    meta = yaml.safe_load(header) or {}
    heading, text = _split_body(body)
    return Requirement(
        uid=path.stem,
        heading=heading,
        text=text,
        normative=bool(meta.get("normative", True)),
        active=bool(meta.get("active", True)),
        risk=str(meta.get("risk", "medium")),
        tags=list(meta.get("tags") or []),
        references=list(meta.get("references") or []),
        path=path,
    )


def _split_front_matter(raw: str) -> tuple[str, str]:
    if not raw.startswith("---"):
        raise ValueError("requirement file has no YAML front matter")
    _, header, body = raw.split("---", 2)
    return header, body


def _split_body(body: str) -> tuple[str, str]:
    """Return the ``# heading`` and the requirement sentence itself.

    Only the first heading is the requirement's own. Anything below a second
    heading is commentary (a subchapter, a diagram, notes) and must not be
    mistaken for the sentence or for the title.
    """
    heading = ""
    sentence_lines: list[str] = []
    for line in body.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if heading:
                break
            heading = stripped.lstrip("# ").strip()
        elif stripped.startswith("*Rationale:") or not stripped:
            # Rationale explains the requirement; it is not the requirement.
            if sentence_lines:
                break
        else:
            sentence_lines.append(stripped)
    return heading, " ".join(sentence_lines)

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RawDocument:
    doc_id: str          # identifiant stable = chemin relatif du fichier dans le corpus
    category: str        # sous-dossier : catalogue_offres, procedures_depannage, faq, conditions_tarifaires
    title: str
    source_file: str
    content: str


def _extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def load_corpus(corpus_dir: str | Path) -> list[RawDocument]:
    """Parcourt le corpus et retourne un document par fichier .md, avec metadonnees."""
    corpus_dir = Path(corpus_dir)
    documents: list[RawDocument] = []

    for path in sorted(corpus_dir.rglob("*.md")):
        relative = path.relative_to(corpus_dir)
        category = relative.parts[0] if len(relative.parts) > 1 else "general"
        text = path.read_text(encoding="utf-8")
        title = _extract_title(text, fallback=path.stem)

        documents.append(
            RawDocument(
                doc_id=str(relative),
                category=category,
                title=title,
                source_file=str(relative),
                content=text,
            )
        )

    return documents

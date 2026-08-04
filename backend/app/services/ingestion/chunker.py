from dataclasses import dataclass

from app.services.ingestion.loader import RawDocument

MAX_CHUNK_CHARS = 800
OVERLAP_CHARS = 120


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_id: str
    category: str
    title: str
    source_file: str
    chunk_index: int
    content: str


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def chunk_document(
    doc: RawDocument, max_chars: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS
) -> list[DocumentChunk]:
    """
    Chunking par paragraphes avec accumulation gloutonne jusqu'a max_chars,
    et un recouvrement en caracteres entre deux chunks consecutifs pour
    ne pas couper une information a cheval sur une frontiere de chunk.

    Choix assume pour le MVP : decoupage par caracteres (simple, sans
    dependance a un tokenizer). Une version ulterieure pourra decouper
    par tokens si la precision du retrieval l'exige.
    """
    paragraphs = _split_paragraphs(doc.content)
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap < len(current) else current
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            # paragraphe seul deja plus long que max_chars : on le garde entier
            chunks.append(paragraph)
            current = ""

    if current:
        chunks.append(current)

    return [
        DocumentChunk(
            chunk_id=f"{doc.doc_id}::{i}",
            doc_id=doc.doc_id,
            category=doc.category,
            title=doc.title,
            source_file=doc.source_file,
            chunk_index=i,
            content=chunk_text,
        )
        for i, chunk_text in enumerate(chunks)
    ]

"""
PDF loading and chunking.

Chunks carry a `domain` tag derived from DOMAIN_MAP. That tag is what lets each
specialist agent filter retrieval to its own documents instead of every agent
searching one undifferentiated index - the difference between a real
multi-agent RAG system and one shared chatbot wearing five hats.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import asdict, dataclass

from pypdf import PdfReader

from backend import config

# Which agent owns which document. A document may serve several domains.
DOMAIN_MAP: dict[str, list[str]] = {
    "faq.pdf": ["faq"],
    "refund_policy.pdf": ["billing", "complaint"],
    "shipping_policy.pdf": ["product", "complaint", "faq"],
    "warranty.pdf": ["technical", "product"],
    "pricing.pdf": ["product", "billing"],
    "products.pdf": ["product"],
    "installation_guide.pdf": ["technical"],
    "user_manual.pdf": ["technical", "billing"],
}


@dataclass
class Chunk:
    id: str
    text: str
    source: str          # filename
    domains: list[str]   # which agents may retrieve this
    page: int
    chunk_index: int

    def to_dict(self) -> dict:
        return asdict(self)


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    # Rejoin words hyphenated across a line break
    text = re.sub(r"-\n(\w)", r"\1", text)
    # Drop the page footer we stamp on every KB page
    text = re.sub(r"TechMart Electronics - Internal Knowledge Base\s*Page \d+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def split_text(text: str, size: int, overlap: int) -> list[str]:
    """Paragraph-aware sliding window.

    Splitting on paragraph boundaries first keeps a policy clause intact instead
    of severing it mid-sentence, which is the single biggest cheap win for
    retrieval quality. Oversized paragraphs are hard-windowed as a backstop.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > size:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(para):
                chunks.append(para[start:start + size].strip())
                start += size - overlap
            continue
        if len(current) + len(para) + 1 <= size:
            current = f"{current} {para}".strip()
        else:
            chunks.append(current.strip())
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {para}".strip()
    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) > 60]  # drop stray headers


def load_pdf_chunks(path: pathlib.Path) -> list[Chunk]:
    reader = PdfReader(str(path))
    domains = DOMAIN_MAP.get(path.name, ["faq"])
    out: list[Chunk] = []
    counter = 0
    for page_no, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if not text:
            continue
        for piece in split_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
            out.append(Chunk(
                id=f"{path.stem}-p{page_no}-c{counter}",
                text=piece,
                source=path.name,
                domains=domains,
                page=page_no,
                chunk_index=counter,
            ))
            counter += 1
    return out


def load_all_chunks(kb_dir: pathlib.Path | None = None) -> list[Chunk]:
    kb_dir = kb_dir or config.KNOWLEDGE_BASE_DIR
    pdfs = sorted(kb_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"No PDFs in {kb_dir}. Run 'python scripts/build_kb.py' first."
        )
    chunks: list[Chunk] = []
    for pdf in pdfs:
        chunks.extend(load_pdf_chunks(pdf))
    return chunks

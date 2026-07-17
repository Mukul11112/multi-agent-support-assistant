"""
Renders knowledge_base/*.pdf from scripts/kb_content.py.

Run:  python scripts/build_kb.py
Then: python -m backend.rag.ingest   (to embed them into the vector store)
"""
import pathlib
import sys

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from kb_content import COMPANY, KB  # noqa: E402

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "knowledge_base"

styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "KBTitle", parent=styles["Title"], fontSize=20, spaceAfter=4, alignment=0
)
SUBTITLE = ParagraphStyle(
    "KBSubtitle", parent=styles["Normal"], fontSize=10, textColor="#666666", spaceAfter=16
)
HEADING = ParagraphStyle(
    "KBHeading", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6
)
BODY = ParagraphStyle(
    "KBBody", parent=styles["Normal"], fontSize=10.5, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=8,
)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor("#888888")
    canvas.drawString(20 * mm, 12 * mm, f"{COMPANY} - Internal Knowledge Base")
    canvas.drawRightString(190 * mm, 12 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_one(filename: str, spec: dict) -> pathlib.Path:
    path = OUT_DIR / filename
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title=spec["title"], author=COMPANY,
    )
    story = [
        Paragraph(spec["title"], TITLE),
        Paragraph(f"{COMPANY} &nbsp;|&nbsp; Document domain: {spec['domain']}", SUBTITLE),
    ]
    for heading, paragraphs in spec["sections"]:
        story.append(Paragraph(heading, HEADING))
        for para in paragraphs:
            story.append(Paragraph(para, BODY))
    story.append(Spacer(1, 6))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, spec in KB.items():
        path = build_one(filename, spec)
        print(f"  wrote {path.name}")
    print(f"\n{len(KB)} knowledge base PDFs written to {OUT_DIR}")


if __name__ == "__main__":
    main()

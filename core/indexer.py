from pathlib import Path
import fitz  # PyMuPDF

from core.database import SearchDatabase


def index_pdf_folder(folder, progress_callback=None):
    """Index text-based PDF files recursively. Returns (pdf_count, page_count, errors)."""
    db = SearchDatabase()
    pdf_count = 0
    page_count = 0
    errors = []

    for pdf_path in Path(folder).rglob("*.pdf"):
        try:
            document = fitz.open(pdf_path)
            db.remove_file(str(pdf_path.resolve()))
            indexed_any = False
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                if text:
                    db.replace_page(str(pdf_path.resolve()), page_number, text)
                    page_count += 1
                    indexed_any = True
                if progress_callback:
                    progress_callback(str(pdf_path.name), page_number, len(document))
            document.close()
            if indexed_any:
                pdf_count += 1
        except Exception as exc:
            errors.append(f"{pdf_path}: {exc}")

    return pdf_count, page_count, errors

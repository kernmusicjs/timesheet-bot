"""
Extract vendor, total TTC, and date from invoice files (PDF or image).
Uses pdfplumber for PDFs and pytesseract for images — no AI costs.
"""

import re
import io
from datetime import date


def extract_text(content: bytes, filename: str) -> str:
    """Extract raw text from a PDF or image file."""
    fname = filename.lower()
    if fname.endswith(".pdf"):
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                return "\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception as e:
            return f"[PDF extraction error: {e}]"
    else:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            return pytesseract.image_to_string(img, lang="fra+eng")
        except Exception as e:
            return f"[OCR error: {e}]"


def parse_invoice(text: str) -> dict:
    """
    Extract vendor, total TTC, and date from raw invoice text.
    Returns dict with keys: vendor, total (str), date (date|None).
    """
    # --- Total TTC ---
    total = None
    # Patterns: "Total TTC 42,50" / "TTC : 42.50 €" / "TOTAL TTC42,50€"
    patterns = [
        r'total\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'montant\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'net\s*à\s*payer\s*[:\-]?\s*(\d+[.,]\d{2})',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            total = m.group(1).replace(",", ".")
            break

    # --- Date ---
    invoice_date = None
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r'\b(\d{2})[/\-](\d{2})[/\-](\d{4})\b', text)
    if m:
        try:
            invoice_date = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    # YYYY-MM-DD
    if not invoice_date:
        m = re.search(r'\b(\d{4})[/\-](\d{2})[/\-](\d{2})\b', text)
        if m:
            try:
                invoice_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass

    # --- Vendor: first non-empty line that doesn't start with a digit ---
    vendor = None
    for line in text.split("\n"):
        line = line.strip()
        if len(line) > 2 and not re.match(r'^\d', line) and not re.match(r'^[^\w]', line):
            vendor = line[:40]
            break

    return {"vendor": vendor, "total": total, "date": invoice_date}


def parse_manual_correction(text: str) -> dict:
    """
    Parse a manual correction reply from the user.
    Format: "Vendor, total, DD/MM" or "Vendor, total, DD/MM/YYYY"
    Returns dict with vendor, total, date (date|None).
    """
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 2:
        return {}

    vendor = parts[0] if parts[0] else None
    total = parts[1].replace("€", "").replace("EUR", "").strip() if len(parts) > 1 else None

    invoice_date = None
    if len(parts) > 2:
        date_str = parts[2].strip()
        m = re.match(r'^(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{4}))?$', date_str)
        if m:
            day, month = int(m.group(1)), int(m.group(2))
            year = int(m.group(3)) if m.group(3) else date.today().year
            try:
                invoice_date = date(year, month, day)
            except ValueError:
                pass

    return {"vendor": vendor, "total": total, "date": invoice_date}

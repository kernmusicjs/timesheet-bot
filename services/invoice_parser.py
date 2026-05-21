"""
Extract vendor, total TTC, and date from invoice files (PDF or image).
100% regex-based with vendor signature database + correction-based learning.
"""

import re
import io
import os
import json
from datetime import date, datetime


# Section-header tokens that disqualify a "vendor" candidate
BAD_VENDOR_TOKENS = [
    "détail", "detail", "facture", "invoice", "commande", "order",
    "récapitulatif", "recapitulatif", "récap", "recap", "client",
    "livraison", "adresse", "page", "ticket", "reçu", "recu",
    "numéro", "numero", "référence", "reference", "bon de",
]

# Built-in vendor signatures: brand name → list of tokens to search (case-insensitive)
VENDOR_SIGNATURES = {
    "Amazon": ["amazon.fr", "amazon.com", "amazon eu", "amzn", "amazon europe"],
    "Leclerc": ["leclerc", "e.leclerc", "scamark"],
    "Fnac": ["fnac.com", "fnac darty", "fnac.fr"],
    "Carrefour": ["carrefour.fr", "carrefour market", "carrefour hyper", "carrefour drive"],
    "Auchan": ["auchan.fr", "auchan retail", "auchan hyper"],
    "Cdiscount": ["cdiscount.com", "cdiscount.fr"],
    "Decathlon": ["decathlon.fr", "decathlon.com"],
    "Action": ["action.fr", "action france"],
    "Boulanger": ["boulanger.com", "boulanger.fr"],
    "Darty": ["darty.com", "darty.fr"],
    "IKEA": ["ikea.fr", "ikea.com"],
    "Castorama": ["castorama.fr"],
    "Leroy Merlin": ["leroymerlin.fr", "leroy merlin"],
    "Brico Dépôt": ["bricodepot.fr", "brico dépôt", "brico depot"],
}

FRENCH_MONTHS_LOOKUP = {
    "janvier": 1, "janv": 1, "février": 2, "fevrier": 2, "févr": 2, "fevr": 2,
    "mars": 3, "avril": 4, "avr": 4, "mai": 5, "juin": 6, "juillet": 7, "juil": 7,
    "août": 8, "aout": 8, "septembre": 9, "sept": 9, "octobre": 10, "oct": 10,
    "novembre": 11, "nov": 11, "décembre": 12, "decembre": 12, "déc": 12, "dec": 12,
}

CORRECTIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "corrections.json")


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


def _load_corrections() -> list:
    try:
        with open(CORRECTIONS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _all_signatures() -> dict:
    """Merge built-in signatures with learned corrections."""
    merged = {k: list(v) for k, v in VENDOR_SIGNATURES.items()}
    for entry in _load_corrections():
        vendor = entry.get("vendor")
        sigs = entry.get("signatures", [])
        if not vendor or not sigs:
            continue
        merged.setdefault(vendor, [])
        for s in sigs:
            if s and s.lower() not in [x.lower() for x in merged[vendor]]:
                merged[vendor].append(s)
    return merged


def _detect_vendor_signature(text: str) -> str | None:
    """Return brand name if a known signature is found in text."""
    text_lower = text.lower()
    for vendor, tokens in _all_signatures().items():
        for tok in tokens:
            if tok.lower() in text_lower:
                return vendor
    return None


def _extract_signatures_from_text(text: str) -> list:
    """Pull domain-like and URL-like tokens from text — candidates for learning."""
    candidates = set()
    for m in re.finditer(r'\b([a-zA-Z0-9][a-zA-Z0-9\-]{1,30}\.(?:fr|com|net|eu|de|be|ch))\b', text):
        candidates.add(m.group(1).lower())
    return list(candidates)[:5]


def _parse_order_date(text: str) -> date | None:
    """Look for explicit order/command date patterns. Returns date or None."""
    # Pattern: "Commandé le 22 septembre 2025"
    m = re.search(
        r'command[ée]\s*le\s*(\d{1,2})\s+([a-zéûôàè]+)\s+(\d{4})',
        text, re.IGNORECASE
    )
    if m:
        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        month = FRENCH_MONTHS_LOOKUP.get(month_name)
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # Numeric order-date patterns
    for pat in [
        r'date\s*de\s*(?:la\s*)?commande\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'commande\s*effectuée\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'order\s*date\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'order\s*placed\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass

    return None


def _all_dates_in_text(text: str) -> list:
    """Find all dates in text (DD/MM/YYYY or 'DD MOIS YYYY'). Return sorted oldest-first."""
    found = []
    for m in re.finditer(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b', text):
        try:
            found.append(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
        except ValueError:
            pass
    for m in re.finditer(r'\b(\d{1,2})\s+([a-zéûôàè]+)\s+(\d{4})\b', text, re.IGNORECASE):
        month = FRENCH_MONTHS_LOOKUP.get(m.group(2).lower())
        if month:
            try:
                found.append(date(int(m.group(3)), month, int(m.group(1))))
            except ValueError:
                pass
    return sorted(set(found))


def _parse_fallback_date(text: str, prefer_oldest: bool = False) -> date | None:
    """Fallback: pick oldest date if vendor known (likely order date), else first."""
    dates = _all_dates_in_text(text)
    if not dates:
        return None
    if prefer_oldest:
        return dates[0]
    m = re.search(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b', text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass
    return dates[0]


def _heuristic_vendor(text: str) -> str | None:
    """Last-resort vendor: first non-empty line that doesn't look like a header."""
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 3 or re.match(r'^\d', line) or re.match(r'^[^\w]', line):
            continue
        if any(tok in line.lower() for tok in BAD_VENDOR_TOKENS):
            continue
        if re.search(r'\d{2}[/\-]\d{2}', line) or re.search(r'\d{4}', line):
            continue
        return line[:40]
    return None


def parse_invoice(text: str) -> dict:
    """
    Extract vendor/total/date with regex + vendor signatures.
    Returns dict: vendor, total (str|None), date (date|None),
                  vendor_confidence ('signature'|'heuristic'|None),
                  date_confidence ('order'|'fallback'|None).
    """
    # --- Total TTC ---
    total = None
    for pat in [
        r'total\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'montant\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'total\s*[àa]\s*payer\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'net\s*[àa]\s*payer\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'facture\s*total\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'total\s*facture\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            total = m.group(1).replace(",", ".")
            break

    # --- Vendor ---
    vendor = _detect_vendor_signature(text)
    vendor_confidence = "signature" if vendor else None
    if not vendor:
        vendor = _heuristic_vendor(text)
        vendor_confidence = "heuristic" if vendor else None

    # --- Date ---
    invoice_date = _parse_order_date(text)
    date_confidence = "order" if invoice_date else None
    if not invoice_date:
        # When vendor is known via signature, prefer oldest date (order > edition)
        prefer_oldest = vendor_confidence == "signature"
        invoice_date = _parse_fallback_date(text, prefer_oldest=prefer_oldest)
        date_confidence = "oldest" if prefer_oldest and invoice_date else ("fallback" if invoice_date else None)

    return {
        "vendor": vendor,
        "total": total,
        "date": invoice_date,
        "vendor_confidence": vendor_confidence,
        "date_confidence": date_confidence,
    }


def save_correction(raw_text: str, vendor: str, total: str, invoice_date) -> None:
    """Persist a manual correction with extracted signatures for future auto-detection."""
    os.makedirs(os.path.dirname(CORRECTIONS_PATH), exist_ok=True)
    corrections = _load_corrections()

    signatures = _extract_signatures_from_text(raw_text)
    raw_hint = ""
    for line in raw_text.split("\n"):
        line = line.strip()
        if len(line) > 3 and not re.match(r'^\d', line):
            raw_hint = line[:60]
            break

    corrections.append({
        "vendor": vendor,
        "signatures": signatures,
        "raw_hint": raw_hint,
        "total": total,
        "date": invoice_date.isoformat() if invoice_date else None,
        "corrected_at": date.today().isoformat(),
    })
    corrections = corrections[-100:]

    with open(CORRECTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(corrections, f, ensure_ascii=False, indent=2)


def parse_manual_correction(text: str) -> dict:
    """
    Parse a manual correction reply from the user.
    Format: "Vendor, total, DD/MM" or "Vendor, total, DD/MM/YYYY"
    """
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 2:
        return {}

    vendor = parts[0] if parts[0] else None
    total = parts[1].replace("€", "").replace("EUR", "").strip() if len(parts) > 1 else None

    invoice_date = None
    if len(parts) > 2:
        date_str = parts[2].strip()
        m = re.match(r'^(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?$', date_str)
        if m:
            day, month = int(m.group(1)), int(m.group(2))
            year_raw = m.group(3)
            if year_raw:
                year = int(year_raw)
                if year < 100:
                    year += 2000
            else:
                year = date.today().year
            try:
                invoice_date = date(year, month, day)
            except ValueError:
                pass

    return {"vendor": vendor, "total": total, "date": invoice_date}

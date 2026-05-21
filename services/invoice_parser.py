"""
Extract vendor, total TTC, and date from invoice files (PDF or image).
Hybrid approach: regex first (free), Claude Haiku fallback when low confidence.
"""

import re
import io
import os
import json
from datetime import date, datetime


# Words that indicate the "vendor" line is actually a header/section title, not a brand
BAD_VENDOR_TOKENS = [
    "détail", "detail", "facture", "invoice", "commande", "order",
    "récapitulatif", "recapitulatif", "récap", "recap", "client",
    "livraison", "adresse", "page", "ticket", "reçu", "recu",
    "numéro", "numero", "référence", "reference", "bon de",
]


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


def _parse_regex(text: str) -> dict:
    """Best-effort regex extraction. May return partial/wrong results."""
    total = None
    for pat in [
        r'total\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'montant\s*ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'net\s*à\s*payer\s*[:\-]?\s*(\d+[.,]\d{2})',
        r'ttc\s*[:\-]?\s*(\d+[.,]\d{2})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            total = m.group(1).replace(",", ".")
            break

    invoice_date = None
    # Order date priority
    for pat in [
        r'command[ée]\s*le\s*[:\-]?\s*(\d{1,2})[/\-\s]+(\d{1,2}|janv|févr|fevr|mars|avril|mai|juin|juil|août|aout|sept|oct|nov|déc|dec)[/\-\s]+(\d{4})',
        r'date\s*de\s*commande\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'commande\s*effectuée\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
        r'order\s*date\s*[:\-]?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})',
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                invoice_date = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                break
            except (ValueError, IndexError):
                pass

    if not invoice_date:
        m = re.search(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b', text)
        if m:
            try:
                invoice_date = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass

    vendor = None
    for line in text.split("\n"):
        line = line.strip()
        if len(line) > 2 and not re.match(r'^\d', line) and not re.match(r'^[^\w]', line):
            vendor = line[:40]
            break

    return {"vendor": vendor, "total": total, "date": invoice_date}


def _confidence_low(result: dict, text: str) -> bool:
    """Return True if regex result looks unreliable."""
    if not result.get("total") or not result.get("date") or not result.get("vendor"):
        return True
    v = (result["vendor"] or "").lower()
    if any(tok in v for tok in BAD_VENDOR_TOKENS):
        return True
    # Vendor contains digits or dates → likely a header
    if re.search(r'\d{2}[/\-]\d{2}', v) or re.search(r'\d{4}', v):
        return True
    if len(v.strip()) < 3:
        return True
    return False


def _parse_with_ai(text: str) -> dict | None:
    """Call Gemini Flash to extract structured invoice data. Returns None on failure."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        snippet = text[:4000]
        prompt = (
            "Extrait du texte brut d'une facture les informations suivantes et réponds UNIQUEMENT en JSON valide (pas de markdown, pas de texte autour) :\n"
            "- vendor: le nom du commerçant/marque (Amazon, Leclerc, Fnac, etc.) — pas un titre de section\n"
            "- total: le montant TOTAL TTC en euros, format '42.50' (point décimal, pas de symbole)\n"
            "- date: la date de COMMANDE/ACHAT (pas la date d'édition/impression de la facture) au format YYYY-MM-DD\n\n"
            "Si une info est introuvable, mets null. Texte de la facture :\n\n"
            f"{snippet}\n\n"
            'Réponds uniquement avec : {"vendor": "...", "total": "...", "date": "YYYY-MM-DD"}'
        )
        resp = model.generate_content(prompt)
        raw = resp.text.strip()
        # Strip possible code fences
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        parsed_date = None
        if data.get("date"):
            try:
                parsed_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except ValueError:
                pass
        return {
            "vendor": data.get("vendor"),
            "total": str(data["total"]) if data.get("total") is not None else None,
            "date": parsed_date,
        }
    except Exception as e:
        print(f"[invoice_parser] Gemini fallback failed: {e}", flush=True)
        return None


def parse_invoice(text: str) -> dict:
    """
    Hybrid extraction: regex first, Claude Haiku fallback if confidence is low.
    Returns dict with keys: vendor, total (str), date (date|None), source ('regex'|'haiku').
    """
    regex_result = _parse_regex(text)
    if not _confidence_low(regex_result, text):
        regex_result["source"] = "regex"
        return regex_result

    ai_result = _parse_with_ai(text)
    if ai_result:
        merged = {
            "vendor": ai_result.get("vendor") or regex_result.get("vendor"),
            "total": ai_result.get("total") or regex_result.get("total"),
            "date": ai_result.get("date") or regex_result.get("date"),
            "source": "gemini",
        }
        return merged

    regex_result["source"] = "regex"
    return regex_result


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

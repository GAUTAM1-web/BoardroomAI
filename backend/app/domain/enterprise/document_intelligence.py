from __future__ import annotations

import base64
import binascii
import hashlib
import io
import re
import zipfile
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any
from uuid import uuid4

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log"}
ZIP_DOCUMENT_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
RISK_TERMS = {
    "breach",
    "cash",
    "compliance",
    "debt",
    "delay",
    "dependency",
    "decline",
    "lawsuit",
    "liability",
    "risk",
    "shortage",
}
OPPORTUNITY_TERMS = {
    "demand",
    "expansion",
    "growth",
    "margin",
    "opportunity",
    "partnership",
    "pilot",
    "revenue",
    "savings",
}
CLASSIFICATION_TERMS = {
    "financial": {"budget", "cash", "cost", "expense", "margin", "revenue"},
    "legal_compliance": {"agreement", "compliance", "contract", "license", "policy"},
    "market_research": {"competitor", "customer", "demand", "market", "survey"},
    "operations": {"inventory", "logistics", "process", "supplier", "workflow"},
    "proposal": {"recommendation", "proposal", "roadmap", "strategy", "summary"},
}


def analyze_document_import(payload: dict[str, Any]) -> dict[str, Any]:
    filename = str(payload["filename"]).strip()
    raw_bytes = _decode_content(str(payload["content_base64"]))
    extension = Path(filename).suffix.lower()
    mime_type = payload.get("mime_type")
    now = datetime.now(UTC)
    warnings: list[str] = []
    text = ""
    extraction_status = "metadata_only"

    if extension in TEXT_EXTENSIONS:
        text = _decode_text(raw_bytes)
        extraction_status = "text_extracted" if text else "metadata_only"
    elif extension in ZIP_DOCUMENT_EXTENSIONS:
        text = _extract_zip_document_text(raw_bytes, extension)
        extraction_status = "text_extracted" if text else "metadata_only"
        if not text:
            warnings.append("No readable office-document text was found in the uploaded file.")
    elif extension == ".pdf":
        text = _extract_pdf_text(raw_bytes)
        extraction_status = "partial_text_extracted" if text else "metadata_only"
        if not text:
            warnings.append("PDF text extraction found no readable text in the local parser.")
    elif extension in IMAGE_EXTENSIONS or (mime_type and str(mime_type).startswith("image/")):
        warnings.append("Image OCR is not configured; only file metadata was indexed.")
    else:
        text = _decode_text(raw_bytes)
        extraction_status = "text_extracted" if text else "metadata_only"
        if not text:
            warnings.append("File type is unsupported for text extraction in the local parser.")

    normalized_text = _collapse(text)
    summary = _summary(normalized_text)
    risks = _matching_sentences(normalized_text, RISK_TERMS)
    opportunities = _matching_sentences(normalized_text, OPPORTUNITY_TERMS)
    classification = _classify(normalized_text, filename)
    associations = {
        "meeting_id": str(payload["meeting_id"]) if payload.get("meeting_id") else None,
        "business_analysis_id": (
            str(payload["business_analysis_id"]) if payload.get("business_analysis_id") else None
        ),
    }

    return {
        "id": str(uuid4()),
        "filename": filename,
        "mime_type": mime_type,
        "file_type": extension.lstrip(".") or "unknown",
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "size_bytes": len(raw_bytes),
        "extraction_status": extraction_status,
        "summary": summary,
        "classification": classification,
        "risks": risks,
        "opportunities": opportunities,
        "associations": associations,
        "evidence_records": _evidence_records(filename, summary, normalized_text, now),
        "tags": _tags(payload.get("tags"), classification, risks, opportunities),
        "warnings": warnings,
        "word_count": len(normalized_text.split()) if normalized_text else 0,
        "character_count": len(normalized_text),
        "extracted_text": normalized_text[:20000],
        "created_at": now.isoformat(),
    }


def _decode_content(value: str) -> bytes:
    content = value.strip()
    if "," in content and content[:80].lower().find("base64") != -1:
        content = content.split(",", 1)[1]
    try:
        return base64.b64decode(content, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Uploaded document content must be valid base64.") from exc


def _decode_text(raw_bytes: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            decoded = raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded.strip():
            return decoded
    return ""


def _extract_zip_document_text(raw_bytes: bytes, extension: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
            if extension == ".docx":
                names = [
                    name
                    for name in archive.namelist()
                    if name.startswith("word/") and name.endswith(".xml")
                ]
            elif extension == ".pptx":
                names = [
                    name
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                ]
            else:
                names = [
                    name
                    for name in archive.namelist()
                    if name == "xl/sharedStrings.xml"
                    or (name.startswith("xl/worksheets/") and name.endswith(".xml"))
                ]
            return _collapse(" ".join(_xml_text(archive.read(name)) for name in sorted(names)))
    except (zipfile.BadZipFile, KeyError, OSError):
        return ""


def _extract_pdf_text(raw_bytes: bytes) -> str:
    raw = raw_bytes.decode("latin-1", errors="ignore")
    tokens = re.findall(r"\(([^()]{3,300})\)\s*Tj", raw)
    tokens.extend(re.findall(r"\(([^()]{3,300})\)", raw[:250000]))
    printable = [
        _collapse(token.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\"))
        for token in tokens
    ]
    return _collapse(" ".join(item for item in printable if item and not item.startswith("/")))


def _xml_text(raw_bytes: bytes) -> str:
    text = raw_bytes.decode("utf-8", errors="ignore")
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(text)


def _summary(text: str) -> str:
    if not text:
        return "No extractable text was found; document metadata was recorded for governance."
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    return _collapse(" ".join(sentences[:3]))[:700]


def _matching_sentences(text: str, terms: set[str]) -> list[str]:
    if not text:
        return []
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
    matches = []
    for sentence in sentences:
        normalized = sentence.lower()
        if any(term in normalized for term in terms):
            matches.append(sentence[:360])
        if len(matches) == 5:
            break
    return matches


def _classify(text: str, filename: str) -> str:
    haystack = f"{filename} {text}".lower()
    scores = {
        label: sum(1 for term in terms if term in haystack)
        for label, terms in CLASSIFICATION_TERMS.items()
    }
    label, score = max(scores.items(), key=lambda item: item[1])
    return label if score else "general_business_document"


def _evidence_records(
    filename: str,
    summary: str,
    text: str,
    retrieval_time: datetime,
) -> list[dict[str, Any]]:
    if not text:
        return [
            {
                "claim": f"{filename} was uploaded, but no text was extracted locally.",
                "source_name": filename,
                "source_type": "user_uploaded_document",
                "source_category": "user_provided_information",
                "retrieval_time": retrieval_time.isoformat(),
                "confidence": "High",
                "verification_status": "metadata_only",
                "freshness": "current_upload",
                "tags": ["document", "metadata"],
            }
        ]
    return [
        {
            "claim": summary,
            "source_name": filename,
            "source_type": "user_uploaded_document",
            "source_category": "user_provided_information",
            "retrieval_time": retrieval_time.isoformat(),
            "confidence": "Medium",
            "verification_status": "extracted_from_upload",
            "freshness": "current_upload",
            "tags": ["document", "extracted_text"],
        }
    ]


def _tags(
    supplied: object,
    classification: str,
    risks: list[str],
    opportunities: list[str],
) -> list[str]:
    tags = [str(item).strip().lower() for item in supplied or [] if str(item).strip()]
    tags.extend(["document", classification])
    if risks:
        tags.append("risk")
    if opportunities:
        tags.append("opportunity")
    return sorted(set(tags))


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

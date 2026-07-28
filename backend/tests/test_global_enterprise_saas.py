from __future__ import annotations

import base64
import io
import zipfile

import pytest

from app.domain.enterprise.document_intelligence import analyze_document_import
from app.domain.enterprise.saas_intelligence import build_assistant_answer


def test_document_import_extracts_text_and_evidence_labels() -> None:
    content = (
        "Revenue growth is strong. Compliance risk remains open. "
        "Supplier partnership creates margin opportunity."
    )
    result = analyze_document_import(
        {
            "filename": "board-summary.txt",
            "content_base64": base64.b64encode(content.encode()).decode(),
            "mime_type": "text/plain",
            "tags": ["Board"],
        }
    )

    assert result["extraction_status"] == "text_extracted"
    assert result["classification"] in {"financial", "legal_compliance", "operations"}
    assert result["risks"]
    assert result["opportunities"]
    assert result["evidence_records"][0]["source_category"] == "user_provided_information"


def test_document_import_extracts_docx_xml_text() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        document_xml = (
            "<w:document><w:body><w:t>Market demand supports expansion.</w:t>"
            "</w:body></w:document>"
        )
        archive.writestr(
            "word/document.xml",
            document_xml,
        )

    result = analyze_document_import(
        {
            "filename": "market-note.docx",
            "content_base64": base64.b64encode(buffer.getvalue()).decode(),
            "mime_type": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            "tags": [],
        }
    )

    assert result["extraction_status"] == "text_extracted"
    assert "Market demand supports expansion" in result["summary"]


def test_document_import_does_not_fabricate_image_ocr() -> None:
    result = analyze_document_import(
        {
            "filename": "site-photo.png",
            "content_base64": base64.b64encode(b"\x89PNG\r\n\x1a\n").decode(),
            "mime_type": "image/png",
            "tags": [],
        }
    )

    assert result["extraction_status"] == "metadata_only"
    assert result["word_count"] == 0
    assert "OCR is not configured" in result["warnings"][0]


def test_document_import_rejects_invalid_base64() -> None:
    with pytest.raises(ValueError, match="valid base64"):
        analyze_document_import(
            {
                "filename": "broken.txt",
                "content_base64": "not base64",
                "mime_type": "text/plain",
                "tags": [],
            }
        )


def test_assistant_answer_is_grounded_in_search_sources() -> None:
    answer = build_assistant_answer(
        "show risk",
        {
            "collections": {
                "meetings": [{"meeting_id": "m1", "startup_idea": "Clinic AI"}],
                "tasks": [],
            }
        },
        {"executive_memory": [{"role": "CEO"}]},
        {"meeting_effectiveness": {"total_meetings": 1}},
    )

    assert answer["source_count"] == 1
    assert answer["sources"][0]["collection"] == "meetings"
    assert "risk" in " ".join(answer["recommended_actions"]).lower()

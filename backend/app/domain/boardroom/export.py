from __future__ import annotations

import json
import textwrap
from typing import Any


def report_to_markdown(meeting: dict[str, Any]) -> str:
    report = meeting["report"]
    brief = meeting.get("startup_brief", {})
    lines = [
        f"# {report['title']}",
        "",
        f"**Decision:** {_title(report['decision'])}",
        f"**Confidence:** {round(float(meeting['aggregate_confidence']) * 100)}%",
        f"**Industry:** {brief.get('industry', 'Unknown')}",
        f"**Country:** {brief.get('country', 'Unknown')}",
        "",
    ]

    for section_key, content in report["sections"].items():
        lines.extend([f"## {_title(section_key)}", "", _markdown_value(content), ""])

    return "\n".join(lines).strip() + "\n"


def report_to_json(meeting: dict[str, Any]) -> str:
    return json.dumps(meeting, indent=2, sort_keys=True, default=str)


def report_to_pdf(meeting: dict[str, Any]) -> bytes:
    report = meeting["report"]
    brief = meeting.get("startup_brief", {})
    pages: list[list[PdfLine]] = [
        [
            PdfLine("BOARDROOM AI", 10, "muted"),
            PdfLine(report["title"], 24, "heading"),
            PdfLine(f"Decision: {_title(report['decision'])}", 14, "body"),
            PdfLine(
                f"Confidence: {round(float(meeting['aggregate_confidence']) * 100)}%",
                14,
                "body",
            ),
            PdfLine(f"Industry: {brief.get('industry', 'Unknown')}", 12, "body"),
            PdfLine(f"Country: {brief.get('country', 'Unknown')}", 12, "body"),
        ]
    ]

    toc_lines = [PdfLine("Table of Contents", 18, "heading")]
    for index, section_key in enumerate(report["sections"], start=1):
        toc_lines.append(PdfLine(f"{index}. {_title(section_key)}", 11, "body"))
    pages.append(toc_lines)

    for section_key, content in report["sections"].items():
        section_lines = [PdfLine(_title(section_key), 17, "heading")]
        for line in _plain_lines(content):
            section_lines.append(PdfLine(line, 10, "body"))
        pages.extend(_paginate(section_lines))

    return _write_pdf(pages, title=report["title"])


class PdfLine:
    def __init__(self, text: str, size: int, style: str) -> None:
        self.text = _ascii(text)
        self.size = size
        self.style = style


def _paginate(lines: list[PdfLine], max_body_lines: int = 42) -> list[list[PdfLine]]:
    pages: list[list[PdfLine]] = []
    current: list[PdfLine] = []
    body_count = 0
    for line in lines:
        if body_count >= max_body_lines and line.size <= 12:
            pages.append(current)
            current = []
            body_count = 0
        current.append(line)
        body_count += 2 if line.size > 14 else 1
    if current:
        pages.append(current)
    return pages


def _write_pdf(pages: list[list[PdfLine]], title: str) -> bytes:
    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    page_ids: list[int] = []

    for page_number, lines in enumerate(pages, start=1):
        content = _page_content(lines, page_number, len(pages), title)
        content_id = add_object(
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1")
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("latin-1")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "latin-1"
    )
    assert catalog_id == 1

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode("latin-1"))
        output.extend(payload)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )
    return bytes(output)


def _page_content(
    lines: list[PdfLine],
    page_number: int,
    total_pages: int,
    title: str,
) -> bytes:
    commands = [
        "0.04 0.05 0.07 rg",
        "0 0 595 842 re",
        "f",
        "0.82 0.87 0.92 rg",
        "BT /F2 9 Tf 48 808 Td (BOARDROOM AI) Tj ET",
        f"BT /F1 8 Tf 420 808 Td ({_pdf_escape(_ascii(title[:42]))}) Tj ET",
        "0.22 0.84 0.78 rg",
        "48 790 499 1.2 re",
        "f",
    ]
    y = 750
    for line in lines:
        font = "F2" if line.style == "heading" else "F1"
        color = "0.98 0.98 1 rg" if line.style == "heading" else "0.82 0.87 0.92 rg"
        if line.style == "muted":
            color = "0.55 0.60 0.66 rg"
        commands.append(color)
        for wrapped in _wrap_pdf_line(line.text, line.size):
            commands.append(
                f"BT /{font} {line.size} Tf 48 {y} Td ({_pdf_escape(wrapped)}) Tj ET"
            )
            y -= max(line.size + 6, 14)
            if y < 78:
                break
        y -= 4 if line.size >= 14 else 0
        if y < 78:
            break
    commands.extend(
        [
            "0.55 0.60 0.66 rg",
            "48 48 499 1 re",
            "f",
            "BT /F1 8 Tf 48 34 Td (Investor-grade board report) Tj ET",
            f"BT /F1 8 Tf 492 34 Td (Page {page_number} of {total_pages}) Tj ET",
        ]
    )
    return "\n".join(commands).encode("latin-1", errors="replace")


def _wrap_pdf_line(text: str, size: int) -> list[str]:
    width = 45 if size >= 18 else 78
    if not text:
        return [""]
    return textwrap.wrap(text, width=width, replace_whitespace=True) or [text]


def _plain_lines(value: Any, prefix: str = "") -> list[str]:
    if value is None:
        return [f"{prefix}Unavailable"]
    if isinstance(value, (str, int, float, bool)):
        return textwrap.wrap(f"{prefix}{value}", width=96) or [f"{prefix}{value}"]
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            lines.extend(_plain_lines(item, prefix="- "))
        return lines
    if isinstance(value, dict):
        lines = []
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                lines.append(f"{prefix}{_title(str(key))}:")
                lines.extend(_plain_lines(nested, prefix="  "))
            else:
                lines.extend(_plain_lines(nested, prefix=f"{prefix}{_title(str(key))}: "))
        return lines
    return [f"{prefix}{value}"]


def _markdown_value(value: Any, depth: int = 0) -> str:
    if value is None:
        return "_Unavailable_"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(f"- {_markdown_value(item, depth + 1)}" for item in value)
    if isinstance(value, dict):
        lines = []
        for key, nested in value.items():
            rendered = _markdown_value(nested, depth + 1)
            if "\n" in rendered:
                lines.append(f"**{_title(str(key))}:**\n{rendered}")
            else:
                lines.append(f"**{_title(str(key))}:** {rendered}")
        return "\n\n".join(lines)
    return str(value)


def _title(value: str) -> str:
    return value.replace("_", " ").title().replace("Ai", "AI").replace("Vc", "VC")


def _ascii(value: str) -> str:
    return value.encode("ascii", errors="ignore").decode("ascii")


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

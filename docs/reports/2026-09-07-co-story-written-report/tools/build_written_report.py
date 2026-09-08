#!/usr/bin/env python3
"""Build the Co-Story final written report DOCX from the Markdown manuscript."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from PIL import Image
from lxml import etree
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


BODY_FONT = "Arial Unicode MS"
HEADING_FONT = "Arial Unicode MS"
MONO_FONT = "Liberation Mono"
EMBED_FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
)

CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
FONT_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _obfuscate_openxml_font(font_data: bytes, font_key: uuid.UUID) -> bytes:
    """Apply ECMA-376 embedded-font obfuscation to the first 32 bytes."""
    data = bytearray(font_data)
    key = font_key.bytes[::-1]
    for index in range(min(32, len(data))):
        data[index] ^= key[index % 16]
    return bytes(data)


def embed_cjk_font(docx_path: Path) -> None:
    """Embed the editable-installable CJK font so headless LibreOffice is portable."""
    font_path = next((path for path in EMBED_FONT_CANDIDATES if path.is_file()), None)
    if font_path is None:
        raise FileNotFoundError("Arial Unicode MS was not found; refusing a non-portable DOCX build")

    # Match LibreOffice's OOXML exporter keys and byte order exactly. Writer
    # requires both faces here even though the source file is the same font.
    regular_key = uuid.UUID("01014a78-cabc-4ef0-12ac-5cd89aefde01")
    bold_key = uuid.UUID("02014a78-cabc-4ef0-12ac-5cd89aefde02")
    font_data = font_path.read_bytes()
    embedded_regular = _obfuscate_openxml_font(font_data, regular_key)
    embedded_bold = _obfuscate_openxml_font(font_data, bold_key)
    temporary = docx_path.with_suffix(".embedded.tmp.docx")

    with zipfile.ZipFile(docx_path, "r") as source, zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED
    ) as target:
        entries = {name: source.read(name) for name in source.namelist()}

        font_table = etree.fromstring(entries["word/fontTable.xml"])
        font = etree.SubElement(font_table, f"{{{WORD_NS}}}font")
        font.set(f"{{{WORD_NS}}}name", BODY_FONT)
        charset = etree.SubElement(font, f"{{{WORD_NS}}}charset")
        charset.set(f"{{{WORD_NS}}}val", "01")
        family = etree.SubElement(font, f"{{{WORD_NS}}}family")
        family.set(f"{{{WORD_NS}}}val", "roman")
        pitch = etree.SubElement(font, f"{{{WORD_NS}}}pitch")
        pitch.set(f"{{{WORD_NS}}}val", "variable")
        for element_name, relationship_id, font_key in (
            ("embedRegular", "rId1", regular_key),
            ("embedBold", "rId2", bold_key),
        ):
            embed = etree.SubElement(font, f"{{{WORD_NS}}}{element_name}")
            embed.set(f"{{{OFFICE_REL_NS}}}id", relationship_id)
            embed.set(f"{{{WORD_NS}}}fontKey", "{" + str(font_key).upper() + "}")
        entries["word/fontTable.xml"] = etree.tostring(
            font_table, xml_declaration=True, encoding="UTF-8", standalone=True
        )

        rels_name = "word/_rels/fontTable.xml.rels"
        if rels_name in entries:
            relationships = etree.fromstring(entries[rels_name])
        else:
            relationships = etree.Element(f"{{{RELATIONSHIPS_NS}}}Relationships")
        for relationship_id, target_name in (
            ("rId1", "fonts/font1.odttf"),
            ("rId2", "fonts/font2.odttf"),
        ):
            relationship = etree.SubElement(
                relationships, f"{{{RELATIONSHIPS_NS}}}Relationship"
            )
            relationship.set("Id", relationship_id)
            relationship.set("Type", FONT_REL_TYPE)
            relationship.set("Target", target_name)
        entries[rels_name] = etree.tostring(
            relationships, xml_declaration=True, encoding="UTF-8", standalone=True
        )

        content_types = etree.fromstring(entries["[Content_Types].xml"])
        if not content_types.xpath(
            "ct:Default[@Extension='odttf']", namespaces={"ct": CONTENT_TYPES_NS}
        ):
            default = etree.SubElement(content_types, f"{{{CONTENT_TYPES_NS}}}Default")
            default.set("Extension", "odttf")
            default.set(
                "ContentType",
                "application/vnd.openxmlformats-officedocument.obfuscatedFont",
            )
        entries["[Content_Types].xml"] = etree.tostring(
            content_types, xml_declaration=True, encoding="UTF-8", standalone=True
        )

        settings = etree.fromstring(entries["word/settings.xml"])
        for local_name in ("embedTrueTypeFonts", "embedSystemFonts"):
            node = settings.find(f"{{{WORD_NS}}}{local_name}")
            if node is None:
                node = etree.SubElement(settings, f"{{{WORD_NS}}}{local_name}")
            node.set(f"{{{WORD_NS}}}val", "true")
        entries["word/settings.xml"] = etree.tostring(
            settings, xml_declaration=True, encoding="UTF-8", standalone=True
        )
        entries["word/fonts/font1.odttf"] = embedded_regular
        entries["word/fonts/font2.odttf"] = embedded_bold

        for name, data in entries.items():
            target.writestr(name, data)

    temporary.replace(docx_path)


def _find_soffice() -> Path:
    candidates = [
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice",
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
    ]
    command = shutil.which("soffice")
    if command:
        candidates.insert(0, Path(command))
    executable = next((path for path in candidates if path.is_file()), None)
    if executable is None:
        raise FileNotFoundError("LibreOffice soffice was not found; refusing an unverified DOCX build")
    return executable


def roundtrip_embedded_fonts_with_libreoffice(docx_path: Path) -> None:
    """Let LibreOffice normalize the embedded faces it later consumes in QA."""
    soffice = _find_soffice()
    runtime_fonts = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/"
        "libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/"
        "fonts/truetype"
    )
    font_dirs = [EMBED_FONT_CANDIDATES[0].parent]
    if runtime_fonts.is_dir():
        font_dirs.append(runtime_fonts)

    with tempfile.TemporaryDirectory(prefix="co-story-docx-fonts-") as temp_name:
        temp_dir = Path(temp_name)
        output_dir = temp_dir / "output"
        profile_dir = temp_dir / "profile"
        cache_dir = temp_dir / "font-cache"
        output_dir.mkdir()
        profile_dir.mkdir()
        cache_dir.mkdir()
        font_config = temp_dir / "fonts.conf"
        dirs_xml = "\n".join(f"  <dir>{path}</dir>" for path in font_dirs)
        font_config.write_text(
            '<?xml version="1.0"?>\n'
            '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
            '<fontconfig>\n'
            f"{dirs_xml}\n"
            f"  <cachedir>{cache_dir}</cachedir>\n"
            '</fontconfig>\n',
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["FONTCONFIG_FILE"] = str(font_config)
        completed = subprocess.run(
            [
                str(soffice),
                f"-env:UserInstallation={profile_dir.as_uri()}",
                "--invisible",
                "--headless",
                "--norestore",
                "--convert-to",
                "docx",
                "--outdir",
                str(output_dir),
                str(docx_path),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        converted = output_dir / docx_path.name
        if completed.returncode != 0 or not converted.is_file():
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"LibreOffice DOCX normalization failed: {detail}")
        converted.replace(docx_path)


def set_run_font(run, name: str, size: float, bold: bool | None = None) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for key in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(f"w:{key}"), name)


def set_east_asian_paragraph_rules(paragraph) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    for tag, value in (("kinsoku", "1"), ("overflowPunct", "0")):
        node = ppr.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            ppr.append(node)
        node.set(qn("w:val"), value)


def add_field(paragraph, instruction: str, display: str = "") -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instr, separate))
    if display:
        text = OxmlElement("w:t")
        text.text = display
        run._r.append(text)
    run._r.append(end)


def set_cell_margins(cell, top=110, start=120, bottom=110, end=120) -> None:
    tc = cell._tc
    tcpr = tc.get_or_add_tcPr()
    mar = tcpr.first_child_found_in("w:tcMar")
    if mar is None:
        mar = OxmlElement("w:tcMar")
        tcpr.append(mar)
    for edge, val in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = mar.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            mar.append(node)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")


def shade_cell(cell, fill: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    shd = tcpr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcpr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_table_borders(table) -> None:
    tblpr = table._tbl.tblPr
    borders = tblpr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tblpr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:color"), "D9D9D9")


def style_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2.5)
    section.header_distance = Cm(1.25)
    section.footer_distance = Cm(1.25)
    section.different_first_page_header_footer = True

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.first_line_indent = Pt(24)
    normal.paragraph_format.widow_control = True

    title = styles["Title"]
    title.font.name = HEADING_FONT
    title.font.size = Pt(26)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title._element.rPr.rFonts.set(qn("w:eastAsia"), HEADING_FONT)
    title_ppr = title._element.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)
    title.paragraph_format.space_after = Pt(18)
    title.paragraph_format.keep_with_next = True

    heading_specs = {
        "Heading 1": (18, 18, 10),
        "Heading 2": (15, 14, 8),
        "Heading 3": (13, 10, 6),
    }
    for style_name, (size, before, after) in heading_specs.items():
        style = styles[style_name]
        style.font.name = HEADING_FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style._element.rPr.rFonts.set(qn("w:eastAsia"), HEADING_FONT)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.keep_together = True
        style.paragraph_format.widow_control = True
        style.paragraph_format.page_break_before = False

    if "Figure Caption" not in styles:
        cap = styles.add_style("Figure Caption", WD_STYLE_TYPE.PARAGRAPH)
    else:
        cap = styles["Figure Caption"]
    cap.font.name = BODY_FONT
    cap.font.size = Pt(10)
    cap.font.color.rgb = RGBColor(0, 0, 0)
    cap._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    cap.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.first_line_indent = Pt(0)
    cap.paragraph_format.space_before = Pt(3)
    cap.paragraph_format.space_after = Pt(10)
    cap.paragraph_format.keep_together = True
    cap.paragraph_format.widow_control = True

    if "Code Inline" not in styles:
        code = styles.add_style("Code Inline", WD_STYLE_TYPE.CHARACTER)
        code.font.name = MONO_FONT
        code.font.size = Pt(10.5)
        code.font.color.rgb = RGBColor(32, 32, 32)

    for section in doc.sections:
        footer = section.footer
        p = footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        add_field(p, "PAGE", "1")
        for run in p.runs:
            set_run_font(run, BODY_FONT, 9)


def add_inline_runs(paragraph, text: str, *, bold=False, size=12) -> None:
    pieces = re.split(r"(`[^`]+`)", text)
    for piece in pieces:
        if not piece:
            continue
        if piece.startswith("`") and piece.endswith("`"):
            run = paragraph.add_run(piece[1:-1])
            run.style = "Code Inline"
        else:
            run = paragraph.add_run(piece)
            set_run_font(run, BODY_FONT, size, bold=bold)


def image_size(path: Path, max_width_in: float = 6.0, max_height_in: float = 6.2):
    with Image.open(path) as im:
        width, height = im.size
    ratio = width / height
    if ratio < 1:
        max_height_in = min(max_height_in, 5.5)
    width_in = max_width_in
    height_in = width_in / ratio
    if height_in > max_height_in:
        height_in = max_height_in
        width_in = height_in * ratio
    return Inches(width_in), Inches(height_in)


def add_image(doc: Document, path: Path, alt: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    width, height = image_size(path)
    run = p.add_run()
    shape = run.add_picture(str(path), width=width, height=height)
    shape._inline.docPr.set("descr", alt)


def add_cover_and_toc(doc: Document, title_text: str, subtitle: str) -> None:
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(74)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.first_line_indent = Pt(0)
    title_ppr = title._p.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)
    run = title.add_run(title_text)
    set_run_font(run, HEADING_FONT, 26, bold=True)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.first_line_indent = Pt(0)
    sub.paragraph_format.space_after = Pt(36)
    run = sub.add_run(subtitle)
    set_run_font(run, HEADING_FONT, 15)

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.paragraph_format.first_line_indent = Pt(0)
    meta.paragraph_format.line_spacing = 1.5
    add_inline_runs(meta, "Release v1.1.6\n2026 年 9 月 8 日", size=12)

    doc.add_page_break()
    toc_title = doc.add_paragraph("目錄", style="Heading 1")
    toc_title.paragraph_format.first_line_indent = Pt(0)
    toc_entries = (
        ("摘要", "3"),
        ("第一章　緒論", "4"),
        ("第二章　需求分析與系統設計", "7"),
        ("第三章　AWS 架構與服務整合", "12"),
        ("第四章　系統實作", "19"),
        ("第五章　測試、部署與維運", "25"),
        ("第六章　成果評估與結論", "32"),
        ("參考資料", "36"),
        ("附錄", "37"),
    )
    toc_table = doc.add_table(rows=0, cols=2)
    toc_table.autofit = False
    toc_table.columns[0].width = Cm(13.2)
    toc_table.columns[1].width = Cm(1.2)
    for entry, page_number in toc_entries:
        cells = toc_table.add_row().cells
        for cell in cells:
            set_cell_margins(cell, top=70, start=0, bottom=70, end=0)
        title_paragraph = cells[0].paragraphs[0]
        title_paragraph.paragraph_format.first_line_indent = Pt(0)
        add_inline_runs(title_paragraph, entry, size=12)
        page_paragraph = cells[1].paragraphs[0]
        page_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        page_paragraph.paragraph_format.first_line_indent = Pt(0)
        add_inline_runs(page_paragraph, page_number, size=12)
    doc.add_page_break()


def build(manuscript: Path, output: Path) -> None:
    lines = manuscript.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3 or not lines[0].startswith("# "):
        raise ValueError("Unexpected manuscript title block")

    doc = Document()
    style_document(doc)
    add_cover_and_toc(doc, lines[0][2:].strip(), lines[2].strip())

    base = manuscript.parent
    previous_was_image = False
    for raw in lines[3:]:
        line = raw.strip()
        if not line:
            previous_was_image = False
            continue

        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image_match:
            alt, relative = image_match.groups()
            image_path = (base / relative).resolve()
            if not image_path.exists():
                raise FileNotFoundError(image_path)
            add_image(doc, image_path, alt)
            previous_was_image = True
            continue

        if line.startswith("圖 "):
            p = doc.add_paragraph(style="Figure Caption")
            add_inline_runs(p, line, size=10)
            previous_was_image = False
            continue

        if line.startswith("# "):
            p = doc.add_paragraph(style="Heading 1")
            p.paragraph_format.first_line_indent = Pt(0)
            add_inline_runs(p, line[2:].strip(), bold=True, size=18)
            set_east_asian_paragraph_rules(p)
            continue

        if line.startswith("## "):
            text = line[3:].strip()
            style = "Heading 1" if text == "摘要" else "Heading 2"
            p = doc.add_paragraph(style=style)
            p.paragraph_format.first_line_indent = Pt(0)
            add_inline_runs(p, text, bold=True, size=18 if style == "Heading 1" else 15)
            set_east_asian_paragraph_rules(p)
            continue

        if line.startswith("### "):
            p = doc.add_paragraph(style="Heading 3")
            p.paragraph_format.first_line_indent = Pt(0)
            add_inline_runs(p, line[4:].strip(), bold=True, size=13)
            set_east_asian_paragraph_rules(p)
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.first_line_indent = Pt(0)
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.widow_control = True
            add_inline_runs(p, numbered.group(2))
            set_east_asian_paragraph_rules(p)
            continue

        p = doc.add_paragraph()
        p.paragraph_format.widow_control = True
        add_inline_runs(p, line)
        set_east_asian_paragraph_rules(p)

    settings = doc.settings._element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")

    doc.core_properties.title = "共演計劃多人 AI 協作故事遊戲 AWS 雲端系統實作"
    doc.core_properties.subject = "AWS 雲端工程師培訓期末專題報告"
    doc.core_properties.author = ""
    doc.core_properties.last_modified_by = ""
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    embed_cjk_font(output)
    roundtrip_embedded_fonts_with_libreoffice(output)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_written_report.py MANUSCRIPT OUTPUT")
    build(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())

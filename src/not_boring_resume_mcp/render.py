"""PDF rendering via Playwright + local Chromium.

This is the Python equivalent of the Puppeteer logic described in ARCHITECTURE.md
(solution A). Everything runs locally: we open notboringresume.cloud in a headless
Chromium, upload the YAML through the app's own "Upload YAML" button, then export
the CV to PDF by reusing the app's react-to-print output.

Why we don't just click "Generate to PDF" and grab a file: the app uses
react-to-print, which builds a fully styled, print-ready document in a hidden iframe
(applying its own pageStyle) and then calls window.print(). window.print() yields no
downloadable file in headless Chromium. So instead we intercept that print() call to
capture the exact document react-to-print prepared, and export *that* with Chromium's
own print engine. The app's print styling stays the single source of truth — the MCP
never duplicates it.
"""

from __future__ import annotations

from pathlib import Path

import markdown as md_lib
from playwright.async_api import Page, async_playwright
from pypdf import PdfReader

SITE_URL = "https://notboringresume.cloud"

# Classic, serif styling for the cover letter PDF. Uses only system serif fonts (no
# network), so it renders identically on any machine. A4 with generous margins, a
# small type size and tight line height. The body is justified; the subject (a Markdown
# heading) is light blue. The sign-off lines end in forced breaks, so justification
# leaves them left-aligned on their own.
LETTER_CSS = """
@page { size: A4; margin: 0; }
* { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
html, body { margin: 0; padding: 0; }
body {
  font-family: Georgia, "Times New Roman", Times, serif;
  color: #1a1a1a;
  font-size: 10pt;
  line-height: 1.5;
}
.letter {
  box-sizing: border-box;
  width: 210mm;
  min-height: 297mm;
  padding: 28mm 24mm;
}
h1, h2, h3 {
  font-weight: 700;
  font-size: 10pt;
  color: #5b9bd5;
  margin: 0 0 9mm;
}
p { margin: 0 0 4.5mm; text-align: justify; }
ul, ol { margin: 0 0 4.5mm; padding-left: 6mm; }
"""

# Injected into every frame (including react-to-print's print iframe) before any app
# code runs. When react-to-print calls the iframe's window.print(), we don't open the
# native dialog — we stash the iframe's fully-prepared print document on the top
# window so we can export it ourselves. This reuses react-to-print's output verbatim.
CAPTURE_PRINT_SCRIPT = """
window.print = function () {
  try {
    window.top.__capturedPrintHTML = document.documentElement.outerHTML;
  } catch (e) {}
};
"""


async def render_cv(yaml_content: str | None, output_path: str) -> dict:
    """Render a YAML CV into a one-page PDF.

    Args:
        yaml_content: the CV YAML content (already tailored by Claude). Pass None to
            render the site's built-in default CV without uploading (useful for tests).
        output_path: where to write the PDF (e.g. output/Acme/backend-dev/cv.pdf).

    Returns:
        {"path": <str>, "overflows": <bool>}
        - path: the path of the written PDF.
        - overflows: True if the PDF spilled onto more than one page (Claude must
          then shorten the YAML and call the tool again).
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.add_init_script(CAPTURE_PRINT_SCRIPT)
        await page.goto(SITE_URL, wait_until="networkidle")

        # With no YAML, render the default CV the site already loaded on mount.
        if yaml_content is not None:
            await _upload_yaml(page, yaml_content)

        # Trigger the app's real export. react-to-print prepares its print iframe and
        # calls print(); our injected override captures the prepared document instead
        # of opening a dialog.
        await page.get_by_role("button", name="Generate to PDF").click()
        await page.wait_for_function("() => window.__capturedPrintHTML")
        print_html = await page.evaluate("() => window.__capturedPrintHTML")

        # Render react-to-print's exact document and export it. set_content keeps the
        # site as the base URL, so any relative asset/stylesheet links still resolve.
        await page.set_content(print_html, wait_until="networkidle")
        await page.pdf(
            path=str(out),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()

    return {"path": str(out), "overflows": _pdf_overflows(out)}


async def fetch_offer_text(url: str) -> str:
    """Open a job-offer URL in headless Chromium and return its visible text.

    Rendering the page (rather than a plain HTTP GET) means JavaScript-heavy job
    boards still yield the actual offer text instead of an empty shell.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        text = await page.evaluate("() => document.body.innerText")
        await browser.close()
    return text.strip()


def _letter_html(markdown_text: str) -> str:
    """Convert the Markdown cover letter to a styled HTML document.

    The `nl2br` extension keeps single newlines as line breaks (e.g. the sign-off
    block), while blank lines still separate paragraphs. A Markdown heading
    (`# Subject: ...`) becomes the light-blue letter header.
    """
    body = md_lib.markdown(markdown_text, extensions=["nl2br"])
    return (
        f"<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{LETTER_CSS}</style></head>"
        f"<body><div class='letter'>{body}</div></body></html>"
    )


async def render_letter(markdown_text: str, output_path: str) -> dict:
    """Render a Markdown cover letter into a clean, classic A4 PDF.

    Reuses the same local Chromium as the CV, so it works on any machine without Word
    or extra system dependencies.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(_letter_html(markdown_text), wait_until="networkidle")
        await page.pdf(
            path=str(out),
            format="A4",
            print_background=True,
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
        )
        await browser.close()

    return {"path": str(out)}


async def _upload_yaml(page: Page, yaml_content: str) -> None:
    """Upload the YAML through the app's "Upload YAML" button.

    That button creates a transient <input type=file> and clicks it (see the app's
    uploadYaml()). We intercept that click with Playwright's file chooser and feed
    the YAML in-memory (no temp file), so the app's setCv(...) runs and React
    renders the CV — the exact same path a real user takes.
    """
    async with page.expect_file_chooser() as fc_info:
        await page.get_by_role("button", name="Upload YAML").click()
    file_chooser = await fc_info.value
    await file_chooser.set_files(
        files=[
            {
                "name": "cv.yaml",
                "mimeType": "application/x-yaml",
                "buffer": yaml_content.encode("utf-8"),
            }
        ]
    )
    # Let React re-render with the new CV data before exporting.
    await page.wait_for_load_state("networkidle")


def _pdf_overflows(path: Path) -> bool:
    """Return True if the generated PDF has more than one page.

    The CV must fit on a single A4 page; a multi-page PDF is the ground-truth
    signal that the content overflowed.
    """
    return len(PdfReader(str(path)).pages) > 1

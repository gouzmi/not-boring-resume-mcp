"""MCP server entry point (FastMCP).

Exposes to Claude (so the end user only installs one thing):
  - a tool   `load_cv(cv_path)`                 -> the CV YAML without its heavy photo
  - a tool   `generate_pdf(yaml, output_path)`  -> the action (PDF rendering)
  - a tool   `fetch_offer(url)`                 -> job-offer text from a URL
  - prompts `tailor_cv(offer)` and `tailor_cv_and_letter(offer)` -> the workflow (the
    skill, shipped inside the MCP), CV only or CV + cover letter. They show up as
    /mcp__not-boring-resume__tailor_cv and /mcp__not-boring-resume__tailor_cv_and_letter.
"""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from not_boring_resume_mcp.cv_image import reattach_images, strip_images
from not_boring_resume_mcp.render import fetch_offer_text, render_cv, render_letter

mcp = FastMCP("not-boring-resume")


@mcp.tool()
def load_cv(cv_path: str = "./cv.yaml") -> str:
    """Return the CV YAML with its embedded photo removed.

    Read the CV through this tool instead of opening the file directly: the photo is
    a base64 data URI that is huge and useless for tailoring. Work from the returned
    text; the photo is reattached automatically by generate_pdf.

    Args:
        cv_path: path to the CV YAML.
    """
    return strip_images(Path(cv_path).read_text(encoding="utf-8"))


@mcp.tool()
async def generate_pdf(
    yaml: str | None = None,
    output_path: str = "cv.pdf",
    cv_path: str | None = None,
) -> dict:
    """Render a YAML CV into a one-page PDF via notboringresume.cloud.

    Writes the PDF to `output_path` and returns {"path", "overflows"}.
    If "overflows" is True, shorten the YAML and call this tool again.

    Args:
        yaml: the CV content in YAML (already tailored to the job offer). Omit it to
            render the site's built-in default CV (handy for a quick manual test).
        output_path: where to save the PDF, e.g. output/Acme/backend-dev/cv.pdf.
            Defaults to cv.pdf in the current directory.
        cv_path: path to the original CV YAML. When given, the photo from that file is
            reattached to `yaml` before rendering (it was stripped by load_cv).
    """
    if yaml is not None and cv_path is not None:
        yaml = reattach_images(yaml, Path(cv_path).read_text(encoding="utf-8"))
    return await render_cv(yaml, output_path)


@mcp.tool()
async def generate_letter_pdf(
    text: str | None = None,
    letter_path: str | None = None,
    output_path: str = "cover-letter.pdf",
) -> dict:
    """Render a cover letter written in Markdown into a clean, classic A4 PDF.

    Provide the letter either inline via `text`, or as an existing Markdown file via
    `letter_path` — so the PDF can be produced from a letter that already exists,
    without composing a new one. Uses the same local Chromium as the CV, so it works
    on any machine without Word or extra system dependencies. Returns {"path"}.

    Args:
        text: the cover letter in Markdown. Blank lines separate paragraphs; a
            top-level heading (`# Subject: ...`) is styled as the light-blue header.
        letter_path: path to an existing Markdown letter to render instead of `text`.
        output_path: where to save the PDF, e.g. output/Acme/backend-dev/cover-letter.pdf.
    """
    if text is None:
        if letter_path is None:
            raise ValueError("Provide either `text` or `letter_path`.")
        text = Path(letter_path).read_text(encoding="utf-8")
    return await render_letter(text, output_path)


@mcp.tool()
async def fetch_offer(url: str) -> str:
    """Fetch a job offer from a URL and return its visible text.

    Use this when the user gives a link instead of pasting the offer. The page is
    rendered in a headless browser, so it works on JavaScript-heavy job boards.

    Args:
        url: the job offer URL.
    """
    return await fetch_offer_text(url)


# Cover-letter sections in the workflow are wrapped with these markers so we can drop
# them when the user only wants the CV.
_COVER_LETTER_BLOCK = re.compile(
    r"<!-- *cover-letter:start *-->\n?.*?<!-- *cover-letter:end *-->\n?",
    re.DOTALL,
)
def _apply_cover_letter_toggle(template: str, enabled: bool) -> str:
    """Keep or remove the cover-letter sections of the workflow.

    When disabled, the whole marked block is dropped; when enabled, only the marker
    comments are removed so the instructions read cleanly.
    """
    if not enabled:
        return _COVER_LETTER_BLOCK.sub("", template)
    return re.sub(r"<!-- *cover-letter:(?:start|end) *-->\n?", "", template)


def _workflow(offer: str, cv_path: str, cover_letter_path: str, with_letter: bool) -> str:
    """Build the tailor workflow prompt from prompts/tailor_cv.md.

    Both prompts below share this single source; with_letter decides whether the
    cover-letter sections are kept. We inject the arguments in place of the $...
    placeholders.
    """
    template = (
        files("not_boring_resume_mcp")
        .joinpath("prompts", "tailor_cv.md")
        .read_text(encoding="utf-8")
    )
    template = _apply_cover_letter_toggle(template, with_letter)
    return (
        template.replace("$CV_PATH", cv_path)
        .replace("$COVER_LETTER_PATH", cover_letter_path)
        .replace("$ARGUMENTS", offer)
    )


@mcp.prompt()
def tailor_cv(offer: str, cv_path: str = "./cv.yaml") -> str:
    """Tailor the CV to a job offer and render the PDF (no cover letter).

    Args:
        offer: the job offer text (plain text or a URL).
        cv_path: path to the CV YAML, in case it is named differently.
    """
    return _workflow(offer, cv_path, "", with_letter=False)


@mcp.prompt()
def tailor_cv_and_letter(
    offer: str,
    cv_path: str = "./cv.yaml",
    cover_letter_path: str = "./cover-letter-template.md",
) -> str:
    """Tailor the CV, render the PDF, and write the cover letter.

    Args:
        offer: the job offer text (plain text or a URL).
        cv_path: path to the CV YAML, in case it is named differently.
        cover_letter_path: path to the cover letter template, in case it differs.
    """
    return _workflow(offer, cv_path, cover_letter_path, with_letter=True)


def main() -> None:
    """Console-script entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()

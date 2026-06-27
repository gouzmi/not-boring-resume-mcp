"""Golden test for render_cv.

Renders the site's built-in default CV (no upload) and checks it matches the
reference export cv.pdf at the project root. We compare normalized extracted text
rather than bytes: the two PDFs come from different engines (the reference is a real
browser export, ours is Playwright), so metadata, fonts and image compression differ
while the actual CV content must be identical.
"""

import asyncio
import re
from pathlib import Path

from pypdf import PdfReader

from not_boring_resume_mcp.render import render_cv

REFERENCE_PDF = Path(__file__).resolve().parent / "cv.pdf"

# The reference is a real-browser export and ours is Playwright, so text extraction
# differs in cosmetic ways only: ligatures encoded as glyph names (/fi.liga), bullet
# markers, and per-glyph spacing. We undo the ligatures, then keep only alphanumerics
# so those extraction artifacts can't cause spurious mismatches.
_LIGATURES = {
    "/ffi.liga": "ffi",
    "/ffl.liga": "ffl",
    "/fi.liga": "fi",
    "/fl.liga": "fl",
    "/ff.liga": "ff",
}


def _normalized_text(path: Path) -> str:
    raw = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    for glyph, repl in _LIGATURES.items():
        raw = raw.replace(glyph, repl)
    return re.sub(r"[^a-z0-9]", "", raw.lower())


def test_render_default_matches_reference(tmp_path):
    out = tmp_path / "rendered.pdf"
    result = asyncio.run(render_cv(None, str(out)))

    assert out.exists(), "render_cv did not produce a PDF"
    assert result["overflows"] is False, "default CV must fit on one page"

    assert _normalized_text(out) == _normalized_text(REFERENCE_PDF), (
        "Rendered default CV text differs from the reference cv.pdf"
    )

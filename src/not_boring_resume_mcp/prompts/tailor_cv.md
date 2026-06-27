Adapt the CV YAML to a specific job offer, verify it fits on one A4 page, and produce a cover letter.

## Paths (relative to the current working directory)
- CV YAML: `$CV_PATH`
- Cover letter template: `$COVER_LETTER_PATH`
- All outputs go to `./output/[COMPANY]/[OFFER]/`

The one-page check and PDF generation are handled by the `generate_pdf` MCP tool (no scripts to run).

## Job Offer
$ARGUMENTS

---

## Step 1 — Read inputs
Get the CV by calling the `load_cv` tool with `$CV_PATH` — do not open the file directly, it embeds a heavy base64 photo. Work from the returned YAML (the photo is reattached later by `generate_pdf`).
<!-- cover-letter:start -->
Read `$COVER_LETTER_PATH` if it exists.
<!-- cover-letter:end -->
If the job offer above is empty, ask the user to paste the job offer.
If the job offer above is a URL, call the `fetch_offer` tool with it and use the returned text as the job offer.

Extract from the job offer:
- `COMPANY`: the company name, lowercased, spaces replaced with hyphens (e.g. `acme-corp`)
- `OFFER`: the job title, lowercased, spaces replaced with hyphens (e.g. `data-engineer`)

All outputs go to `./output/[COMPANY]/[OFFER]/`.

## Step 2 — Adapt the YAML
Rules:
- Keep all factual data unchanged: names, dates, companies, contact info
- Rewrite `about.description` to speak directly to this role (2–4 sentences max) while keeping the maximum to preserve the original style.
- Reorder skill categories so the most relevant appear first
- Trim or remove the least relevant bullet points to save space
- Never invent skills or experience that don't exist in the original YAML
- Target: content that fits on exactly one A4 page

Keep the full adapted YAML for the next step and save it to `./output/[COMPANY]/[OFFER]/cv.yaml`.

## Step 3 — Generate and verify the PDF (max 5 attempts)
Call the `generate_pdf` tool with:
- `yaml`: the full adapted YAML
- `output_path`: `./output/[COMPANY]/[OFFER]/cv.pdf`
- `cv_path`: `$CV_PATH` (so the original photo is reattached before rendering)

Inspect the returned `overflows`:
- `overflows: false` → the CV fits on one page. Done.
- `overflows: true` → the content spilled onto a second page. Identify the longest / least relevant bullet points, shorten or remove them, rewrite the YAML, then call `generate_pdf` again. Repeat until `overflows` is false (max 5 attempts).

<!-- cover-letter:start -->
## Step 4 — Cover letter
If `$COVER_LETTER_PATH` exists, write a tailored cover letter from it. The template
marks which parts to adapt with `[[TAILOR: <instruction>]] … [[/TAILOR]]` blocks:

- Keep all text **outside** any `[[TAILOR ...]]` marker exactly as written. These are
  the fixed parts of the letter.
- For each `[[TAILOR: <instruction>]] … [[/TAILOR]]` block, the text **inside** is an
  example showing the desired tone, length and level of specificity. Rewrite it to
  follow the instruction and this job offer, drawing concrete facts (companies, tools,
  outcomes) from the adapted YAML. Keep a length and register similar to the example.
- Remove every `[[TAILOR: ...]]` and `[[/TAILOR]]` marker from the final text.
- Style: do not use dashes (em dashes, en dashes, hyphens) as punctuation. Use commas.

Format the final cover letter in **Markdown**. Make the subject line a top-level heading (`# Subject: ...`); omit it entirely if the letter has no subject.
Save it to `./output/[COMPANY]/[OFFER]/cover-letter.md`.
Then call the `generate_letter_pdf` tool with:
- `text`: the final cover letter in Markdown
- `output_path`: `./output/[COMPANY]/[OFFER]/cover-letter.pdf`

Output the final cover letter in the conversation.
<!-- cover-letter:end -->

## Step 5 — Summary
Confirm the saved files:
- CV PDF: `./output/[COMPANY]/[OFFER]/cv.pdf`
- CV YAML: `./output/[COMPANY]/[OFFER]/cv.yaml`
<!-- cover-letter:start -->
- Cover letter: `./output/[COMPANY]/[OFFER]/cover-letter.md` and `./output/[COMPANY]/[OFFER]/cover-letter.pdf`
<!-- cover-letter:end -->

List the key changes made to the YAML.

# not-boring-resume-mcp

[![Build Status](https://github.com/gouzmi/not-boring-resume-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/gouzmi/not-boring-resume-mcp/actions/workflows/ci.yml)
[![PyPI Versions](https://img.shields.io/pypi/v/not-boring-resume-mcp?style=plastic&label=pypi-version)](https://pypi.org/project/not-boring-resume-mcp/)

MCP server that renders a YAML CV into a one-page PDF via
[notboringresume.cloud](https://notboringresume.cloud) (local headless Chromium).  
Optionnaly it can also generate a cover letter adapted to the resume and the offer.

## Installation

Requires [uv](https://docs.astral.sh/uv/). First download the browser Playwright
uses to render PDFs (one-time):

```bash
uvx --from not-boring-resume-mcp playwright install chromium
```

**Claude Code:**

```bash
claude mcp add not-boring-resume -- uvx not-boring-resume-mcp
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "not-boring-resume": {
      "command": "uvx",
      "args": ["not-boring-resume-mcp"]
    }
  }
}
```

## Usage

Run Claude from a folder that holds your `cv.yaml` (and, optionally, a
`cover-letter-template.md`). Then call one of the prompts:

- `/mcp__not-boring-resume__tailor_cv` — tailor the CV and render `cv.pdf`
- `/mcp__not-boring-resume__tailor_cv_and_letter` — also write and render the cover letter

### The offer argument

Both prompts take the job **offer** as their argument — pass it right after the
prompt name, either as **plain text** (paste the whole job description) or as a
**URL**:

```
/mcp__not-boring-resume__tailor_cv https://example.com/jobs/data-engineer
/mcp__not-boring-resume__tailor_cv_and_letter <paste the full offer text here>
```

When you give a URL, the server fetches the page and extracts its visible text
before tailoring. The offer is what the CV (and letter) get adapted to, so the
more complete it is, the better the result.

Both prompts also accept optional path arguments if your files aren't in the
default location: `cv_path` (defaults to `./cv.yaml`) and, for
`tailor_cv_and_letter`, `cover_letter_path` (defaults to `./cover-letter-template.md`).

Results are saved under `./output/[company]/[offer]/` (`cv.pdf`, the adapted `cv.yaml`,
and, when requested, the cover letter as `.md` and `.pdf`).

### The `cv.yaml` file

This is the only required input. You can **download a ready-to-edit template from
[notboringresume.cloud](https://notboringresume.cloud)** (use the editor there to
build one, then save it as `cv.yaml`), or start from the skeleton below and fill in
your own data. Markdown is supported in the free-text fields (`description`,
`about.description`) — e.g. `**bold**` and `[links](https://...)`.

```yaml
profile:
  name: Jane Doe
  position: Data & Software Engineer
  image: >-                              # optional: data:image/jpeg;base64,...
    data:image/jpeg;base64,<...>

contact:
  mail: jane.doe@example.com
  city: Taipei, Taiwan
  linkedin:
    title: LinkedIn
    url: https://linkedin.com/in/jane-doe/
  github:
    title: GitHub
    url: https://github.com/janedoe

skills:
  - categoryName: Data Engineering
    skills:
      - Spark
      - Airflow
      - DBT
  - categoryName: Languages
    skills:
      - Python
      - SQL

certifications:
  - name: AWS Certified Data Analyst Specialty (2021)

languages:
  - name: English
    level: Fluent
  - name: Spanish
    level: Intermediate

about:
  description: >
    Two or three sentences on who you are and what kind of role you're
    after. Markdown is allowed here.

experiences:
  - company: Some Company
    year: May 2021 - Jun 2024
    position: Data Engineer
    description: >-
      - **Achievement** with a measurable outcome.
      - Another bullet describing impact, tools, scale.

education:
  - name: Some University
    location: City, Country
    year: 2015 - 2020
    diplomaName: MSc, Computer Science

projects:
  - name: Side Project
    year: Since 2026
    description: >
      One line on the project and the stack used.
```

A complete, real-world example lives at
[`examples/cv.yaml`](examples/cv.yaml).

### The `cover-letter-template.md` file

Only needed for `tailor_cv_and_letter`. There's **no download for this one** —
write your own. It's a normal Markdown letter where the parts that should be
rewritten per offer are wrapped in `[[TAILOR: instructions]]example text[[/TAILOR]]`
markers: the instruction tells the model what to write, and the example text shows
the tone/length to match. Everything outside the markers is kept verbatim.

```markdown
# Subject: Application for [[TAILOR: the job title from the offer]]Data Engineer[[/TAILOR]] Position

Dear Hiring Team,

I am a Data & Software Engineer with five years of experience [...].
[[TAILOR: one sentence speaking directly to THIS company, its scale, mission, or
specific challenges; mirror the tone of this paragraph]]Example sentence about the
company.[[/TAILOR]]

[[TAILOR: a paragraph covering a first angle relevant to the offer (data pipelines,
APIs, cloud). Be specific: name companies, tools, outcomes from the adapted YAML.
Keep the same length and register as this example]]Example paragraph.[[/TAILOR]]

[...]

Best regards,
Jane Doe
jane.doe@example.com
```

A complete example lives at
[`examples/cover-letter-template.md`](examples/cover-letter-template.md).

## Development

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev                              # install deps
uv run playwright install chromium         # one-time: browser for rendering/tests
uv run ruff format .                        # format
uv run ruff check .                         # lint
uv run pytest                               # tests
```

> The test suite renders the live default CV from notboringresume.cloud, so it
> needs network access and will fail if the site is down.

## Continuous integration

CI (lint + tests) runs on every pull request and push to `main`. See
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) for details.

## Releasing (publishing to PyPI)

Releases are on-demand and automated with
[python-semantic-release](https://python-semantic-release.readthedocs.io/) —
trigger the release workflow manually with `gh workflow run release.yml --ref main`
and it bumps the version, tags, and publishes to PyPI from the
[Conventional Commit](https://www.conventionalcommits.org/) history. See
[`.github/workflows/release.yml`](.github/workflows/release.yml) for the full flow.

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
`cover-letter-template.md`). Then call one of the prompts with the job offer, either
pasted as text or as a URL:

- `/mcp__not-boring-resume__tailor_cv` — tailor the CV and render `cv.pdf`
- `/mcp__not-boring-resume__tailor_cv_and_letter` — also write and render the cover letter

Results are saved under `./output/[company]/[offer]/` (`cv.pdf`, the adapted `cv.yaml`,
and, when requested, the cover letter as `.md` and `.pdf`).

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

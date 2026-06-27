# not-boring-resume-mcp

MCP server that renders a YAML CV into a one-page PDF via
[notboringresume.cloud](https://notboringresume.cloud) (local headless Chromium).  
Optionnaly it can also generate a cover letter adapted to the resume and the offer.

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

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`:

- **lint** — `ruff format --check` and `ruff check`
- **test** — installs Chromium via Playwright, then runs `pytest`

## Releasing (publishing to PyPI)

Releases are **tag-driven**: pushing a `v*` tag builds the package, creates the
matching GitHub Release, and publishes to PyPI. The workflow lives in
`.github/workflows/publish.yml`.

### One-time setup

Configure a **Trusted Publisher** on PyPI (no API token to store). On
[PyPI](https://pypi.org/) → your project → **Publishing** → **Add a pending
publisher**:

| Field        | Value                       |
| ------------ | --------------------------- |
| Owner        | your GitHub account / org   |
| Repository   | `not-boring-resume-mcp`     |
| Workflow     | `publish.yml`               |
| Environment  | `pypi`                      |

### Cutting a release

1. Bump the version in `pyproject.toml` (e.g. `version = "0.1.1"`), commit and push.
2. Create and push a matching tag:

   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```

The tag triggers the workflow, which:

1. **Verifies** the tag (`v0.1.1`) matches `version` in `pyproject.toml` — the
   job fails fast if they differ, so you can't ship a mismatched release.
2. Builds the sdist and wheel.
3. Creates the GitHub Release with auto-generated notes and the built artifacts.
4. Publishes to PyPI.

> The tag version (minus the `v`) **must** equal `project.version`, and that
> version must not already exist on PyPI — PyPI never lets you overwrite a
> published version.

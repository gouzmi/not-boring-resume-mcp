"""Keep the embedded photo out of the LLM's context.

A CV YAML may carry a photo as a base64 data URI (e.g. profile.image:
"data:image/jpeg;base64,...."). That blob is huge and useless for tailoring, so we
strip it before the LLM reads the CV and reattach it just before rendering the PDF.

The image stays in the original cv.yaml (its source of truth); it never transits
through the model. Detection is generic: any string value starting with "data:image/"
is treated as an image, wherever it sits in the YAML tree.
"""

from __future__ import annotations

import io

from ruamel.yaml import YAML

_IMAGE_PREFIX = "data:image/"

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.width = 1 << 20  # never line-wrap (data URIs are very long)


def _load(text: str):
    return _yaml.load(text)


def _dump(data) -> str:
    buf = io.StringIO()
    _yaml.dump(data, buf)
    return buf.getvalue()


def _find_images(node, path: tuple, out: dict[tuple, str]) -> None:
    """Collect {path: value} for every string leaf that is an image data URI."""
    if isinstance(node, dict):
        for key, value in node.items():
            _find_images(value, path + (key,), out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _find_images(value, path + (index,), out)
    elif isinstance(node, str) and node.startswith(_IMAGE_PREFIX):
        out[path] = node


def _set_path(data, path: tuple, value: str) -> None:
    """Set value at the given key/index path, creating missing dict levels."""
    node = data
    for key in path[:-1]:
        if isinstance(node, dict) and key not in node:
            node[key] = {}
        node = node[key]
    node[path[-1]] = value


def strip_images(yaml_text: str) -> str:
    """Return the YAML with every image data URI blanked to an empty string."""
    data = _load(yaml_text)
    images: dict[tuple, str] = {}
    _find_images(data, (), images)
    for path in images:
        _set_path(data, path, "")
    return _dump(data)


def reattach_images(target_yaml: str, source_yaml: str) -> str:
    """Copy the image data URIs from source_yaml back into target_yaml by path.

    Used to restore the photo the LLM never saw before rendering the PDF.
    """
    images: dict[tuple, str] = {}
    _find_images(_load(source_yaml), (), images)
    if not images:
        return target_yaml
    data = _load(target_yaml)
    for path, value in images.items():
        _set_path(data, path, value)
    return _dump(data)

"""
Input sanitization utilities for user-supplied text fields.

Strips HTML/script tags and dangerous patterns to prevent
stored XSS and injection attacks.  Does NOT depend on external
libraries (no bleach requirement).
"""

import re
from typing import Optional

# Pre-compiled patterns
_HTML_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_SCRIPT_BODY_RE = re.compile(
    r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE
)
_STYLE_BODY_RE = re.compile(
    r"<style[^>]*>.*?</style>", re.DOTALL | re.IGNORECASE
)
_EVENT_HANDLER_RE = re.compile(
    r"\bon\w+\s*=\s*[\"'][^\"']*[\"']", re.IGNORECASE
)
_JAVASCRIPT_URI_RE = re.compile(
    r"javascript\s*:", re.IGNORECASE
)


def strip_dangerous(value: Optional[str]) -> Optional[str]:
    """Remove script/style blocks, HTML tags, event handlers,
    and javascript: URIs from a string.

    Returns None unchanged, empty string unchanged.
    """
    if not value:
        return value
    text = _SCRIPT_BODY_RE.sub("", value)
    text = _STYLE_BODY_RE.sub("", text)
    text = _EVENT_HANDLER_RE.sub("", text)
    text = _JAVASCRIPT_URI_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    # Collapse resulting multi-spaces but preserve newlines
    text = re.sub(r"[^\S\n]+", " ", text).strip()
    return text
